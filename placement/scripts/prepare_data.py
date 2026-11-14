"""Fetch real public numeric rasters; create aligned EPSG:3067 analysis caches.

Run from placement/: uv run python scripts/prepare_data.py
No credentials required. Large originals and derived assets stay under data/.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import ssl
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import rasterio
from rasterio import Affine
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds, transform as window_transform
from forest_placement.maps import make_background

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'
PREP=ROOT/'data/prepared'
BOUNDS=(345000,6650000,420120,6725120)
SHAPE=(3756,3756)
TRANSFORM=Affine(20,0,BOUNDS[0],0,-20,BOUNDS[3])
NLS='https://www.nic.funet.fi/index/geodata/mml/dem10m/'
WCS='https://paikkatiedot.ymparisto.fi/geoserver/inspire_lc/wcs'
LUKE='https://www.nic.funet.fi/index/geodata/luke/vmi/2023/'
SOURCES=[]
# Python's default CA store on macOS (uv-managed builds read /etc/ssl/cert.pem)
# lacks the HARICA root that the Syke WCS server chains to. certifi's Mozilla
# bundle has it. Verification stays on: hostname and chain are still checked.
try:
    import certifi
    CA_BUNDLE=certifi.where()
except ImportError:
    CA_BUNDLE=None
TLS=ssl.create_default_context(cafile=CA_BUNDLE)
CURL_CA={'CURL_CA_BUNDLE':CA_BUNDLE} if CA_BUNDLE else {}
# Pinned public data release (see tools/artifacts-manifest.json). When a fresh run
# reproduces these numeric caches byte for byte, metadata.json records the release
# timestamps so its bytes match the manifest; the run's own clock times are kept
# separately in preparation-run.json, never discarded.
RELEASE=dict(prepared_at='2026-11-13T19:54:06.478715+00:00',accessed='2026-11-13',
             # Published metadata stays byte-identical across UI translations.
             canopy_name='Luke MS-NFI 2023 sayısal ortalama ağaç boyu + taç örtüsü; eksik orman hücrelerinde 20 m varsayımı',
             files={'detailed.npz':'98d64016333bcc86e7ab98b50c712648d1dfdf37839b0fb472b2649a30b8bac8',
                    'coarse.npz':'42643b6899ef4313227fd79bcce71f61ecdb39a96c13619cf64765a17116f9ed'})

def write_metadata(metadata):
    """Publish release metadata separately from this preparation run’s clock."""
    run=dict(prepared_at=metadata['prepared_at'],accessed=sorted({s['accessed'] for s in metadata['sources']}),files=dict(metadata['files']))
    run['reproduced_release']=metadata['files']==RELEASE['files']
    if run['reproduced_release']:
        metadata['prepared_at']=RELEASE['prepared_at']
        if 'canopy_name' in metadata:
            metadata['canopy_name']=RELEASE['canopy_name']
        for item in metadata['sources']:item['accessed']=RELEASE['accessed']
    (PREP/'metadata.json').write_text(json.dumps(metadata,indent=2))
    (PREP/'preparation-run.json').write_text(json.dumps(run,indent=2))
    print('Reproduced pinned release:' if run['reproduced_release'] else 'New data release (differs from pinned manifest):',sorted(metadata['files']),flush=True)

def fetch(url,path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        print('Downloading',path.name,flush=True)
        tmp=path.with_suffix(path.suffix+'.part')
        with urllib.request.urlopen(url,timeout=180,context=TLS) as response, tmp.open('wb') as output:
            import shutil
            shutil.copyfileobj(response,output)
        tmp.replace(path)
    return path

def source(name,url,licence,**extra):
    SOURCES.append(dict(name=name,url=url,licence=licence,accessed=datetime.now(timezone.utc).date().isoformat(),**extra))

def regrid(path,method=Resampling.average,dtype='float32',nodata=-9999):
    out=np.full(SHAPE,nodata,dtype=dtype)
    with rasterio.open(path) as src:
        reproject(rasterio.band(src,1),out,src_transform=src.transform,src_crs=src.crs,
                  src_nodata=src.nodata,dst_transform=TRANSFORM,dst_crs='EPSG:3067',
                  dst_nodata=nodata,resampling=method,num_threads=2)
    return out

def nls_dem(local=None):
    if local:
        source('User-supplied NLS 10m DEM',str(Path(local).resolve()),'User must confirm source licence')
        return regrid(local)
    path=fetch(NLS+'dem10m_direct.vrt',RAW/'nls_index.vrt')
    root=ET.parse(path).getroot()
    gt=[float(x) for x in root.findtext('GeoTransform').split(',')]
    urls=[]
    for item in root.findall('.//ComplexSource'):
        rect=item.find('DstRect')
        x=gt[0]+int(rect.get('xOff'))*gt[1];y=gt[3]+int(rect.get('yOff'))*gt[5]
        right=x+int(rect.get('xSize'))*gt[1];bottom=y+int(rect.get('ySize'))*gt[5]
        if x<BOUNDS[2] and right>BOUNDS[0] and y>BOUNDS[1] and bottom<BOUNDS[3]:
            urls.append(NLS+item.findtext('SourceFilename'))
    def download(u):return fetch(u,RAW/'nls'/u.split('/')[-1])
    with ThreadPoolExecutor(max_workers=4) as pool: paths=list(pool.map(download,urls))
    dem=np.full(SHAPE,-9999,dtype='float32')
    for path in paths:
        a=regrid(path);mask=a!=-9999;dem[mask]=a[mask]
    source('NLS Finland 10m ground DEM, Paituli 2019 snapshot',NLS+'2019/','CC BY 4.0',tiles=urls,native_resolution_m=10)
    return dem

def luke_raster(theme):
    path=RAW/(theme+'.tif');url=LUKE+theme+'_vmi1x_1923.tif'
    if not path.exists():
        print('Clipping numeric Luke raster',theme,flush=True)
        with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT='120',**CURL_CA):
            with rasterio.open(url) as src:
                win=from_bounds(*BOUNDS,src.transform).round_offsets().round_lengths()
                # Expand a small collar to ensure complete destination support.
                win=rasterio.windows.Window(win.col_off-2,win.row_off-2,win.width+4,win.height+4)
                a=src.read(1,window=win)
                profile=src.profile.copy();profile.update(width=a.shape[1],height=a.shape[0],transform=window_transform(win,src.transform),compress='deflate')
                with rasterio.open(path,'w',**profile) as dst:dst.write(a,1)
    source('Luke MS-NFI 2023 '+theme,url,'CC BY 4.0',native_resolution_m=16,unit='dm' if theme=='keskipituus' else 'percent')
    # nearest avoids converting nodata codes into plausible measurements.
    return regrid(path,Resampling.nearest)

def block(a,factor,op='mean'):
    reshaped=a.reshape(a.shape[0]//factor,factor,a.shape[1]//factor,factor)
    if op=='max':return reshaped.max(axis=(1,3))
    if op=='min':return reshaped.min(axis=(1,3))
    return reshaped.mean(axis=(1,3),dtype=np.float32)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dem',help='Replace public NLS snapshot with a local georeferenced NLS DEM')
    parser.add_argument('--building-heights',help='Optional numeric heights above ground, metres, GeoTIFF')
    parser.add_argument('--assumed-canopy',action='store_true',help='Explicit 20m canopy scenario instead of downloading Luke')
    args=parser.parse_args()
    RAW.mkdir(parents=True,exist_ok=True);PREP.mkdir(parents=True,exist_ok=True)
    query=urllib.parse.urlencode(dict(service='WCS',version='1.0.0',request='GetCoverage',coverage='inspire_lc:LC.LandCoverRaster.2024',crs='EPSG:3067',bbox=','.join(map(str,BOUNDS)),resx=20,resy=20,format='GeoTIFF'))
    url=WCS+'?'+query
    clc=regrid(fetch(url,RAW/'corine2024.tif'),Resampling.nearest,dtype='uint16',nodata=65535)
    source('Syke CORINE Land Cover 2024, national 20m raster',url,'CC BY 4.0',native_resolution_m=20,publication='2026-09-29')
    forest=(clc>=3110)&(clc<3140)
    water=(clc>=5100)&(clc<5300)
    wetland=(clc>=4100)&(clc<4300)
    built=(clc>=1100)&(clc<1500)
    terrain=nls_dem(args.dem)
    # NLS sea holes may be completed with mean sea level ONLY for CORINE sea.
    sea=clc==5231
    sea_filled=(terrain==-9999)&sea
    terrain[sea_filled]=0
    valid=(terrain!=-9999)&(clc!=65535)
    if args.assumed_canopy:
        height=np.where(forest,20,0).astype('float32');cover=np.where(forest,100,0).astype('float32');missing=forest.copy()
        canopy_name='Assumed 20 m opaque canopy scenario (not measured)'
        source('Assumed opaque canopy scenario','local assumption','Not a real dataset',height_m=20)
    else:
        rawheight=luke_raster('keskipituus');rawcover=luke_raster('latvuspeitto')
        missing=forest&((rawheight<0)|(rawheight>=32766)|(rawcover<0)|(rawcover>=32766))
        # Luke estimates beyond CORINE forest still obstruct rays where measured.
        measured=(rawheight>=0)&(rawheight<32766)&(rawcover>0)&(rawcover<=100)
        height=np.where(measured,rawheight/10,0).astype('float32')
        cover=np.where((rawcover>=0)&(rawcover<=100),rawcover,0).astype('float32')
        height[missing]=20;cover[missing]=100
        canopy_name='Luke MS-NFI 2023 numeric mean tree height + canopy cover; 20 m assumed in missing forest cells'
    buildings=np.zeros(SHAPE,dtype='float32')
    if args.building_heights:
        buildings=np.maximum(regrid(args.building_heights,Resampling.max),0)
        source('User-supplied building heights',str(Path(args.building_heights).resolve()),'User must confirm source licence')
    metadata=dict(crs='EPSG:3067',bounds=BOUNDS,prepared_at=datetime.now(timezone.utc).isoformat(),
       sources=SOURCES,canopy_name=canopy_name,assumed_canopy_forest_pct=round(100*float(missing.sum())/forest.sum(),3),
       buildings_included=bool(args.building_heights),sea_filled_cells=int(sea_filled.sum()),invalid_cells=int((~valid).sum()),
       forest_definition='CORINE national codes 3111–3133 (311/312/313). Transitional woodland 324* excluded.',
       files={})
    for name,factor in [('detailed',2),('coarse',6)]:
        path=PREP/(name+'.npz')
        # Conservative high-point aggregation of terrain and obstruction heights.
        # Fractions preserve 20m target areas, unlike majority classification.
        ground=block(np.where(valid,terrain,0),factor,'max')
        surface=block(np.where(valid,terrain+np.maximum(height,buildings),0),factor,'max')
        np.savez_compressed(path,terrain=ground,surface=surface,
            valid=block(valid,factor,'min').astype(bool),forest=block(forest,factor),water=block(water,factor),
            wetland=block(wetland,factor),built=block(built,factor),cover=block(cover,factor),
            cell=20*factor,bounds=BOUNDS)
        metadata['files'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        print('Prepared',name,ground.shape,flush=True)
    write_metadata(metadata)
    make_background(PREP)
    print('Offline data ready:',PREP,flush=True)

if __name__=='__main__':main()
