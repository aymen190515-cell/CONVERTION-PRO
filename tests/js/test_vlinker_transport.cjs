const assert = require('node:assert/strict');
const {AdapterSerialTransport, ClusterDriver} = require('../../src/convertion_pro/ui/vlinker_transport.js');
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));
function fixture(reply = 'ATI\r\nELM327 v2.3\r\n>') {
    let controller;
    const writes = [];
    const events = new EventTarget();
    const port = {
        readable: new ReadableStream({start(c) { controller = c; }}),
        writable: new WritableStream({write(bytes) {
            const text = new TextDecoder().decode(bytes);
            writes.push(text);
            if (reply instanceof Error) throw reply;
            const chunks = typeof reply === 'function' ? reply(text) : [reply];
            for (const chunk of chunks) if (chunk) controller.enqueue(new TextEncoder().encode(chunk));
        }}),
        async open(options) { this.options = options; },
        async close() { this.closed = true; }
    };
    events.requestPort = async () => port;
    const transport = new AdapterSerialTransport({serial: events, timeoutMs: 30});
    return {transport, port, writes, events, end: () => controller.close(), fail: () => controller.error(new Error('USB lost'))};
}
(async () => {
    for (const chunks of [
        ['ATI\r\nELM327 v2.3\r\n>'],
        ['>', 'AT', 'I\r', '\nEL', 'M327 v2.3', '\r\n', '>', '\r\n>'],
        ['vLinker FS USB\r>'],
        [...'ATI\rELM327 v2.3\r>']
    ]) {
        const f = fixture(() => chunks);
        await f.transport.connect();
        assert.equal(f.transport.state, 'CONNECTED');
        assert.deepEqual(f.writes, ['ATI\r']);
        assert.equal(f.port.options.baudRate, 115200);
        for (const forbidden of ['0100', 'ATSP0', 'ATSH123', 'ATZ', 'ATI\r0100']) {
            await assert.rejects(f.transport.command(forbidden), /hors liste/);
        }
        assert.deepEqual(f.writes, ['ATI\r']);
        await f.transport.disconnect();
        assert.equal(f.transport.state, 'DISCONNECTED');
        assert.equal(f.port.closed, true);
        const log = JSON.parse(f.transport.exportLog());
        assert.equal(log.cluster_identified, false);
        assert.equal(log.eeprom_read_available, false);
        assert(log.events.some(event => event.direction === 'RX'));
        assert(log.events.some(event => event.direction === 'TX'));
    }
    for (const reply of ['', 'ELM327 v2.3\r', 'ATI\r>', '?\r>', 'ERROR\r>', 'random device\r>', new Error('Write failed'), 'X'.repeat(8193)]) {
        const f = fixture(reply);
        await assert.rejects(f.transport.connect());
        await pause(5);
        assert.equal(f.transport.state, 'DISCONNECTED');
        assert.equal(f.port.closed, true);
        assert.equal(f.transport.pending, null);
    }
    const opening = fixture();
    opening.port.open = async () => { throw new Error('Port occupied'); };
    await assert.rejects(opening.transport.connect(), /occupied/);
    assert.equal(opening.transport.state, 'DISCONNECTED');
    const unplug = fixture('');
    const connecting = assert.rejects(unplug.transport.connect(), /Flux série fermé/);
    await pause(1);
    unplug.end();
    await connecting;
    assert.equal(unplug.transport.state, 'DISCONNECTED');
    const voltage = fixture(command => command === 'ATI\r' ? ['ELM327 v2.3\r>'] : ['AT RV\r', '12.', '4V\r', '>']);
    await voltage.transport.connect();
    assert.equal(await voltage.transport.voltage(), '12.4V');
    assert.deepEqual(voltage.writes, ['ATI\r', 'ATRV\r']);
    await voltage.transport.disconnect();
    for (const chunks of [['ATRV\r--.-V\r>'], ['AT RV\r', '--', '.', '-', 'V\r', '>']]) {
        const unavailable = fixture(command => command === 'ATI\r'
            ? ['ELM327 v2.3\r>'] : chunks);
        await unavailable.transport.connect();
        for (let attempt = 0; attempt < 2; attempt++) {
            assert.equal(await unavailable.transport.voltage(), null);
            assert.equal(unavailable.transport.state, 'CONNECTED');
            assert.equal(unavailable.transport.identity, 'ELM327 v2.3');
        }
        const log = JSON.parse(unavailable.transport.exportLog());
        assert(log.events.filter(event => event.direction === 'RX')
            .map(event => event.text).join('').includes('--.-V'));
        assert.equal(log.cluster_identified, false);
        assert.equal(log.eeprom_read_available, false);
        assert.equal(unavailable.port.closed, undefined);
        await unavailable.transport.disconnect();
    }
    for (const mode of ['eof', 'error', 'event', 'manual']) {
        const f = fixture(command => command === 'ATI\r' ? ['ELM327 v2.3\r>'] : []);
        await f.transport.connect();
        const read = f.transport.command('ATRV');
        const rejected = assert.rejects(read);
        await pause(1);
        if (mode === 'eof') f.end();
        if (mode === 'error') f.fail();
        if (mode === 'event') {
            const event = new Event('disconnect');
            event.port = f.port;
            f.events.dispatchEvent(event);
        }
        if (mode === 'manual') await f.transport.disconnect();
        await rejected;
        await pause(5);
        assert.equal(f.transport.state, 'DISCONNECTED');
        assert.equal(f.port.closed, true);
    }
    const pending = fixture(command => command === 'ATI\r' ? ['ELM327 v2.3\r>'] : []);
    await pending.transport.connect();
    const timed = assert.rejects(pending.transport.command('ATRV'), /Délai/);
    await assert.rejects(pending.transport.command('ATI'), /déjà en cours/);
    await timed;
    await pause(5);
    assert.equal(pending.transport.state, 'DISCONNECTED');
    const retry = fixture();
    await retry.transport.connect();
    await retry.transport.disconnect();
    // A fresh port/stream per reconnect, as Web Serial supplies on reopen.
    const next = fixture();
    retry.transport.serial = next.events;
    await retry.transport.connect();
    await retry.transport.disconnect();
    const cancel = new AdapterSerialTransport({serial: {requestPort: async () => { throw new Error('Selection cancelled'); }}});
    await assert.rejects(cancel.connect(), /cancelled/);
    assert.equal(cancel.state, 'DISCONNECTED');
    const driver = new ClusterDriver();
    assert.equal(driver.capability().clusterIdentified, false);
    assert.equal(driver.capability().eepromReadAvailable, false);
    await assert.rejects(driver.identify(), /non documenté/);
    await assert.rejects(driver.readEEPROM(), /non documenté/);
    console.log('Adapter synthetic scenarios passed');
})().catch(error => { console.error(error); process.exitCode = 1; });
