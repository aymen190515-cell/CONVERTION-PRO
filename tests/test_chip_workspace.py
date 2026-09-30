from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from zipfile import ZipFile
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from convertion_pro.core import chip_workspace as core
from convertion_pro.ui import chip_api
from convertion_pro.hardware.memory_access import (
    CapabilityRegistry, M24C32, MemoryAccessError, MemoryReader, ReadEffect, Support, REGISTRY,
)


def test_import_provenance_cannot_be_promoted_by_filename_or_profile():
    work = core.Workspace()
    meta = work.import_file(b'\xff'*4096, 'ST_M24C32', '../../HARDWARE-verified.bin')
    assert meta['source'] == 'FILE'
    assert meta['name'] == 'HARDWARE-verified.bin'
    assert not meta['chip_identity_verified'] and not meta['hardware_access']
    assert meta['sha256'] == sha256(b'\xff'*4096).hexdigest()


def test_backup_round_trip_preserves_full_data_and_provenance():
    work = core.Workspace()
    meta = work.simulate('ST_M24C32')
    assert work.inspect(meta['id'])['preview_bytes'] == 256
    blob = work.export_backup(meta['id'])
    with ZipFile(BytesIO(blob)) as archive:
        assert set(archive.namelist()) == {'memory.bin', 'manifest.json'}
        data = archive.read('memory.bin')
        manifest = json.loads(archive.read('manifest.json'))
    assert len(data) == 4096
    assert sha256(data).hexdigest() == manifest['sha256']
    assert manifest['source'] == 'SIMULATED'
    assert manifest['audit'][-1]['event'] == 'EXPORT_PREPARED'
    assert work.compare(meta['id'], data)['identical'] is True
    assert work.compare(meta['id'], data)['hardware_verified'] is False


def test_comparison_reports_changed_missing_and_extra_bytes_without_mutation():
    work = core.Workspace()
    meta = work.import_file(b'\x00\x01\x02')
    result = work.compare(meta['id'], b'\x00\x08\x02\xff')
    assert result['changed_byte_count'] == 2
    assert result['first_differences'] == [
        {'offset':1,'reference':1,'candidate':8},
        {'offset':3,'reference':None,'candidate':255},
    ]
    assert work.compare(meta['id'], b'\x00')['changed_byte_count'] == 2
    assert work.inspect(meta['id'])['sha256'] == meta['sha256']


def test_large_diff_is_bounded_and_session_close_removes_only_memory():
    work = core.Workspace()
    meta = work.import_file(b'\x00'*100)
    result = work.compare(meta['id'], b'\xff'*100)
    assert result['changed_byte_count'] == 100
    assert len(result['first_differences']) == 64 and result['differences_truncated']
    assert work.close(meta['id'])['scope'] == 'IN_MEMORY_SESSION_ONLY'
    with pytest.raises(ValueError, match='inconnue'):
        work.inspect(meta['id'])


@pytest.mark.parametrize('data,profile', [(b'', 'RAW_FILE'),(b'abc','ST_M24C32'),(b'x','Lexus')])
def test_preflight_rejects_invalid_image(data, profile):
    with pytest.raises(ValueError):
        core.Workspace().import_file(data, profile)


def test_session_and_byte_budgets(monkeypatch):
    monkeypatch.setattr(core, 'MAX_STORED_BYTES', 4)
    work = core.Workspace()
    work.import_file(b'1234')
    with pytest.raises(ValueError, match='plein'):
        work.import_file(b'5')
    monkeypatch.setattr(core, 'MAX_SESSIONS', 1)
    work = core.Workspace()
    meta = work.import_file(b'1')
    with pytest.raises(ValueError, match='plein'):
        work.import_file(b'2')
    work.close(meta['id'])
    work.import_file(b'3')


@pytest.mark.parametrize('effect', [ReadEffect.UNKNOWN, ReadEffect.MAY_ERASE_OR_WRITE])
def test_even_a_validated_read_mode_is_blocked_if_it_may_erase(effect):
    entry = replace(M24C32, status=Support.VALIDATED, read_effect=effect,
                    validation_record='TEST ONLY')
    registry = CapabilityRegistry((entry,))
    with pytest.raises(MemoryAccessError, match='erase/write'):
        # Rejected before touching even a transport attribute or driver.
        MemoryReader(registry).read(M24C32.key, 'EEPROM', None, None,
                                    confirmed_preconditions=M24C32.preconditions)


def test_missing_preconditions_block_before_transport():
    entry = replace(M24C32, status=Support.VALIDATED, validation_record='TEST ONLY')
    with pytest.raises(MemoryAccessError, match='preconditions'):
        MemoryReader(CapabilityRegistry((entry,))).read(M24C32.key, 'EEPROM', None, None)


@pytest.mark.parametrize('changes', [{'mode':'BOOT'}, {'package':'UNVERIFIED_SO8'}, {'mask':'OTHER_MASK'}])
def test_support_never_leaks_between_modes_packages_or_masks(changes):
    assert REGISTRY.lookup(replace(M24C32.key, **changes)).status == Support.UNSUPPORTED


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(chip_api, 'workspace', core.Workspace())
    app = FastAPI()
    app.include_router(chip_api.router)
    with TestClient(app, base_url='http://127.0.0.1', client=('127.0.0.1', 50000)) as client:
        client.headers['X-Chip-Workspace'] = '1'
        client.get('/chips')
        yield client


def test_complete_file_api_and_backup(client):
    assert client.get('/chips').status_code == 200
    catalog = client.get('/api/chips/catalog').json()
    assert not catalog['hardware_execution_enabled']
    assert catalog['profiles'][0]['capability']['status'] == 'DOCUMENTED_UNVALIDATED'
    response = client.post('/api/chips/import?name=a.bin', content=b'abc')
    assert response.status_code == 200
    session = response.json()['id']
    assert client.get('/api/chips/sessions/'+session).json()['source'] == 'FILE'
    backup = client.get('/api/chips/sessions/'+session+'/backup')
    assert backup.status_code == 200 and backup.headers['content-type'] == 'application/zip'
    with ZipFile(BytesIO(backup.content)) as archive:
        assert archive.read('memory.bin') == b'abc'
    result = client.post('/api/chips/sessions/'+session+'/compare', content=b'abc').json()
    assert result['identical'] and not result['hardware_verified']
    assert client.delete('/api/chips/sessions/'+session).json()['closed']


def test_simulation_is_explicit_and_hardware_cannot_fall_back(client):
    response = client.post('/api/chips/simulate', json={'profile':'ST_M24C32'})
    assert response.json()['source'] == 'SIMULATED'
    response = client.post('/api/chips/hardware/read', json={'chip':'24C32','port':'COM3'})
    assert response.status_code == 501
    assert 'data' not in response.json() and 'data_hex' not in response.json()
    for operation in ('write', 'erase', 'unlock'):
        assert client.post('/api/chips/hardware/'+operation).status_code == 404


def test_remote_and_cross_origin_requests_are_rejected(client):
    assert client.get('/api/chips/catalog', headers={'host':'attacker.example'}).status_code == 403
    assert client.post('/api/chips/import', content=b'a', headers={'origin':'https://attacker.example'}).status_code == 403
    assert client.get('/api/chips/catalog', headers={'sec-fetch-site':'cross-site'}).status_code == 403


def test_streaming_body_limit_and_invalid_session(client, monkeypatch):
    monkeypatch.setattr(chip_api, 'MAX_BYTES', 3)
    assert client.post('/api/chips/import', content=b'1234').status_code == 413
    assert client.get('/api/chips/sessions/not-a-session').status_code == 404
    assert client.post('/api/chips/import?profile=ST_M24C32', content=b'a').status_code == 422
