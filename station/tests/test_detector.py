"""Detector boundary tests: coordinate mapping, RGB layout, NMS and model rejection."""
from types import SimpleNamespace
import numpy as np
import pytest
import station.detector as module
from station.detector import SmokeDetector

class Session:
    names="{0: 'smoke'}"
    output=np.array([[[320,322],[320,322],[320,320],[160,160],[.9,.8]]],dtype=np.float32)
    def __init__(self,*args,**kwargs):pass
    def get_inputs(self):return [SimpleNamespace(name='images',shape=['batch',3,'height','width'])]
    def get_modelmeta(self):return SimpleNamespace(custom_metadata_map={'names':self.names})
    def run(self,unused,inputs):
        self.tensor=inputs['images']
        return [self.output]


def test_letterbox_rgb_original_coordinates_and_nms(tmp_path,monkeypatch):
    model=tmp_path/'model.onnx';model.touch()
    monkeypatch.setattr(module.ort,'InferenceSession',Session)
    detector=SmokeDetector(model)
    frame=np.zeros((360,640,3),np.uint8);frame[:,:,2]=255
    detections,timings=detector.predict(frame)
    assert len(detections)==1
    assert detections[0].box==pytest.approx((.25,100/360,.75,260/360))
    tensor=detector.session.tensor
    assert tensor.shape==(1,3,640,640) and tensor.dtype==np.float32
    assert tensor[0,0,200,0]==1 and tensor[0,2,200,0]==0
    assert tensor[0,0,0,0]==pytest.approx(114/255)
    assert all(value>=0 for value in timings.values())


def test_reject_general_object_detector(tmp_path,monkeypatch):
    model=tmp_path/'model.onnx';model.touch()
    class Coco(Session):names="{0:'person',1:'car'}"
    monkeypatch.setattr(module.ort,'InferenceSession',Coco)
    with pytest.raises(ValueError,match='single-class Pyronear smoke'):
        SmokeDetector(model)


def test_missing_model_has_setup_instruction(tmp_path):
    with pytest.raises(FileNotFoundError,match='fetch_model.py'):
        SmokeDetector(tmp_path/'missing.onnx')


def test_confidence_filter_no_detections(tmp_path,monkeypatch):
    model=tmp_path/'model.onnx';model.touch()
    monkeypatch.setattr(module.ort,'InferenceSession',Session)
    detector=SmokeDetector(model,confidence=.99)
    assert detector.predict(np.zeros((360,640,3),np.uint8))[0]==[]
