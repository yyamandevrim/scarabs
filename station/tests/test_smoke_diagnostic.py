"""Replay must preserve misses, spatial votes and interruption semantics."""
import importlib.util
from pathlib import Path
from station.alarm import Detection

SCRIPT = Path(__file__).parents[1] / 'scripts' / 'diagnose_smoke.py'


def load_script():
    spec = importlib.util.spec_from_file_location('diagnose_smoke', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_replay_counts_analyses_not_boxes_and_closes_after_timeout():
    replay = load_script().replay
    box = Detection((.1, .1, .5, .5), .6)
    records = [{'time': t, 'label': 'positive', 'detections': boxes}
               for t, boxes in enumerate(([box] * 4, [], [box], [], [box]))]
    result = replay(records, threshold=.35, timeout=12, history_gap=3)
    assert result['detection_frames'] == 3
    assert result['positive_misses'] == 2
    assert result['event_count'] == 1
    assert result['first_event_time'] == 4
    assert [row['votes'] for row in result['timeline']] == [[1, 1, 1, 1], [], [2], [], [3]]
    assert result['events'][0]['closed_at'] > 16


def test_replay_threshold_and_long_gap_do_not_manufacture_persistence():
    replay = load_script().replay
    strong = Detection((.1, .1, .5, .5), .6)
    weak = Detection(strong.box, .3)
    records = [{'time': t, 'label': 'positive', 'detections': [box]}
               for t, box in [(0, strong), (1, strong), (10, weak), (11, strong), (12, strong)]]
    high = replay(records, threshold=.35, timeout=12, history_gap=3)
    low = replay(records, threshold=.25, timeout=12, history_gap=3)
    assert high['event_count'] == 0
    assert high['positive_misses'] == 1
    assert low['event_count'] == 1
    assert low['first_event_time'] == 12
    assert low['timeline'][2]['history_reset'] is True


def test_replay_rejects_reversed_time_instead_of_misleading_votes():
    import pytest
    replay = load_script().replay
    with pytest.raises(ValueError, match='strictly increasing'):
        replay([{'time': 2, 'detections': [], 'label': 'negative'},
                {'time': 1, 'detections': [], 'label': 'negative'}], .35, 12, 3)


def test_saved_input_is_the_real_rgb_letterbox_tensor(tmp_path):
    import cv2
    import hashlib
    import json
    import numpy as np
    import pytest
    model = Path(__file__).parents[1] / 'models' / 'smoke.onnx'
    if not model.is_file():
        pytest.skip('Local model required for exact ORT input diagnostic')
    frame = np.full((240, 320, 3), (40, 1, 200), dtype=np.uint8)
    image = tmp_path / 'held.png'
    cv2.imwrite(str(image), frame)
    before = hashlib.sha256(image.read_bytes()).hexdigest()
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'series': [{'name': 'mechanics', 'samples': [
        {'image': 'held.png', 'time': 0, 'label': 'unknown',
         'provenance': 'Synthetic solid colour; preprocessing mechanics only'}]}]}))
    output = tmp_path / 'proof'
    load_script().diagnose(manifest, model, output, [192], [.35], save_inputs=True)
    tensor = np.load(output / 'input-0000-192.npy')
    assert tensor.shape == (1, 3, 192, 192)
    assert tensor.dtype == np.float32
    assert tensor[0, :, 24, 0] == pytest.approx([200/255, 1/255, 40/255])
    assert tensor[0, :, 0, 0] == pytest.approx([114/255]*3)
    assert hashlib.sha256(image.read_bytes()).hexdigest() == before
    assert np.array_equal(cv2.imread(str(output / 'input-0000-192.png'))[24, 0], [40, 1, 200])


def test_floor_collection_matches_direct_threshold_on_real_smoke():
    import cv2
    import pytest
    from station.detector import SmokeDetector
    root = Path(__file__).parents[1]
    model, clip = root / 'models/smoke.onnx', root / 'media/smoke.ogv'
    if not model.is_file() or not clip.is_file():
        pytest.skip('Local licensed clip and model required')
    cap = cv2.VideoCapture(str(clip))
    ok, frame = cap.read()
    cap.release()
    assert ok
    frame = cv2.resize(frame, (320, 240))
    detector = SmokeDetector(model, 192, .1)
    collected, _ = detector.predict(frame)
    assert any(d.confidence > .35 for d in collected)
    for threshold in (.25, .35, .45):
        detector.confidence = threshold
        direct, _ = detector.predict(frame)
        assert direct == [d for d in collected if d.confidence >= threshold]
