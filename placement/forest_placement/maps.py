"""Locally rendered map rasters, correctly warped to Leaflet's Web Mercator."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from rasterio import Affine
from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_bounds

def write_overlay(rgba,bounds,path,cell):
    height,width=rgba.shape[:2]
    transform=Affine(cell,0,bounds[0],0,-cell,bounds[3])
    dst_transform,w,h=calculate_default_transform('EPSG:3067','EPSG:3857',width,height,*bounds)
    dest=np.zeros((h,w,4),dtype=np.uint8)
    for b in range(4):
        reproject(rgba[:,:,b],dest[:,:,b],src_transform=transform,src_crs='EPSG:3067',
                  dst_transform=dst_transform,dst_crs='EPSG:3857',resampling=Resampling.nearest)
    Image.fromarray(dest).save(path)
    west,south,east,north=transform_bounds('EPSG:3857','EPSG:4326',dst_transform.c,dst_transform.f+h*dst_transform.e,dst_transform.c+w*dst_transform.a,dst_transform.f)
    return [[south,west],[north,east]]

def make_background(prepared):
    prepared=Path(prepared)
    with np.load(prepared/'detailed.npz') as d:
        h,w=d['terrain'].shape;rgba=np.zeros((h,w,4),dtype=np.uint8);rgba[:]=[222,229,213,255]
        forest,water,wet,built=d['forest'],d['water'],d['wetland'],d['built']
        for mask,color in [(wet,[163,189,162]),(built,[182,179,166]),(forest,[96,137,101]),(water,[143,183,200])]:
            for b in range(3):rgba[:,:,b]=(rgba[:,:,b]*(1-mask)+color[b]*mask).astype('uint8')
        dy,dx=np.gradient(d['terrain']);shade=np.clip(1+(dx-dy)*.009,.82,1.12)
        rgba[:,:,:3]=np.clip(rgba[:,:,:3]*shade[:,:,None],0,255).astype('uint8')
        bounds=d['bounds'].tolist();cell=int(d['cell'])
        llbounds=write_overlay(rgba,bounds,prepared/'background.png',cell)
        for name,color in [('forest',[47,119,67]),('water',[64,144,186])]:
            image=np.zeros_like(rgba);image[:,:,:3]=color;image[:,:,3]=(d[name]*100).astype('uint8')
            write_overlay(image,bounds,prepared/(name+'.png'),cell)
        (prepared/'map.json').write_text(json.dumps(dict(bounds=llbounds)))
