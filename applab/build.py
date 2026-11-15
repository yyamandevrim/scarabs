#!/usr/bin/env python3
"""Assemble a clean ACORN App Lab app and ZIP from the canonical sources."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "applab"
DIST = HERE / "dist"


def model_source():
    spec = importlib.util.spec_from_file_location("acorn_fetch_model", ROOT / "station/scripts/fetch_model.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build():
    fetch = model_source()
    model = ROOT / "station/models/smoke.onnx"
    if not model.is_file():
        subprocess.run([sys.executable, str(ROOT / "station/scripts/fetch_model.py")], check=True)
    if fetch.digest(model) != fetch.MODEL_SHA:
        raise ValueError("Model checksum mismatch; restore with station/scripts/fetch_model.py")
    DIST.mkdir(exist_ok=True)
    app = DIST / "acorn"
    if app.exists():
        shutil.rmtree(app)
    (app / "sketch").mkdir(parents=True)
    (app / "python/models").mkdir(parents=True)
    for name in ("app.yaml", "README.md"):
        shutil.copyfile(HERE / name, app / name)
    shutil.copyfile(HERE / "sketch.yaml", app / "sketch/sketch.yaml")
    firmware = ROOT / "firmware/acorn_mcu"
    # Override the existing configurable switch; LED4 stays enabled. No external LED is assumed.
    (app / "sketch/sketch.ino").write_text("// Generated: on-board LED4 only.\n#define LED_EXTERNAL 0\n" + (firmware / "acorn_mcu.ino").read_text())
    for source in sorted(firmware.glob("*.h")):
        shutil.copyfile(source, app / "sketch" / source.name)
    for source in sorted((ROOT / "station/station").rglob("*")):
        rel = source.relative_to(ROOT / "station/station")
        if not source.is_file() or "__pycache__" in rel.parts:
            continue
        if source.name == ".DS_Store":
            continue
        if source.suffix != ".py" and rel.parts[0] != "static":
            continue
        if rel.parts[0] == "static" and source.suffix not in {".js", ".css", ".woff2", ".txt", ".svg", ".html", ".md"}:
            raise ValueError(f"Unexpected panel asset: {rel}")
        if source.is_symlink() or source.name.startswith("."):
            raise ValueError(f"Unexpected station source: {rel}")
        destination = app / "python/station" / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    for name in ("main.py", "settings.example.toml"):
        shutil.copyfile(HERE / "python" / name, app / "python" / name)
    shutil.copyfile(ROOT / "station/config.toml", app / "python/config.toml")
    shutil.copyfile(ROOT / "station/scripts/fetch_model.py", app / "python/fetch_model.py")
    shutil.copyfile(model, app / "python/models/smoke.onnx")
    project = tomllib.loads((ROOT / "station/pyproject.toml").read_text())["project"]
    dependencies = []
    for dependency in project["dependencies"]:
        if dependency.startswith("opencv-python-headless"):
            # Explicit installs make uv try to fetch Arduino's private-version wheel from PyPI.
            dependencies.append(f"# Base image supplies {dependency}; do not reinstall its custom wheel.")
        else:
            dependencies.append(dependency)
    (app / "python/requirements.txt").write_text("# Generated from station/pyproject.toml; App Lab supplies arduino.app_utils.\n" + "\n".join(dependencies) + "\n")
    # Allowlist assembly above never copies local TOML, .env, media, data or caches.
    manifest = {p.relative_to(app).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(app.rglob("*")) if p.is_file()}
    (app / "BUILD.json").write_text(json.dumps({"files_sha256": manifest, "model_source": fetch.URL,
                                               "model_license": "AGPL-3.0"}, indent=2) + "\n")
    archive = DIST / "acorn.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as out:
        for path in sorted(app.rglob("*")):
            if path.is_file():
                out.write(path, path.relative_to(app).as_posix())
    print(f"App: {app}\nZIP: {archive}\nSize: {archive.stat().st_size:,} bytes")
    return app, archive


if __name__ == "__main__":
    build()
