from dataclasses import replace
import pytest
from station.config import load_config
from conftest import ROOT


def test_default_two_inputs():
    config=load_config(ROOT/'config.toml')
    assert [c.name for c in config.cameras if c.active]==['left','centre']
    assert [c.yaw for c in config.cameras]==[-70,0,70]


def test_max_two_active(config):
    with pytest.raises(ValueError,match='At most two'):
        replace(config,cameras=[replace(c,active=True) for c in config.cameras])

@pytest.mark.parametrize('pair',[('left','right'),('centre','right'),('left','centre')])
def test_any_pair_allowed(config,pair):
    cfg=replace(config,cameras=[replace(c,active=c.name in pair) for c in config.cameras])
    assert sum(c.active for c in cfg.cameras)==2


def test_usb_requires_persistent_identifier(config):
    with pytest.raises(ValueError,match='never an index'):
        replace(config,cameras=[replace(config.cameras[0],kind='usb',source='/dev/video0'),*config.cameras[1:]])
    replace(config,cameras=[replace(config.cameras[0],kind='usb',source='/dev/v4l/by-path/pci-usb-video-index0'),*config.cameras[1:]])


def test_three_named_slots_required(config):
    with pytest.raises(ValueError,match='exactly three'):
        replace(config,cameras=config.cameras[:2])

@pytest.mark.parametrize('field,value',[('analysis_hz',0),('confidence',0),('input_size',633),('retention_days',-1),('similarity_iou',2)])
def test_invalid_parameters(config,field,value):
    with pytest.raises(ValueError):replace(config,**{field:value})
