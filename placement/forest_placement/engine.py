"""Analysis orchestration, reproducible cache keys, comparison and map products."""
from __future__ import annotations
import hashlib
import json
import math
import time
from functools import lru_cache
from pathlib import Path
import numpy as np
from pyproj import Transformer
from shapely import contains_xy
from shapely.geometry import Polygon
from .core import frustum, sightlines, summarize
from .models import Candidate
from .maps import write_overlay

ROOT=Path(__file__).resolve().parents[1]
PREP=ROOT/'data/prepared'
CACHE=ROOT/'data/results'
TO_METRIC=Transformer.from_crs(4326,3067,always_xy=True)
TO_LONLAT=Transformer.from_crs(3067,4326,always_xy=True)
ALGORITHM='opaque-ray-half-cell-v4-two-inputs'
SCENARIOS=('bare_ground','bare_smoke','canopy_ground','canopy_smoke')

@lru_cache(maxsize=2)
def load_grid(resolution):
    with np.load(PREP/(resolution+'.npz')) as f:return {k:f[k] for k in f.files}

def metadata():
    path=PREP/'metadata.json'
    if not path.exists():raise FileNotFoundError('Veri hazır değil. placement/ içinde uv run python scripts/prepare_data.py çalıştırın.')
    return json.loads(path.read_text())

def priority_mask(points,x,y):
    if not points:return np.zeros(x.shape,dtype=bool)
    polygon=Polygon([TO_METRIC.transform(*p) for p in points])
    return contains_xy(polygon,x,y)

def sector(candidate,camera,x,y):
    # Horizontal sector guide only; analytical masks use the full 3D frustum.
    angles=np.radians(np.linspace(candidate.heading+camera.yaw-camera.hfov/2,candidate.heading+camera.yaw+camera.hfov/2,45))
    xx=[x]+(x+candidate.max_range*np.sin(angles)).tolist()+[x]
    yy=[y]+(y+candidate.max_range*np.cos(angles)).tolist()+[y]
    lon,lat=TO_LONLAT.transform(xx,yy)
    return [[a,b] for a,b in zip(lat,lon)]

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
    if not(0<=fullrow<grid['terrain'].shape[0] and 0<=fullcol<grid['terrain'].shape[1]):raise ValueError('Aday hazırlanan veri alanı dışında.')
    if not grid['valid'][fullrow,fullcol]:raise ValueError('Aday noktasında geçerli yükselti verisi yok.')
    if grid['water'][fullrow,fullcol]>.5:raise ValueError('Balon çıkış noktası su üzerinde olamaz; karada bir nokta seçin.')
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
    los=sightlines(data['terrain'],data['surface'],data['valid'],ox,oy,observer_z,cell,candidate.max_range,candidate.smoke_height,candidate.earth_radius)
    ground_dz=data['terrain']-observer_z-distance**2/(2*candidate.earth_radius)
    smoke_dz=data['surface']+candidate.smoke_height-observer_z-distance**2/(2*candidate.earth_radius)
    masks=[]
    for i in range(4):
        dz=ground_dz if i%2==0 else smoke_dz
        masks.append(np.array([frustum(dx,dy,dz,candidate.heading+cam.yaw,cam.tilt,cam.hfov,cam.vfov)&los[i]&eligible for cam in candidate.cameras]))
    active=[i for i,c in enumerate(candidate.cameras) if c.active]
    def metrics(i,indices):
        return summarize(masks[i][indices],data['forest'],data['water'],eligible,cell*cell,priority)
    results={};images={}
    for i,name in enumerate(SCENARIOS):
        values,counts=metrics(i,active);results[name]=values
        rgba=np.zeros((*eligible.shape,4),dtype=np.uint8)
        forest=data['forest']>0
        for mask,color in [(eligible&forest&(counts==0),[202,104,80,150]),(eligible&forest&(counts==1),[48,177,105,195]),(eligible&forest&(counts>=2),[149,95,213,220]),(eligible&(data['water']>0)&(counts>0),[57,165,219,95])]:
            rgba[mask]=color
        imagefile=CACHE/(key+'_'+name+'.png')
        llbounds=write_overlay(rgba,localbounds,imagefile,cell)
        images[name]=dict(url='/results/'+imagefile.name,bounds=llbounds)
    pairs=[]
    for indices,label in [([0,1],'Sol + merkez'),([1,2],'Merkez + sağ'),([0,2],'Sol + sağ')]:
        pairs.append(dict(pair=indices,label=label,**{name:metrics(i,indices)[0] for i,name in enumerate(SCENARIOS)}))
    sensitivity=[]
    for delta in [-20,-10,0,10,20]:
        cs=[frustum(dx,dy,smoke_dz,candidate.heading+delta+candidate.cameras[i].yaw,candidate.cameras[i].tilt,candidate.cameras[i].hfov,candidate.cameras[i].vfov)&los[3]&eligible for i in active]
        values,_=summarize(cs,data['forest'],data['water'],eligible,cell*cell,priority)
        sensitivity.append(dict(drift=delta,heading=(candidate.heading+delta)%360,**values))
    clipped=bool(min(x-bounds[0],bounds[2]-x,y-bounds[1],bounds[3]-y)<candidate.max_range)
    unknown=round(float(np.sum(data['forest']*eligible*~data['valid'])*cell*cell/10000),3)
    notes=[f"NLS 10 m (2019 arşivi), Syke CORINE 2024 (20 m). {meta['canopy_name']}.",
           f"Eksik orman taç verisi: %{meta['assumed_canopy_forest_pct']}; bu hücrelerde 20 m kapalı taç varsayımı.",
           'Taç örtüsü >0 olan hücreler opak kabul edilir. Ortalama boy, tekil ağaç tepesi değildir; saydamlık modellenmez.',
           'Bina yükseklikleri dahil.' if meta['buildings_included'] else 'Bina yükseklikleri yok; binaların perdelemesi eksik. Yapılaşma yalnız haritada gösterilir.',
           f'{cell} m hesap ızgarası; arazi/engel yüksekliği hücredeki maksimum, hedef alanı 20 m orman oranıyla ağırlıklı.',
           'Dünya eğriliği dahil; atmosferik kırılma, pus, rüzgâr ve optik algılama modellenmez.',
           'Hedef, taç yüzeyinin üzerinde seçilen yükseklikte tek bir geometrik noktadır; duman yayılım modeli değildir.']
    if clipped:notes.append('Menzil veri sınırını aşıyor; alanlar yalnız hazırlanan bölgenin içindedir.')
    if unknown:notes.append(f'Yükselti verisi eksik {unknown} ha orman kör alana dahil edildi; görüşü doğrulanamadı.')
    result=dict(id=key,input=candidate.model_dump(),resolution_m=cell,observer_elevation_m=round(observer_z,2),
        active_cameras=active,mode='üç kamera, referans' if candidate.reference else 'iki girişli modül',
        metrics=results,pair_comparison=pairs,reference=dict(label='üç kamera, referans',metrics={name:metrics(i,[0,1,2])[0] for i,name in enumerate(SCENARIOS)}),
        heading_sensitivity=sensitivity,images=images,
        sectors=[dict(active=c.active,label=['Sol','Merkez','Sağ'][i]+('' if c.active else ' · bağlı değil'),points=sector(candidate,c,x,y)) for i,c in enumerate(candidate.cameras)],
        uncertainty=notes,range_clipped=clipped,unknown_forest_ha=unknown,
        field_checks=dict(road_access='sahada doğrulanacak',shadow='sahada doğrulanacak',site_constraints='sahada doğrulanacak'),
        computed_seconds=round(time.perf_counter()-started,4),cached=False,data_prepared_at=meta['prepared_at'],algorithm=ALGORITHM)
    tmp=resultfile.with_suffix('.tmp');tmp.write_text(json.dumps(result,ensure_ascii=False));tmp.replace(resultfile)
    result['request_seconds']=round(time.perf_counter()-started,4)
    return result
