from unittest.mock import Mock
import pytest
from station.config import Config
from station.alarm import Detection, EventTracker
from station.runtime import Station


def make_config(config, **options):
    return Config(cameras=config.cameras, model=config.model, data_dir=config.data_dir, **options)


def test_field_default_keeps_small_smoke_input_and_slow_timing(config):
    cfg = make_config(config)
    assert (cfg.profile, cfg.input_size, cfg.confidence, cfg.analysis_hz) == ('field', 640, .25, 1/6)
    assert cfg.analysis_interval == 6
    assert cfg.event_timeout == 36
    assert cfg.alarm_gap_seconds == 12


def test_demo_profile_uses_measured_near_smoke_settings(config):
    cfg = make_config(config, profile='demo')
    assert (cfg.input_size, cfg.confidence, cfg.analysis_hz, cfg.event_timeout) == (192, .35, 1, 12)


def test_profile_values_remain_overridable_and_timeout_tracks_interval(config):
    cfg = make_config(config, profile='field', input_size=320, confidence=.4, analysis_hz=.1)
    assert (cfg.input_size, cfg.confidence, cfg.analysis_interval, cfg.event_timeout, cfg.alarm_gap_seconds) == (320, .4, 10, 60, 20)
    assert make_config(config, profile='demo', event_timeout=20).event_timeout == 20
    with pytest.raises(ValueError, match='profile'):
        make_config(config, profile='unknown')


@pytest.mark.parametrize('profile,rate', [('field', 1/6), ('demo', 1), ('field', .1)])
def test_slow_three_of_five_opens_and_survives_a_full_vote_window(config, profile, rate):
    cfg = make_config(config, profile=profile, analysis_hz=rate)
    tracker = EventTracker(cfg.similarity_iou, cfg.event_timeout, cfg.alarm_gap_seconds)
    detection = Detection((.1, .1, .3, .3), .8)
    create, extend, close = Mock(return_value='one'), Mock(), Mock()
    step = 1 / rate
    for i, boxes in enumerate(([detection], [], [detection], [], [detection])):
        tracker.update(boxes, i * step, create, extend, close)
    create.assert_called_once_with(detection, 4 * step)
    for i in range(5, 10):
        tracker.update([], i * step, create, extend, close)
    tracker.update([detection], 10 * step, create, extend, close)
    close.assert_not_called()
    create.assert_called_once()
    tracker.update([], 10 * step + cfg.event_timeout + .01, create, extend, close)
    close.assert_called_once()


def test_analysis_gap_discards_old_votes_before_new_alarm(config):
    tracker = EventTracker(.25, 15, 10)
    detection = Detection((.1, .1, .3, .3), .8)
    create, extend, close = Mock(return_value='one'), Mock(), Mock()
    for now in (0, 5, 25, 30):
        tracker.update([detection], now, create, extend, close)
    create.assert_not_called()
    tracker.update([detection], 35, create, extend, close)
    create.assert_called_once_with(detection, 35)


def test_status_exposes_effective_profile_and_overrides(config):
    cfg = make_config(config, profile='demo', confidence=.4)
    station = Station(cfg, detector=object())
    try:
        profile = station.status()['analysis_profile']
        assert profile == {'name': 'demo', 'input_size': 192, 'detector_view': 'full', 'confidence': .4,
                           'analysis_hz': 1, 'interval_seconds': 1, 'event_timeout_seconds': 12,
                           'history_gap_seconds': 3, 'required_detections': 3, 'window_analyses': 5}
    finally:
        station.stop()
