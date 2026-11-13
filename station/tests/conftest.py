from pathlib import Path
import time
import cv2
import numpy as np
import pytest
from station.config import Config, CameraConfig

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def config(tmp_path):
    return Config(cameras=[CameraConfig('left','missing.avi',yaw=-70),CameraConfig('centre','missing.avi'),CameraConfig('right','missing.avi',active=False,yaw=70)],model=ROOT/'models/smoke.onnx',data_dir=tmp_path/'data',analysis_hz=10,retry_seconds=.03,stale_seconds=.2,event_timeout=.2,pre_seconds=.1,post_seconds=.1,clip_fps=10,clip_width=160)

@pytest.fixture
def video(tmp_path):
    # Synthetic fixture exercises capture mechanics only, never labelled real footage.
    path=tmp_path/'mechanics.avi'
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),25,(160,90))
    assert writer.isOpened()
    for i in range(100):
        frame=np.full((90,160,3),i,dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return path


def wait_until(predicate,timeout=3):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if predicate():return
        time.sleep(.02)
    assert predicate(), 'Condition not reached before timeout'
