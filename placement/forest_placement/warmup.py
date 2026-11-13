"""Compile the exact float32/bool LOS signature during image build and load at startup."""
import time
import numpy as np
from .core import sightlines

def warmup(load_data=False):
    started=time.perf_counter()
    a=np.zeros((6,6),dtype=np.float32)[1:4,1:4]
    sightlines(a,a,np.ones((6,6),dtype=np.bool_)[1:4,1:4],1.5,1.5,600.0,40,12000.0,50.0,6371000.0)
    if load_data:
        from .engine import load_grid, metadata
        metadata()
        for resolution in ('coarse','detailed'):load_grid(resolution)
    return time.perf_counter()-started

if __name__=='__main__':print(f'Warm-up: {warmup():.3f}s')
