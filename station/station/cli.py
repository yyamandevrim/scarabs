"""Run the local panel or benchmark the identical detector on recorded video."""
import argparse
import json
import logging
import platform
from pathlib import Path
import time
import cv2
import numpy as np
from .alarm import AlarmRule
from .config import load_config
from .detector import SmokeDetector


def benchmark(config, clip, frames, stride, warmup):
    detector = SmokeDetector(config.model,config.input_size,config.confidence,config.nms_iou,config.ort_threads)
    capture = cv2.VideoCapture(str(clip))
    if not capture.isOpened():
        raise ValueError(f"Cannot open clip: {clip}")
    samples, positive, index, first = [], 0, 0, True
    rule = AlarmRule(config.similarity_iou)
    alarm_positive = 0
    try:
        while len(samples) < frames:
            ok, image = capture.read()
            if not ok:
                break
            if index % stride == 0:
                if first:
                    for _ in range(warmup):
                        detector.predict(image)
                    first = False
                detections, timings = detector.predict(image)
                positive += bool(detections)
                alarm_positive += bool(rule.observe(detections))
                samples.append(timings)
            index += 1
    finally:
        capture.release()
    if not samples:
        raise ValueError("No readable benchmark frames")
    result = {"platform":platform.platform(),"machine":platform.machine(),"provider":"CPUExecutionProvider", "model":str(config.model),"clip":str(clip),"input_size":config.input_size,"confidence":config.confidence,"ort_threads":config.ort_threads,"frames":len(samples),"positive_frames":positive,"alarm_positive_frames":alarm_positive,"stride":stride,"warmup":warmup,"note":"Measured on this machine only; not a UNO Q performance claim"}
    for key in samples[0]:
        values = [sample[key] for sample in samples]
        result[key] = {"mean":float(np.mean(values)),"p50":float(np.percentile(values,50)),"p95":float(np.percentile(values,95))}
    print(json.dumps(result,indent=2))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",default="config.toml")
    sub=parser.add_subparsers(dest="command",required=True)
    serve=sub.add_parser("serve")
    serve.add_argument("--host",default="127.0.0.1")
    serve.add_argument("--port",default=8080,type=int)
    bench=sub.add_parser("benchmark")
    bench.add_argument("clip",type=Path)
    bench.add_argument("--frames",type=int,default=60)
    bench.add_argument("--stride",type=int,default=25)
    bench.add_argument("--warmup",type=int,default=3)
    archive=sub.add_parser("archive-events",help="Stop the server first. Move events and evidence to data/archive/ (or delete them) for a clean panel")
    archive.add_argument("--delete",action="store_true",help="Permanently delete instead of archiving")
    archive.add_argument("--yes",action="store_true",help="Do not ask for confirmation")
    for command,text in (("unplug","Simulate a live dropout of a recorded (file) camera source"),("replug","Restore a source hidden by unplug")):
        sub.add_parser(command,help=text).add_argument("slot",choices=("left","centre","right"))
    args=parser.parse_args()
    try:
        config=load_config(args.config)
        if args.command=="serve":
            # Evidence logs (clip format and encode time) go to the terminal.
            logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
            import uvicorn
            from .runtime import Station
            from .web import create_app
            uvicorn.run(create_app(Station(config)),host=args.host,port=args.port)
        elif args.command=="archive-events":
            from .maintenance import archive_events, event_summary
            summary=event_summary(config.data_dir)
            word="DELETE" if args.delete else "ARCHIVE"
            if not args.yes:
                print(f"{config.data_dir}: {summary['events']} events, {summary['media_files']} evidence files.")
                print("Permanently delete them?" if args.delete else "Move them to data/archive/ (kept, not shown in the panel)?")
                try:
                    answer=input(f"Type {word} to continue: ")
                except EOFError:
                    answer=""
                if answer.strip()!=word:
                    parser.exit(1,"Cancelled; nothing changed.\n")
            result=archive_events(config.data_dir,delete=args.delete)
            print(json.dumps(result,indent=2))
        elif args.command in ("unplug","replug"):
            from . import maintenance
            print(getattr(maintenance,args.command)(config,args.slot))
        else:
            if args.frames < 1 or args.stride < 1 or args.warmup < 0:
                parser.error("frames and stride must be positive; warmup cannot be negative")
            benchmark(config,args.clip,args.frames,args.stride,args.warmup)
    except (ValueError,FileNotFoundError,RuntimeError) as exc:
        parser.exit(2,f"Configuration/startup error: {exc}\n")

if __name__=="__main__":
    main()
