import numpy as np
import pytest
from pydantic import ValidationError
from forest_placement.core import sightlines,frustum,summarize,rank_candidates
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

@pytest.mark.parametrize('dx,dy,dz,heading,tilt,hfov,vfov,answer',[
    (0,100,0,0,0,80,50,True),(100,0,0,0,0,80,50,False),
    (0,-100,0,0,0,160,160,False),(100,0,0,90,0,80,50,True),
    (100,100,0,0,0,90,50,True),(101,100,0,0,0,90,50,False),
    (0,100,-100,0,45,80,10,True),(0,100,-100,0,0,80,50,False),
    (-1,100,0,359,0,20,50,True),
])
def test_frustum(dx,dy,dz,heading,tilt,hfov,vfov,answer):
    assert bool(frustum(np.array(dx),np.array(dy),np.array(dz),heading,tilt,hfov,vfov))==answer

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

def test_inactive_camera_has_no_influence():
    forest=np.ones((1,3));water=np.zeros((1,3));m=np.array([[[1,0,0]],[[0,1,0]],[[0,0,1]]],bool)
    active,_=summarize(m[:2],forest,water,np.ones((1,3),bool),10000)
    reference,_=summarize(m,forest,water,np.ones((1,3),bool),10000)
    assert active['visible_forest_ha']==2
    assert active['blind_forest_ha']==1
    assert reference['visible_forest_ha']==3

def test_no_active_cameras():
    f=np.ones((2,2));m,_=summarize([],f,np.zeros_like(f),np.ones_like(f,bool),10000)
    assert m['visible_forest_ha']==0 and m['blind_forest_ha']==4

def test_priority_mask_counts_only_visible_forest_and_ranks_first():
    forest=np.array([[1,1,0]],float);water=1-forest;priority=np.array([[True,False,True]])
    one,_=summarize(np.array([[[1,0,1]]],bool),forest,water,np.ones_like(priority),10000,priority)
    two,_=summarize(np.array([[[0,1,1]]],bool),forest,water,np.ones_like(priority),10000,priority)
    assert one['priority_visible_ha']==1 and two['priority_visible_ha']==0
    two['visible_forest_ha']=100
    assert rank_candidates([two,one])[0] is one

def test_default_pair_and_max_two_active():
    c=PRESETS[0]
    assert [x.active for x in c.cameras]==[True,True,False]
    data=c.model_dump();data['cameras'][2]['active']=True
    with pytest.raises(ValidationError,match='At most two'):Candidate(**data)
    data['reference']=True
    assert sum(x.active for x in Candidate(**data).cameras)==3

@pytest.mark.parametrize('camera',[dict(hfov=0),dict(vfov=180),dict(tilt=95),dict(yaw=181)])
def test_camera_bounds(camera):
    with pytest.raises(ValidationError):Camera(**camera)

def test_pair_frusta_default_gap_and_neighbour_overlap():
    angle=np.radians(np.linspace(-180,180,3601))
    dx,dy=1000*np.sin(angle),1000*np.cos(angle)
    masks=[frustum(dx,dy,np.full_like(dx,-100),yaw,10,80,50) for yaw in [-70,0,70]]
    assert (masks[0]&masks[1]).any() and (masks[1]&masks[2]).any()
    assert not (masks[0]&masks[2]).any()
    assert not (masks[0]|masks[2])[1800] # central direction is in the gap

def test_self_intersecting_priority_rejected():
    data=PRESETS[0].model_dump();data['priority']=[[24.5,60.1],[24.7,60.3],[24.5,60.3],[24.7,60.1]]
    with pytest.raises(ValidationError):Candidate(**data)
