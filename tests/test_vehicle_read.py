import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from convertion_pro.core.cluster_read import VehicleReadService
from convertion_pro.core.vehicle_catalog import load_vehicle_catalog

ROOT = Path(__file__).resolve().parents[1]
KEY = 'jeep_wrangler_2012_2018'


def test_vehicle_simulation_uses_selected_profile_and_driver():
    service = VehicleReadService(load_vehicle_catalog())
    capabilities = service.capabilities(KEY)
    assert capabilities['simulation_available'] is True
    assert capabilities['hardware_read_available'] is False
    assert capabilities['cluster_identified'] is False
    result = service.read(KEY, 'SIMULATED')
    data = bytes.fromhex(result['data_hex'])
    assert len(data) == 1024
    assert data[0x68:0x6A] == b'\x04\x12'
    assert result['sha256'] == hashlib.sha256(data).hexdigest()
    assert result['vehicle_key'] == KEY
    assert result['driver_id'] == 'SYNTHETIC_JEEP_1024'
    assert result['source'] == 'SIMULATED'
    assert result['hardware_access'] is False


def test_vehicle_hardware_and_toyota_fail_before_any_driver(monkeypatch):
    from convertion_pro.core import cluster_read
    def forbidden(*args, **kwargs):
        raise AssertionError('No programmer or transport may be constructed')
    monkeypatch.setattr(cluster_read, 'SimulatedProgrammer', forbidden)
    service = VehicleReadService(load_vehicle_catalog())
    for make in service.catalog['makes']:
        for vehicle in make['vehicles']:
            with pytest.raises(ValueError):
                service.read(vehicle['key'], 'HARDWARE')
            if make['key'] == 'toyota':
                assert service.capabilities(vehicle['key'])['reason'] == 'RH850 DRIVER REQUIRED'
                with pytest.raises(ValueError, match='Aucun pilote de simulation'):
                    service.read(vehicle['key'], 'SIMULATED')
    for key in ('', 'unknown'):
        with pytest.raises(RuntimeError):
            service.read(key, 'SIMULATED')


def test_missing_cluster_profile_never_falls_back():
    catalog = load_vehicle_catalog()
    del catalog['makes'][0]['vehicles'][0]['cluster_profile']
    service = VehicleReadService(catalog)
    assert service.capabilities(KEY)['simulation_available'] is False
    with pytest.raises(ValueError, match='Aucun pilote de simulation'):
        service.read(KEY, 'SIMULATED')


def test_vehicle_read_api_requires_selection_and_explicit_simulation():
    spec = importlib.util.spec_from_file_location('vehicle_read_preview', ROOT / 'preview.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for key, mode, status in [('', 'SIMULATED', 422), ('unknown', 'SIMULATED', 422),
                              (KEY, 'HARDWARE', 501), ('toyota_tundra_gas', 'SIMULATED', 422)]:
        response = asyncio.run(module.advanced_read_memory(mode=mode, vehicle_key=key))
        assert response.status_code == status
        assert 'data_hex' not in json.loads(response.body)
    result = asyncio.run(module.advanced_read_memory(mode='SIMULATED', vehicle_key=KEY))
    assert result['vehicle_key'] == KEY


def test_selected_vehicle_read_to_download_preserves_synthetic_bytes():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js required for browser workflow test')
    source = (ROOT / 'preview.py').read_text()
    read = source.split('async function readMemory(mode = "HARDWARE"){', 1)[1].split(
        'function configureAdvancedVehicleConversion()', 1)[0]
    save = source.split('function saveActiveMemoryFile(){', 1)[1].split(
        'document.addEventListener(', 1)[0]
    result = VehicleReadService(load_vehicle_catalog()).read(KEY, 'SIMULATED')
    script = '''
const assert = require('node:assert/strict');
const payload = PAYLOAD;
let vehicleContext = {key: payload.vehicle_key};
let selectedVehicle = vehicleContext;
let workspaceMode = 'VEHICLE_ADVANCED';
let currentMemoryBytes = [], currentMemoryFilename;
let downloaded, blob;
const elements = {};
const element = () => ({style: {}, textContent: '', classList: {remove(){}, add(){}}});
const document = {
    getElementById: id => elements[id] ||= element(),
    createElement: () => ({click(){downloaded = this.download;}, remove(){}}),
    body: {appendChild(){}}
};
const URL = {createObjectURL(value){blob = value; return 'synthetic-url';}, revokeObjectURL(){}};
const show = () => {};
const alert = () => {throw new Error('Unexpected alert');};
let requests = 0;
const fetch = async url => {
    requests++;
    assert(url.includes('vehicle_key=' + payload.vehicle_key));
    assert(url.includes('mode=SIMULATED'));
    return {ok: true, json: async () => payload};
};
const populateMemoryWorkspace = data => {
    assert.equal(data.source, 'SIMULATED');
    currentMemoryBytes = data.bytes;
    currentMemoryFilename = data.filename;
};
async function readMemory(mode = "HARDWARE"){ READ
function saveActiveMemoryFile(){ SAVE
(async () => {
    await readMemory('SIMULATED');
    saveActiveMemoryFile();
    assert.equal(downloaded, payload.filename);
    assert.deepEqual(Buffer.from(await blob.arrayBuffer()), Buffer.from(payload.data_hex, 'hex'));
    vehicleContext = null;
    await readMemory('SIMULATED');
    assert.equal(requests, 1);
    assert(elements.memoryError.textContent.includes('aucun repli'));
})().catch(error => {console.error(error); process.exitCode = 1;});
'''.replace('PAYLOAD', json.dumps(result)).replace('READ', read).replace('SAVE', save)
    response = subprocess.run([node, '-e', script], capture_output=True, text=True, timeout=10)
    assert response.returncode == 0, response.stdout + response.stderr


def test_memory_workspace_electrical_values_are_bound_to_source():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node.js required for browser rendering test')
    source = (ROOT / 'preview.py').read_text()
    function = source.split('function populateMemoryWorkspace({', 1)[1].split(
        'async function openAdvancedMemoryFile(file)', 1)[0]
    script = '''
const assert = require('node:assert/strict');
let currentMemoryBytes, originalMemoryBytes, modifiedMemoryOffsets,
    currentMemoryAnnotations, currentMemorySource, currentMemoryFilename,
    currentMemorySha256, currentMemoryType;
const elements = {};
const document = {getElementById: id => elements[id] ||= {textContent: ''}};
const updateMemoryModifiedState = () => {};
const renderHexViewer = () => {};
const configureAdvancedVehicleConversion = () => {};
function populateMemoryWorkspace({ FUNCTION
const input = {bytes: [255], filename: 'synthetic.bin', memoryType: 'EEPROM',
    sha256: 'test-only', voltage: 12.4, current: 0.42};
populateMemoryWorkspace({...input, source: 'SIMULATED'});
assert.equal(elements.memoryVoltage.textContent,
    '12.4 V · SIMULATED — NO HARDWARE VALIDATION');
assert.equal(elements.memoryCurrent.textContent,
    '0.42 A · SIMULATED — NO HARDWARE VALIDATION');
assert(!elements.memoryCurrent.textContent.includes('MONITORING'));
assert.equal(elements.memoryModeBadge.textContent, 'SIMULATED — NO HARDWARE ACCESSED');
// A FILE must ignore telemetry even if supplied, including values from an earlier demo.
for (const telemetry of [{voltage: 12.4, current: 0.42}, {voltage: null, current: null}]) {
    populateMemoryWorkspace({...input, ...telemetry, source: 'FILE'});
    for (const id of ['memoryVoltage', 'memoryCurrent']) {
        assert.equal(elements[id].textContent, 'N/A · FILE — NO PHYSICAL MEASUREMENT');
    }
    assert.equal(elements.memoryModeBadge.textContent, 'FILE — NOT A LIVE HARDWARE READ');
}
populateMemoryWorkspace({...input, source: 'UNKNOWN'});
assert.equal(elements.memoryVoltage.textContent, 'N/A · UNVERIFIED SOURCE');
assert.equal(elements.memoryCurrent.textContent, 'N/A · UNVERIFIED SOURCE');
'''.replace('FUNCTION', function)
    response = subprocess.run([node, '-e', script], capture_output=True, text=True, timeout=10)
    assert response.returncode == 0, response.stdout + response.stderr
