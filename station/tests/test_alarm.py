from unittest.mock import Mock
import pytest
from station.alarm import AlarmRule, Detection, EventTracker, iou

A=Detection((.1,.1,.3,.3),.8)
B=Detection((.7,.7,.9,.9),.9)
NEAR=Detection((.11,.11,.31,.31),.7)


def test_three_of_five_with_misses():
    rule=AlarmRule()
    assert rule.observe([A])==[]
    assert rule.observe([])==[]
    assert rule.observe([NEAR])==[]
    assert rule.observe([])==[]
    assert rule.observe([A])==[A]


def test_different_places_do_not_accumulate():
    rule=AlarmRule()
    for boxes in ([A],[B],[A],[],[B]):
        assert rule.observe(boxes)==[]


def test_many_boxes_in_one_analysis_count_once():
    rule=AlarmRule()
    assert rule.observe([A,A,A,A])==[]
    assert rule.observe([A])==[]
    assert rule.observe([A])==[A]


def test_votes_age_out_of_window():
    rule=AlarmRule()
    for boxes in ([A],[A],[],[],[],[A]):
        assert rule.observe(boxes)==[]


def test_similarity_is_configurable():
    rule=AlarmRule(.99)
    assert not rule.observe([A])
    assert not rule.observe([NEAR])
    assert not rule.observe([A])


def test_reset_after_camera_loss():
    rule=AlarmRule()
    rule.observe([A]);rule.observe([A]);rule.reset()
    assert not rule.observe([A])


def test_event_extension_and_timeout():
    tracker=EventTracker(.25,10)
    create=Mock(return_value='event1');extend=Mock();close=Mock()
    for now in (0,1,2):tracker.update([A],now,create,extend,close)
    create.assert_called_once_with(A,2)
    tracker.update([NEAR],3,create,extend,close)
    create.assert_called_once()
    extend.assert_called_once_with('event1',NEAR,3)
    tracker.update([],14,create,extend,close)
    close.assert_called_once_with('event1',14)
    assert not tracker.events


def test_unrelated_smoke_opens_separate_event():
    tracker=EventTracker(.25,10)
    create=Mock(side_effect=['one','two']);extend=Mock();close=Mock()
    for now in (0,1,2):tracker.update([A],now,create,extend,close)
    for now in (3,4,5):tracker.update([B],now,create,extend,close)
    assert create.call_count==2
    assert len(tracker.events)==2

@pytest.mark.parametrize('a,b,expected',[(A.box,A.box,1),(A.box,B.box,0),((0,0,0,0),A.box,0)])
def test_iou(a,b,expected):
    assert iou(a,b)==expected
