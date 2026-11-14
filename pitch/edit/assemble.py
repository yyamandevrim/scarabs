#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=11,<13", "fonttools[woff]>=4.60,<5"]
# ///
"""Assemble ACORN's data-driven, silent-by-default rough cuts; no app access."""
import argparse
import json
import math
import subprocess
from copy import deepcopy
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[2]
EDIT = Path(__file__).resolve().parent
OUT = EDIT / "out"
STILLS = {".jpg", ".jpeg", ".png", ".webp"}


def run(args):
    subprocess.run([str(x) for x in args], check=True)


def probe(path):
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)
    ]))


def local(path):
    """All data paths are repo-relative, including optional future audio."""
    p = Path(path)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"Expected a repository-relative path: {path}")
    return ROOT / p


class Type:
    def __init__(self, data):
        self.faces = []
        for i, key in enumerate(("font", "font_ext")):
            font = TTFont(local(data[key]))
            chars = set(font.getBestCmap())
            dest = OUT / f"plex-{i}.ttf"
            font.flavor = None
            font.save(dest)
            self.faces.append((dest, chars))
        self.cache = {}

    def face(self, char, size):
        i = next((i for i, (_, chars) in enumerate(self.faces) if ord(char) in chars), None)
        if i is None:
            raise ValueError(f"Font has no glyph for {char!r}")
        if (i, size) not in self.cache:
            self.cache[i, size] = ImageFont.truetype(str(self.faces[i][0]), size)
        return self.cache[i, size]

    def width(self, text, size):
        return sum(self.face(c, size).getlength(c) for c in text)

    def lines(self, text, size, width):
        result = []
        for paragraph in text.split("\n"):
            line = ""
            for word in paragraph.split():
                candidate = f"{line} {word}".strip()
                if self.width(candidate, size) > width:
                    if not line or self.width(word, size) > width:
                        raise ValueError(f"Unbreakable text overflows: {word}")
                    result.append(line)
                    line = word
                else:
                    line = candidate
            result.append(line)
        return result

    def block(self, draw, text, x, y, size, width, color, center=False, max_lines=3):
        lines = self.lines(text, size, width)
        if len(lines) > max_lines:
            raise ValueError(f"Too many lines ({len(lines)}): {text}")
        for line in lines:
            px = x + (width - self.width(line, size)) / 2 if center else x
            # Per-character font fallback preserves Turkish in the same Plex Sans family.
            for char in line:
                face = self.face(char, size)
                draw.text((px, y + size), char, font=face, fill=color, anchor="ls")
                px += face.getlength(char)
            y += size + 8
        return y


def frames(seconds, fps):
    count = round(seconds * fps)
    if abs(count / fps - seconds) > 0.00001:
        raise ValueError(f"Duration is not frame aligned: {seconds}")
    return count


def validate(data):
    assert (data["width"], data["height"], data["fps"]) == (1920, 1080, 30)
    assert [s["id"] for s in data["shots"]] == [f"{n:02}" for n in range(1, 21)]
    shots = {s["id"]: s for s in data["shots"]}
    for cut in data["cuts"].values():
        assert sum(r["duration"] for r in cut["timeline"]) == cut["expected_duration"]
        for row in cut["timeline"]:
            shot = shots[row["shot"]]
            frames(row["duration"], data["fps"])
            edits = row.get("edits", shot["edits"])
            assert sum(e["duration"] for e in edits) >= row["duration"]
            for edit in edits:
                frames(edit["duration"], data["fps"])
                for src in edit["sources"]:
                    local(src["file"])
                    assert src["out_seconds"] > src["in_seconds"] >= 0
        for key in ("voice_over", "music"):
            if cut["audio"].get(key) and not local(cut["audio"][key]).is_file():
                raise FileNotFoundError(f"Named {key} file is missing: {cut['audio'][key]}")


def geometry(src, box, info):
    stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    crop = src.get("crop", [0, 0, stream["width"], stream["height"]])
    cx, cy, cw, ch = crop
    assert cx >= 0 and cy >= 0 and cx + cw <= stream["width"] and cy + ch <= stream["height"]
    x, y, bw, bh = box
    scale = min(bw / cw, bh / ch)
    w, h = int(cw * scale) // 2 * 2, int(ch * scale) // 2 * 2
    return crop, (x + (bw - w) // 2, y + (bh - h) // 2, w, h)


def overlay(data, types, shot, missing, geoms, path):
    pal = data["palette"]
    im = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    types.block(d, f"{data['brand_name']}  ·  ROUGH CUT  ·  SHOT {shot['id']}  /  {shot['source_type']}",
                64, 20, 22, 1792, pal["secondary"])
    y = 60
    for line in shot["on_screen_text"]:
        y = types.block(d, line, 64, y, 36, 1792, pal["text"], max_lines=2) + 3
    for line in shot["caption"]:
        y = types.block(d, line, 64, y, 28, 1792, pal["blue"], max_lines=2) + 2
    if y > 212:
        raise ValueError(f"Header overlaps media on shot {shot['id']}: {y}")
    if missing:
        d.rectangle((64, 248, 1856, 880), fill=pal["panel"])
        types.block(d, f"MISSING  ·  SHOT {shot['id']}  ·  {shot['source_type']}",
                    108, 302, 42, 1704, pal["amber"])
        types.block(d, shot["description"], 108, 388, 38, 1660, pal["text"])
        y = 570
        for file in missing:
            y = types.block(d, "Waiting for: " + file, 108, y, 26, 1660, pal["secondary"]) + 14
    else:
        for src, (crop, rect) in geoms:
            if not src.get("wordmark_rect"):
                continue
            # Only cover the old header artwork, at its verified capture position.
            cx, cy, cw, ch = crop
            x, y, w, h = rect
            lx, ly, lw, lh = src["wordmark_rect"]
            a, b = x + (lx - cx) * w / cw, y + (ly - cy) * h / ch
            rw, rh = lw * w / cw, lh * h / ch
            d.rectangle((a, b, a + rw, b + rh), fill=pal["panel"])
            types.block(d, data["brand_name"], a, b + 2, int(rh * 0.69), rw, pal["text"], max_lines=1)
        if shot.get("translation"):
            # Beside the solo phone, or in the free upper-right area for pairs.
            if len(geoms) == 1 and geoms[0][0].get("crop", [0,0,1,1])[2] == 512:
                types.block(d, shot["translation"], 1200, 450, 26, 620, pal["secondary"])
            else:
                types.block(d, shot["translation"], 1200, 106, 24, 650, pal["secondary"])
    if shot.get("note"):
        types.block(d, shot["note"], 64, 916, 24, 1792, pal["amber"], center=True, max_lines=1)
    # English script reads are burnt as subtitles while the audio is absent.
    types.block(d, shot["subtitle"], 100, 966, 34, 1720, pal["text"], center=True, max_lines=2)
    im.save(path)


def render_edit(data, types, shot, edit, dest, log):
    fps = data["fps"]
    duration = edit["duration"]
    count = frames(duration, fps)
    missing = [s["file"] for s in edit["sources"] if not local(s["file"]).is_file()]
    # If a paired view lacks a component, show an explicit gap rather than imply a pair.
    geoms = []
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-filter_complex_threads", "1",
           "-f", "lavfi", "-i", f"color=c={data['palette']['background']}:s=1920x1080:r={fps}:d={duration}"]
    filters = []
    last = "0:v"
    if not missing:
        paired = len(edit["sources"]) == 2
        boxes = [(104, 218, 384, 682), (548, 218, 1268, 682)] if paired else [(64, 218, 1792, 682)]
        for i, (src, box) in enumerate(zip(edit["sources"], boxes), 1):
            file = local(src["file"])
            info = probe(file)
            crop, rect = geometry(src, box, info)
            geoms.append((src, (crop, rect)))
            still = file.suffix.lower() in STILLS
            if still:
                cmd += ["-loop", "1", "-framerate", str(fps), "-i", file]
                available = duration
            else:
                total = float(info["format"]["duration"])
                if src["in_seconds"] >= total:
                    raise ValueError(f"In point outside {src['file']}")
                available = min(src["out_seconds"], total) - src["in_seconds"]
                cmd += ["-ss", str(src["in_seconds"]), "-t", str(available), "-i", file]
            cx, cy, cw, ch = crop
            x, y, w, h = rect
            chain = f"[{i}:v]setpts=PTS-STARTPTS,fps={fps},crop={cw}:{ch}:{cx}:{cy},scale={w}:{h}:flags=lanczos,setsar=1"
            if still and shot["source_type"] == "REAL":
                # 100 -> 103% crop move on the actual photo only; no invented geometry.
                chain += f",zoompan=z='1+0.03*on/{max(count-1,1)}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={w}x{h}:fps={fps}"
            chain += f",tpad=stop_mode=clone:stop_duration={duration},trim=end_frame={count},setpts=PTS-STARTPTS[v{i}]"
            filters.append(chain)
            filters.append(f"[{last}][v{i}]overlay={x}:{y}:shortest=1[b{i}]")
            last = f"b{i}"
            log.append(dict(file=src["file"],in_seconds=src["in_seconds"],out_seconds=src["out_seconds"],
                            held_seconds=round(max(0,duration-available),6)))
    card = dest.with_suffix(".png")
    overlay(data, types, shot, missing, geoms, card)
    idx = 1 + (0 if missing else len(geoms))
    cmd += ["-loop", "1", "-framerate", str(fps), "-i", card]
    filters.append(f"[{last}][{idx}:v]overlay=shortest=1,format=yuv420p[video]")
    cmd += ["-filter_complex", ";".join(filters), "-map", "[video]", "-an", "-frames:v", str(count),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-threads", "4",
            "-r", str(fps), "-video_track_timescale", "30000", "-movflags", "+faststart", dest]
    run(cmd)
    return missing


def add_audio(cut, silent, target):
    audio = cut["audio"]
    paths = [(key, local(audio[key])) for key in ("voice_over", "music") if audio.get(key)]
    if not paths:
        silent.replace(target)
        return
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", silent]
    filters, labels = [], []
    duration = cut["expected_duration"]
    for i, (key, path) in enumerate(paths, 1):
        cmd += ["-i", path]
        gain = audio["voice_gain" if key == "voice_over" else "music_gain"]
        chain = f"[{i}:a]aresample=48000,asetpts=PTS-STARTPTS,volume={gain},apad,atrim=duration={duration}"
        if key == "music":
            chain += f",afade=t=out:st={max(0,duration-3)}:d=3"
        filters.append(chain + f"[a{i}]")
        labels.append(f"[a{i}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0,alimiter=limit=0.95[audio]")
    run(cmd + ["-filter_complex", ";".join(filters), "-map", "0:v", "-map", "[audio]", "-c:v", "copy",
               "-c:a", "aac", "-b:a", "192k", "-t", str(duration), "-movflags", "+faststart", target])


def review(data, cut, target, records):
    folder = OUT / "review" / target.stem
    folder.mkdir(parents=True, exist_ok=True)
    contact = Image.new("RGB", (1280, math.ceil(len(records)/2)*390), data["palette"]["background"])
    draw = ImageDraw.Draw(contact)
    start = 0
    for i, row in enumerate(cut["timeline"]):
        path = folder / f"{i+1:02}-shot-{row['shot']}-middle.png"
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(start + row["duration"]/2), "-i", target,
             "-frames:v", "1", "-update", "1", path])
        with Image.open(path) as frame:
            frame = frame.convert("RGB")
            if max(frame.getextrema()[c][1] for c in range(3)) < 32:
                raise ValueError(f"Black midpoint: {path}")
            contact.paste(frame.resize((640,360)), ((i%2)*640, (i//2)*390))
        draw.text(((i%2)*640+12, (i//2)*390+363), f"Shot {row['shot']} | {start:.3f}s | {records[i]['status']}", fill="white")
        start += row["duration"]
    contact.save(folder / "contact.jpg")
    info = probe(target)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert video["codec_name"] == "h264" and video["pix_fmt"] == "yuv420p"
    assert (video["width"], video["height"], video["r_frame_rate"]) == (1920,1080,"30/1")
    assert int(video["nb_frames"]) == frames(cut["expected_duration"], data["fps"])
    assert abs(float(info["format"]["duration"])-cut["expected_duration"]) < .034
    if not any(cut["audio"].get(k) for k in ("voice_over", "music")):
        assert all(s["codec_type"] != "audio" for s in info["streams"])
    (folder / "ffprobe.json").write_text(json.dumps(info,indent=2)+"\n")
    return info["format"]["duration"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cut", choices=["all","master","30s"], default="all")
    args = parser.parse_args()
    data = json.loads((EDIT / "assembly.json").read_text())
    validate(data)
    data["brand_name"] = json.loads(local(data["brand_file"]).read_text())["name"]
    OUT.mkdir(parents=True, exist_ok=True)
    types = Type(data)
    shots = {s["id"]: s for s in data["shots"]}
    report = {}
    for name, cut in data["cuts"].items():
        if args.cut not in ("all",name):
            continue
        work = OUT / "work" / name
        work.mkdir(parents=True,exist_ok=True)
        parts, records = [], []
        for n, row in enumerate(cut["timeline"]):
            shot = deepcopy(shots[row["shot"]])
            shot.update({k:v for k,v in row.items() if k != "shot"})
            print(f"{name}: shot {shot['id']} ({row['duration']} s)", flush=True)
            remaining = row["duration"]
            record = dict(shot=shot["id"],duration=row["duration"],status="filled",sources=[],waiting_for=[])
            for j, edit in enumerate(shot["edits"]):
                if remaining <= 0:
                    break
                edit = deepcopy(edit)
                edit["duration"] = min(edit["duration"], remaining)
                dest = work / f"{n:02}-{j:02}.mp4"
                missing = render_edit(data,types,shot,edit,dest,record["sources"])
                if missing:
                    record["status"] = "placeholder"
                    record["waiting_for"] += missing
                parts.append(dest)
                remaining -= edit["duration"]
            records.append(record)
        listing = work / "concat.txt"
        listing.write_text("".join(f"file '{p.name}'\n" for p in parts))
        silent = work / "silent.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", listing,
             "-map", "0:v:0", "-c", "copy", "-movflags", "+faststart", silent])
        target = OUT / cut["output"]
        add_audio(cut,silent,target)
        length = review(data,cut,target,records)
        report[name] = dict(output=str(target.relative_to(ROOT)),duration=length,shots=records)
        print(f"Verified {target.relative_to(ROOT)}: {length} s",flush=True)
    (OUT / "render-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")


if __name__ == "__main__":
    main()
