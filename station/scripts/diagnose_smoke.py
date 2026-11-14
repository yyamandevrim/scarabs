"""Offline held-frame smoke diagnosis; never opens a camera or writes station data.

Manifest: {"series": [{"name": "screen-smoke", "samples": [
  {"image": "frame.png", "time": 0, "label": "positive", "provenance": "..."}
]}]}. Paths are relative to the manifest. Times are seconds, strictly increasing
within each series. Labels are operator assertions, not model-derived truth.
Keep manifests, inputs and output outside the repository; output may be private.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import time

import cv2
import numpy as np
from station.alarm import EventTracker, iou
from station.detector import SmokeDetector


def replay(records, threshold, timeout, history_gap):
    """Replay actual sample timestamps through the production spatial tracker."""
    tracker = EventTracker(.25, timeout, history_gap)
    events, timeline = [], []

    def create(detection, now):
        key = len(events)
        events.append({'id': key, 'opened_at': now, 'last_seen': now,
                       'opening_confidence': detection.confidence, 'closed_at': None})
        return key

    def extend(key, detection, now):
        events[key]['last_seen'] = now

    def close(key, now):
        events[key]['closed_at'] = now

    previous = None
    for record in records:
        now = float(record['time'])
        if not np.isfinite(now) or (previous is not None and now <= previous):
            raise ValueError('Sample times must be finite and strictly increasing')
        reset = previous is not None and now - previous > history_gap
        detections = [d for d in record['detections'] if d.confidence >= threshold]
        before = len(events)
        tracker.update(detections, now, create, extend, close)
        votes = [sum(any(iou(d.box, p.box) >= .25 for p in frame)
                     for frame in tracker.rule.history) for d in detections]
        timeline.append({'time': now, 'label': record['label'],
                         'detections': [asdict(d) for d in detections], 'votes': votes,
                         'history_reset': reset, 'opened': len(events)-before,
                         'open_events': len(tracker.events)})
        previous = now
    if previous is not None:
        # Explicit synthetic drain, not an observed negative frame.
        tracker.update([], previous+timeout+.001, create, extend, close)
    positives = [row for row in timeline if row['label'] == 'positive']
    negatives = [row for row in timeline if row['label'] == 'negative']
    return {'threshold': threshold, 'timeout': timeout, 'history_gap': history_gap,
            'sample_count': len(timeline),
            'detection_frames': sum(bool(r['detections']) for r in timeline),
            'positive_samples': len(positives),
            'positive_misses': sum(not r['detections'] for r in positives),
            'negative_samples': len(negatives),
            'negative_detection_frames': sum(bool(r['detections']) for r in negatives),
            'negative_event_count': sum(r['opened'] for r in negatives),
            'event_count': len(events),
            'first_event_time': events[0]['opened_at'] if events else None,
            'first_event_delay_seconds': events[0]['opened_at']-timeline[0]['time'] if events else None,
            'events': events, 'timeline': timeline}


class InputRecorder:
    """Observe the actual tensor handed to ORT, without duplicating preprocessing."""
    def __init__(self, session):
        self.session, self.tensor, self.output = session, None, None

    def run(self, outputs, inputs):
        self.tensor = next(iter(inputs.values()))
        result = self.session.run(outputs, inputs)
        self.output = result[0]
        return result


def diagnose(manifest, model, output, sizes, thresholds, threads=2,
             timeout=12, history_gap=3, save_inputs=False):
    if not thresholds or any(not .1 <= t <= 1 for t in thresholds):
        raise ValueError('Thresholds must be in [0.1, 1]; collection floor is 0.1')
    if timeout <= 0 or history_gap <= 0:
        raise ValueError('Timeout and history gap must be positive')
    output.mkdir(parents=True, exist_ok=False)
    source = json.loads(manifest.read_text())
    held, provenance = {}, []
    for group in source['series']:
        name = group['name']
        if name in held:
            raise ValueError('Series names must be unique')
        held[name] = []
        for index, sample in enumerate(group['samples']):
            if sample['label'] not in ('positive', 'negative', 'unknown') or not sample.get('provenance'):
                raise ValueError('Each sample needs a label and provenance')
            path = manifest.parent / sample['image']
            image = cv2.imread(str(path))
            if image is None:
                raise ValueError(f'Unreadable held image: {path}')
            sample_id = len(provenance)
            provenance.append({**sample, 'series': name, 'index': index, 'id': sample_id,
                               'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                               'pixel_sha256': hashlib.sha256(image.tobytes()).hexdigest(),
                               'shape': list(image.shape)})
            held[name].append((sample_id, sample, image))
    report = {'machine': platform.platform(), 'provider': 'CPUExecutionProvider',
              'model_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
              'collection_floor': .1, 'ort_threads': threads, 'samples': provenance,
              'note': 'Held-frame offline replay; no live throughput or field accuracy claim. '
                      'Times are supplied sample times. Final closure is a synthetic drain. '
                      'Counts below 0.1 are censored. NMS IoU .45, spatial IoU .25.',
              'timing_note': 'Per-image timings include the first cold run; not a steady throughput benchmark.',
              'runs': []}
    for size in sizes:
        detector = SmokeDetector(model, size, .1, .45, threads)
        recorder = InputRecorder(detector.session)
        detector.session = recorder
        for name, samples in held.items():
            records = []
            for sample_id, sample, image in samples:
                started = time.perf_counter()
                detections, timings = detector.predict(image)
                raw = np.squeeze(recorder.output, axis=0)
                raw = raw.T if raw.shape[0] == 5 else raw
                top = raw[np.argsort(raw[:, 4])[-5:][::-1]]
                row = {'time': sample['time'], 'label': sample['label'],
                       'sample_id': sample_id, 'detections': detections, 'timings': timings,
                       'model_output': {'shape': list(recorder.output.shape),
                                        'max_score': float(top[0, 4]),
                                        'top_xywh_score': top.tolist()},
                       'wall_ms': (time.perf_counter()-started)*1000}
                records.append(row)
                if save_inputs:
                    stem = output / f'input-{sample_id:04d}-{size}'
                    np.save(stem.with_suffix('.npy'), recorder.tensor)
                    np.save(output / f'output-{sample_id:04d}-{size}.npy', recorder.output)
                    rgb = np.rint(recorder.tensor[0].transpose(1, 2, 0)*255).astype(np.uint8)
                    cv2.imwrite(str(stem.with_suffix('.png')), rgb[:, :, ::-1])
            report['runs'].append({'input_size': size, 'series': name,
                'unique_pixel_count': len({provenance[sid]['pixel_sha256'] for sid, _, _ in samples}),
                'raw': [{**r, 'detections': [asdict(d) for d in r['detections']]} for r in records],
                'sweeps': [replay(records, t, timeout, history_gap) for t in thresholds]})
    (output/'report.json').write_text(json.dumps(report, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New private directory outside repo')
    parser.add_argument('--sizes', type=int, nargs='+', default=[192, 320, 416, 640])
    parser.add_argument('--thresholds', type=float, nargs='+', default=[.25, .35, .45])
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--timeout', type=float, default=12)
    parser.add_argument('--history-gap', type=float, default=3)
    parser.add_argument('--save-inputs', action='store_true', help='Save exact ORT input/output tensors and letterbox PNGs')
    args = parser.parse_args()
    report = diagnose(args.manifest, args.model, args.output, args.sizes, args.thresholds,
                      args.threads, args.timeout, args.history_gap, args.save_inputs)
    for run in report['runs']:
        for sweep in run['sweeps']:
            print(json.dumps({'size': run['input_size'], 'series': run['series'],
                              **{k: v for k, v in sweep.items() if k not in ('timeline', 'events')}}))


if __name__ == '__main__':
    main()
