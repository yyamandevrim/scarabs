import numpy as np
import pytest
from pydantic import ValidationError
from forest_placement.core import sightlines,camera_sector,footprint_radii,summarize,rank_candidates
from forest_placement.models import Camera,Candidate,PRESETS

def rays(terrain,observer=10,cell=10,smoke=50,radius=6371000,surface=None,valid=None):
    if surface is None:surface=terrain.copy()
    if valid is None:valid=np.ones_like(terrain,dtype=bool)
    return sightlines(terrain.astype('float32'),surface.astype('float32'),valid,.5,.5,observer,cell,1e6,smoke,radius)

def test_flat_plane_visible():
    a=np.zeros((7,100));m=rays(a,observer=100)
    assert m[0,0,1:].all()
    assert m[2,0,1:].all()
    assert m[3,0,1:].all()

def test_single_ridge_blocks_ground_behind_but_tall_smoke_clears_it():
    a=np.zeros((3,30));a[:,10]=100
    m=rays(a,observer=10,smoke=400)
    assert m[0,0,9]
    assert m[0,0,10]
    assert not m[0,0,20]
    assert m[3,0,20]

def test_canopy_blocks_floor_and_nearby_ground():
    ground=np.zeros((3,30));surface=ground.copy();surface[:,10]=30
    m=rays(ground,observer=10,surface=surface)
    assert m[0,0,10] and m[0,0,20]
    assert not m[2,0,10] and not m[2,0,20]
    assert m[3,0,10]

def test_curvature_hides_beyond_horizon():
    a=np.zeros((1,501))
    curved=rays(a,observer=20,cell=100)
    flat=rays(a,observer=20,cell=100,radius=1e30)
    assert curved[0,0,100] # 10km before ~16km horizon
    assert not curved[0,0,400] # 40km beyond horizon
    assert flat[0,0,400]

def test_unknown_obstruction_invalidates_ray():
    a=np.zeros((1,30));v=np.ones(a.shape,dtype=bool);v[:,10]=False
    m=rays(a,valid=v)
    assert not m[:,0,20].any()
    assert m[0,0,9]

@pytest.mark.parametrize('heading',[0,20,60,120,180,359.99])
def test_sectors_tile_full_ring_without_overlap(heading):
    angles=np.radians(np.arange(0,360,.1))
    dx,dy=1000*np.sin(angles),1000*np.cos(angles)
    masks=np.array([camera_sector(dx,dy,np.full_like(dx,-100),heading+yaw,10,120,50) for yaw in (0,120,240)])
    assert np.all(masks.sum(axis=0)==1)
    assert masks.sum()==len(angles)


def test_vertical_geometry_and_inner_disc():
    distance=np.array([10,100,1000,12000])
    mask=camera_sector(np.zeros(4),distance,np.full(4,-600),0,10,120,50)
    assert mask.tolist()==[False,False,True,True]
    spans=footprint_radii(-600,10,50,12000,6371000)
    assert len(spans)==1
    inner,outer=spans[0]
    assert inner==pytest.approx(600/np.tan(np.radians(35)),rel=.001)
    assert outer==12000
    # A steeper tilt produces a real outer vertical limit before maximum range.
    inner,outer=footprint_radii(-600,45,20,12000,6371000)[0]
    assert inner<outer<1000

def test_unique_forest_overlap_and_water_exclusion():
    forest=np.array([[1,.5,0,1]],dtype=float);water=np.array([[0,.5,1,0]],dtype=float)
    masks=np.array([[[1,1,1,0]],[[1,0,1,0]]],dtype=bool)
    result,counts=summarize(masks,forest,water,np.ones(forest.shape,dtype=bool),10000)
    assert result['visible_forest_ha']==1.5
    assert result['blind_forest_ha']==1
    assert result['overlap_forest_ha']==1
    assert result['water_view_ha']==1.5
    assert result['total_forest_ha']==2.5
    assert counts.tolist()==[[2,1,2,0]]

def test_priority_mask_counts_only_visible_forest_and_ranks_first():
    forest=np.array([[1,1,0]],float);water=1-forest;priority=np.array([[True,False,True]])
    one,_=summarize(np.array([[[1,0,1]]],bool),forest,water,np.ones_like(priority),10000,priority)
    two,_=summarize(np.array([[[0,1,1]]],bool),forest,water,np.ones_like(priority),10000,priority)
    assert one['priority_visible_ha']==1 and two['priority_visible_ha']==0
    two['visible_forest_ha']=100
    assert rank_candidates([two,one])[0] is one

def test_default_three_camera_configuration_and_reject_old_modes():
    c=PRESETS[0]
    assert [x.active for x in c.cameras]==[True]*3
    assert [x.yaw for x in c.cameras]==[0,120,240]
    assert [x.hfov for x in c.cameras]==[120]*3
    for key,value in [('active',False),('yaw',70),('hfov',80)]:
        data=c.model_dump();data['cameras'][2][key]=value
        with pytest.raises(ValidationError,match='Three active'):Candidate(**data)
    with pytest.raises(ValidationError):Candidate(**c.model_dump(),reference=True)
    data=c.model_dump();data['cameras'][2]['tilt']=20
    with pytest.raises(ValidationError,match='vertical geometry'):Candidate(**data)

@pytest.mark.parametrize('camera',[dict(hfov=0),dict(vfov=180),dict(tilt=95),dict(yaw=361)])
def test_camera_bounds(camera):
    with pytest.raises(ValidationError):Camera(**camera)

def test_self_intersecting_priority_rejected():
    data=PRESETS[0].model_dump();data['priority']=[[24.5,60.1],[24.7,60.3],[24.5,60.3],[24.7,60.1]]
    with pytest.raises(ValidationError):Candidate(**data)
