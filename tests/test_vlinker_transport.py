from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_adapter_transport_synthetic_scenarios():
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node.js required for Web Serial synthetic tests')
    result = subprocess.run(
        [node, str(ROOT / 'tests/js/test_vlinker_transport.cjs')],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'Adapter synthetic scenarios passed' in result.stdout


def test_preview_includes_adapter_transport_and_separate_states():
    import importlib.util
    spec = importlib.util.spec_from_file_location('vlinker_preview_test', ROOT / 'preview.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    import asyncio
    response = asyncio.run(module.preview())
    html = response.body.decode()
    assert '__VLINKER_TRANSPORT_JS__' not in html
    assert 'class AdapterSerialTransport' in html
    assert 'Cluster identifié : NON' in html
    assert 'Lecture EEPROM disponible : NON' in html
    assert 'cpClusterDriver.capability().reason' in html
    assert html.count('navigator.serial.requestPort') == 0
    assert 'this.serial.requestPort()' in html


def test_unavailable_voltage_interface_preserves_adapter_state():
    node = shutil.which('node')
    if node is None:
        pytest.skip('Node.js required for interface test')
    source = (ROOT / 'preview.py').read_text()
    function = source.split('async function cpVLinkerVoltage() {', 1)[1].split(
        'function cpExportVLinkerLog()', 1
    )[0]
    script = '''
const assert = require('node:assert/strict');
const elements = {
    'cp-vlinker-voltage': {disabled: false},
    'cp-vlinker-measurement': {textContent: ''}
};
const document = {getElementById: id => elements[id]};
const cpAdapter = {
    state: 'CONNECTED',
    voltage: async () => null,
    record: () => {throw new Error('Unavailable voltage is not an error');}
};
async function cpVLinkerVoltage() { FUNCTION
cpVLinkerVoltage().then(() => {
    assert.equal(elements['cp-vlinker-measurement'].textContent,
        'Tension indisponible ; aucune validation de l’alimentation du cluster.');
    assert.equal(elements['cp-vlinker-voltage'].disabled, false);
    assert.equal(cpAdapter.state, 'CONNECTED');
}).catch(error => {console.error(error); process.exitCode = 1;});
'''.replace('FUNCTION', function)
    result = subprocess.run([node, '-e', script], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr
