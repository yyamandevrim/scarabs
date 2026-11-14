"""The copyable laptop recipe must run without hardware and reach local ground."""
from station.config import load_config
from pathlib import Path


def test_laptop_demo_uses_portable_recordings_without_a_simulated_mcu():
    root = Path(__file__).resolve().parents[1]
    config = load_config(root / 'demo-laptop.toml')
    assert config.mcu.mode == 'off'
    active = [c for c in config.cameras if c.active]
    assert len(active) == 2 and all(c.kind == 'file' for c in active)
    assert {Path(c.source).name for c in active} == {'smoke.ogv', 'cloud.webm'}
    assert all(Path(c.source).is_relative_to(root / 'media') for c in config.cameras)
    assert config.lora.enabled and config.lora.transport == 'simulated'
    assert (config.lora.peer_host, config.lora.peer_port) == ('127.0.0.1', 49173)
    assert config.lora.sf == 7 and config.lora.duty_fraction == .01
    assert config.data_dir == root / 'data/laptop'
