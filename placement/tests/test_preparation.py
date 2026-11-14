"""Exercise the real preparation publisher without downloads or raster rebuilds."""
import copy
import json
import runpy
import ssl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def preparation(tmp_path):
    module = runpy.run_path(str(ROOT / 'scripts/prepare_data.py'))
    writer = module['write_metadata']
    writer.__globals__['PREP'] = tmp_path
    return module, writer


def test_preparation_keeps_tls_chain_and_hostname_verification(tmp_path):
    module, _ = preparation(tmp_path)
    assert module['TLS'].verify_mode == ssl.CERT_REQUIRED
    assert module['TLS'].check_hostname
    if module['CA_BUNDLE']:
        assert Path(module['CA_BUNDLE']).is_file()
        assert module['CURL_CA']['CURL_CA_BUNDLE'] == module['CA_BUNDLE']


def test_identical_release_metadata_is_reproducible_while_run_times_survive(tmp_path):
    module, write = preparation(tmp_path)
    release = module['RELEASE']
    template = {'prepared_at': '2026-11-14T01:00:00+00:00', 'files': copy.deepcopy(release['files']),
                'sources': [{'name': 'source', 'accessed': '2026-11-14'}],
                'canopy_name': 'English description of the published canopy'}
    write(copy.deepcopy(template))
    first = (tmp_path / 'metadata.json').read_bytes()
    published = json.loads(first)
    assert published['prepared_at'] == release['prepared_at']
    assert published['sources'][0]['accessed'] == release['accessed']
    run = json.loads((tmp_path / 'preparation-run.json').read_text())
    assert run['prepared_at'] == template['prepared_at']
    assert run['accessed'] == ['2026-11-14']
    assert run['reproduced_release'] is True
    template['canopy_name'] = 'Updated UI translation of the same canopy'
    template['prepared_at'] = '2026-11-15T02:00:00+00:00'
    template['sources'][0]['accessed'] = '2026-11-15'
    write(copy.deepcopy(template))
    assert (tmp_path / 'metadata.json').read_bytes() == first
    assert json.loads((tmp_path / 'preparation-run.json').read_text())['prepared_at'] == template['prepared_at']


def test_different_numeric_release_retains_its_own_dates(tmp_path):
    _, write = preparation(tmp_path)
    metadata = {'prepared_at': '2026-11-14T01:00:00+00:00', 'files': {'detailed.npz': 'changed'},
                'sources': [{'name': 'source', 'accessed': '2026-11-14'}]}
    write(copy.deepcopy(metadata))
    assert json.loads((tmp_path / 'metadata.json').read_text()) == metadata
    assert json.loads((tmp_path / 'preparation-run.json').read_text())['reproduced_release'] is False
