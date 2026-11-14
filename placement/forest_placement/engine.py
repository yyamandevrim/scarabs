"""Analysis orchestration, reproducible cache keys, comparison and map products."""
from __future__ import annotations
import hashlib
import json
import math
import os
import time
from functools import lru_cache
from pathlib import Path
import numpy as np
from pyproj import Transformer
from shapely import contains_xy
from shapely.geometry import Polygon
from .core import camera_sector, footprint_radii, sightlines, summarize
from .models import Candidate
from .maps import write_overlay
from .palette import map_color

ROOT=Path(__file__).resolve().parents[1]
PREP=Path(os.environ.get('PLACEMENT_PREPARED', ROOT/'data/prepared'))
CACHE=Path(os.environ.get('PLACEMENT_CACHE', ROOT/'data/results'))
TO_METRIC=Transformer.from_crs(4326,3067,always_xy=True)
TO_LONLAT=Transformer.from_crs(3067,4326,always_xy=True)
ALGORITHM='opaque-ray-half-cell-v8-360-sectors-en'
SCENARIOS=('bare_ground','bare_smoke','canopy_ground','canopy_smoke')

@lru_cache(maxsize=2)
def load_grid(resolution):
    with np.load(PREP/(resolution+'.npz')) as f:return {k:f[k] for k in f.files}

def metadata():
    path=PREP/'metadata.json'
    if not path.exists():raise FileNotFoundError('Data is not ready. Run uv run python scripts/prepare_data.py from placement/.')
    meta = json.loads(path.read_text())
    # Older prepared datasets remain usable without rebuilding numeric rasters.
    names = {
        'Varsayılan 20 m kapalı taç senaryosu (ölçüm değil)': 'Assumed 20 m opaque canopy scenario (not measured)',
        'Luke MS-NFI 2023 sayısal ortalama ağaç boyu + taç örtüsü; eksik orman hücrelerinde 20 m varsayımı': 'Luke MS-NFI 2023 numeric mean tree height + canopy cover; 20 m assumed in missing forest cells',
    }
    meta["canopy_name"] = names.get(meta.get("canopy_name"), meta.get("canopy_name"))
    return meta

def priority_mask(points,x,y):
    if not points:return np.zeros(x.shape,dtype=bool)
    polygon=Polygon([TO_METRIC.transform(*p) for p in points])
    return contains_xy(polygon,x,y)

def sector(candidate,camera,x,y,dz):
    spans=footprint_radii(dz,camera.tilt,camera.vfov,candidate.max_range,candidate.earth_radius)
    polygons=[]
    angles=np.radians(np.linspace(candidate.heading+camera.yaw-60,candidate.heading+camera.yaw+60,61))
    for inner,outer in spans:
        xx=np.concatenate((x+outer*np.sin(angles),x+inner*np.sin(angles[::-1])))
        yy=np.concatenate((y+outer*np.cos(angles),y+inner*np.cos(angles[::-1])))
        lon,lat=TO_LONLAT.transform(xx,yy)
        polygons.append([[a,b] for a,b in zip(lat,lon)])
    return dict(polygons=polygons,radii_m=spans)

def analyze(candidate:Candidate,use_cache=True):
    started=time.perf_counter();meta=metadata()
    key=hashlib.sha256(json.dumps(dict(input=candidate.model_dump(),data=meta['files'],algorithm=ALGORITHM),sort_keys=True).encode()).hexdigest()[:24]
    CACHE.mkdir(parents=True,exist_ok=True)
    resultfile=CACHE/(key+'.json')
    if use_cache and resultfile.exists():
        result=json.loads(resultfile.read_text());result['cached']=True;result['request_seconds']=round(time.perf_counter()-started,4);return result
    grid=load_grid(candidate.resolution);cell=int(grid['cell']);bounds=grid['bounds']
    x,y=TO_METRIC.transform(candidate.lon,candidate.lat)
    fullrow=int((bounds[3]-y)//cell);fullcol=int((x-bounds[0])//cell)
    if not(0<=fullrow<grid['terrain'].shape[0] and 0<=fullcol<grid['terrain'].shape[1]):raise ValueError('Candidate is outside the prepared region.')
    if not grid['valid'][fullrow,fullcol]:raise ValueError('No valid elevation at this point.')
    if grid['water'][fullrow,fullcol]>.5:raise ValueError('Choose a land launch point; this cell is mostly water.')
    buffer=int(math.ceil(candidate.max_range/cell))+2
    r0=max(0,fullrow-buffer);r1=min(grid['terrain'].shape[0],fullrow+buffer+1)
    c0=max(0,fullcol-buffer);c1=min(grid['terrain'].shape[1],fullcol+buffer+1)
    data={k:v[r0:r1,c0:c1] for k,v in grid.items() if v.ndim==2}
    localbounds=[float(bounds[0]+c0*cell),float(bounds[3]-r1*cell),float(bounds[0]+c1*cell),float(bounds[3]-r0*cell)]
    ox=(x-localbounds[0])/cell;oy=(localbounds[3]-y)/cell
    observer_z=float(grid['terrain'][fullrow,fullcol]+candidate.height)
    xx,yy=np.meshgrid(localbounds[0]+(np.arange(c1-c0)+.5)*cell,localbounds[3]-(np.arange(r1-r0)+.5)*cell)
    dx,dy=xx-x,yy-y;distance=np.hypot(dx,dy)
    eligible=(distance<=candidate.max_range)
    priority=priority_mask(candidate.priority,xx,yy)
    los=sightlines(data['terrain'],data['surface'],data['valid'],ox,oy,observer_z,cell,float(candidate.max_range),float(candidate.smoke_height),float(candidate.earth_radius))
    ground_dz=data['terrain']-observer_z-distance**2/(2*candidate.earth_radius)
    smoke_dz=data['surface']+candidate.smoke_height-observer_z-distance**2/(2*candidate.earth_radius)
    masks=[]; fovs=[]
    for i in range(4):
        dz=ground_dz if i%2==0 else smoke_dz
        fovs.append(np.array([camera_sector(dx,dy,dz,candidate.heading+cam.yaw,cam.tilt,cam.hfov,cam.vfov)&eligible for cam in candidate.cameras]))
        masks.append(fovs[-1]&los[i])
    active=[i for i,c in enumerate(candidate.cameras) if c.active]
    def metrics(i,indices):
        return summarize(masks[i][indices],data['forest'],data['water'],eligible,cell*cell,priority,fovs[i][indices])
    results={};images={}
    for i,name in enumerate(SCENARIOS):
        values,counts=metrics(i,active);results[name]=values
        rgba=np.zeros((*eligible.shape,4),dtype=np.uint8)
        forest=data['forest']>0
        for mask,color in [(eligible&forest&~np.any(fovs[i][active],axis=0),map_color('outside',125)),(eligible&forest&np.any(fovs[i][active],axis=0)&(counts==0),map_color('occluded',190)),(eligible&forest&(counts==1),map_color('visible',195)),(eligible&forest&(counts>=2),map_color('overlap',220)),(eligible&(data['water']>0)&(counts>0),map_color('water',95))]:
            rgba[mask]=color
        imagefile=CACHE/(key+'_'+name+'.png')
        llbounds=write_overlay(rgba,localbounds,imagefile,cell)
        images[name]=dict(url='/results/'+imagefile.name,bounds=llbounds)
    cameras=[dict(camera=i+1,label=f'Camera {i+1}',metrics={name:metrics(j,[i])[0] for j,name in enumerate(SCENARIOS)}) for i in range(3)]
    local_r=fullrow-r0;local_c=fullcol-c0
    target_dz=[float(data['terrain'][local_r,local_c]-observer_z),float(data['surface'][local_r,local_c]+candidate.smoke_height-observer_z)]
    sectors=[dict(label=f'Camera {i+1}',active=True,footprints={name:sector(candidate,c,x,y,target_dz[j%2]) for j,name in enumerate(SCENARIOS)}) for i,c in enumerate(candidate.cameras)]
    clipped=bool(min(x-bounds[0],bounds[2]-x,y-bounds[1],bounds[3]-y)<candidate.max_range)
    unknown=round(float(np.sum(data['forest']*eligible*~data['valid'])*cell*cell/10000),3)
    # Conservative provenance, not an affected-ray mask or hectare estimate. Include
    # the entire sampled window: boundary rays can cross cells centred outside range.
    unknown_elevation=bool(np.any(~data['valid']))
    notes=[f"NLS 10 m (2019 archive), Syke CORINE 2024 (20 m). {meta['canopy_name']}.",
           f"Missing forest canopy data: {meta['assumed_canopy_forest_pct']}%; a 20 m opaque canopy is assumed in these cells.",
           'Cells with canopy cover >0 are treated as opaque. Mean height is not an individual treetop height; transparency is not modelled.',
           'Building heights included.' if meta['buildings_included'] else 'No building heights; building obstruction is omitted. Built-up areas are shown only on the map.',
           f'{cell} m analysis grid; terrain/obstruction heights use cell maxima, and target area is weighted by the 20 m forest fraction.',
           'Earth curvature included; atmospheric refraction, haze, wind and optical detection are not modelled.',
           'The target is a single geometric point at the selected height above the canopy surface; this is not a smoke-dispersion model.']
    if clipped:notes.append('Range extends beyond the data boundary; areas include only the prepared region.')
    if unknown:notes.append(f'{unknown} ha of forest with missing elevation is included in the blind area; visibility could not be verified.')
    if unknown_elevation:notes.append('Unknown elevation in the analysis window: crossing sightlines remain unverified and blind. In-view blind area may include these rays as well as physical obstruction; affected area has not been quantified.')
    result=dict(id=key,input=candidate.model_dump(),resolution_m=cell,observer_elevation_m=round(observer_z,2),
        active_cameras=active,mode='360° · three cameras',
        metrics=results,camera_breakdown=cameras,images=images,sectors=sectors,
        uncertainty=notes,range_clipped=clipped,unknown_forest_ha=unknown,unknown_elevation_in_window=unknown_elevation,
        field_checks=dict(road_access='to be verified in the field',shadow='to be verified in the field',site_constraints='to be verified in the field'),
        computed_seconds=round(time.perf_counter()-started,4),cached=False,data_prepared_at=meta['prepared_at'],algorithm=ALGORITHM)
    # Bounded generated cache: 256 analyses, including their four images.
    entries=sorted(CACHE.glob('*.json'),key=lambda p:p.stat().st_mtime)
    for old in entries[:-255]:
        for asset in CACHE.glob(old.stem+'*'):
            if asset.is_file():asset.unlink(missing_ok=True)
    tmp=resultfile.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False));tmp.replace(resultfile)
    result['request_seconds']=round(time.perf_counter()-started,4)
    return result
