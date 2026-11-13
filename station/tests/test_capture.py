from dataclasses import replace
import time
import numpy as np
from station.capture import LatestFrame, CaptureWorker
from station.runtime import Station
from conftest import wait_until

class EmptyDetector:
    def predict(self,frame):
        return [],{'preprocess_ms':0.1,'inference_ms':1.,'analysis_ms':1.1}


def test_latest_frame_only():
    latest=LatestFrame()
    for i in range(1000):latest.put(i,i/10)
    assert latest.get().image==999
    assert latest.get().sequence==1000
    assert latest.get().timestamp==99.9
    latest.clear()
    assert latest.get() is None


def test_slow_consumer_sees_latest_not_queue(config,video):
    worker=CaptureWorker(replace(config.cameras[0],source=str(video),width=160,height=90),config)
    worker.start()
    try:
        wait_until(lambda:worker.latest.sequence>2)
        first=worker.latest.get()
        time.sleep(.25)
        second=worker.latest.get()
        assert second.sequence-first.sequence>=4
        assert worker.latest.get() is second
        assert len(worker.ring)<=worker.ring.maxlen
    finally:worker.stop()


def test_loss_other_active_camera_continues_and_retries(config,video,tmp_path):
    missing=tmp_path/'recovered.avi'
    cameras=[replace(c,source=str(missing if c.name=='left' else video),width=160,height=90) for c in config.cameras]
    station=Station(replace(config,cameras=cameras),detector=EmptyDetector())
    station.start()
    try:
        wait_until(lambda:station.metrics['centre']['analyses']>=3)
        states={c['name']:c for c in station.status()['cameras']}
        assert states['left']['status_text']=='bağlantı koptu'
        assert states['centre']['connected']
        assert states['right']['status_text']=='takılı, bağlı değil'
        assert 'right' not in station.workers
        before=station.metrics['centre']['analyses']
        import shutil
        shutil.copy(video,missing)
        wait_until(lambda:station.metrics['left']['analyses']>=2)
        assert station.metrics['centre']['analyses']>before
    finally:
        station.stop();station.store.shutdown()


def test_disconnect_after_open_and_reconnect(config,video):
    class Disconnecting:
        def __init__(self):self.count=0
        def isOpened(self):return True
        def get(self,key):return 25
        def read(self):
            self.count+=1
            time.sleep(.01)
            return (True,np.zeros((90,160,3),np.uint8)) if self.count<4 else (False,None)
        def set(self,*args):pass
        def release(self):pass
    attempts=[]
    def factory():
        attempts.append(1)
        return Disconnecting()
    worker=CaptureWorker(replace(config.cameras[0],kind='usb',source='/dev/v4l/by-id/test'),replace(config,retry_seconds=.1),factory)
    worker.start()
    try:
        wait_until(lambda:worker.status()['connected'])
        wait_until(lambda:not worker.status()['connected'])
        assert worker.latest.get() is None
        wait_until(lambda:len(attempts)>=2)
    finally:worker.stop()


def test_no_loop_eof_disconnected(config,video):
    worker=CaptureWorker(replace(config.cameras[0],source=str(video),loop=False,width=160,height=90),replace(config,retry_seconds=2))
    # Use a two-frame copy so EOF is quick and deterministic.
    import cv2
    path=video.parent/'short.avi'
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),25,(160,90))
    for _ in range(2):writer.write(np.zeros((90,160,3),np.uint8))
    writer.release();worker.camera.source=str(path)
    worker.start()
    try:
        wait_until(lambda:worker.latest.sequence>=2)
        wait_until(lambda:not worker.status()['connected'])
        assert worker.latest.get() is None
    finally:worker.stop()
