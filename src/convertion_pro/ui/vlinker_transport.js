/* Adapter-only ELM commands. No CAN/OBD payload, probing or cluster access.
 * ATI and ATRV: ELM327 datasheet, AT command descriptions.
 */
class AdapterSerialTransport {
    constructor({serial, timeoutMs = 3000, onState = () => {}} = {}) {
        this.serial = serial;
        this.timeoutMs = timeoutMs;
        this.onState = onState;
        this.log = [];
        this.state = 'DISCONNECTED';
        this.identity = null;
        this.buffer = '';
        this.pending = null;
        this.closing = null;
    }
    record(direction, text) {
        this.log.push({at: new Date().toISOString(), direction, text});
        if (this.log.length > 2000) this.log.shift();
    }
    setState(state, detail = '') {
        this.state = state;
        this.record('STATE', state + (detail ? ': ' + detail : ''));
        this.onState({state, detail, identity: this.identity});
    }
    async connect(baudRate = 115200) {
        if (this.state !== 'DISCONNECTED' || this.closing) throw new Error('Connexion déjà active');
        if (!this.serial) throw new Error('Web Serial nécessite Chrome/Edge et une page sécurisée');
        if (![9600, 38400, 115200].includes(baudRate)) throw new Error('Débit série invalide');
        this.identity = null;
        this.buffer = '';
        this.setState('OPENING');
        try {
            this.port = await this.serial.requestPort();
            await this.port.open({baudRate});
            this.record('INFO', 'Débit série PC: ' + baudRate + ' (aucun débit CAN configuré)');
            this.reader = this.port.readable.getReader();
            this.writer = this.port.writable.getWriter();
            this.disconnectListener = event => {
                if (event.target === this.port || event.port === this.port) {
                    void this.disconnect('Adaptateur USB débranché');
                }
            };
            this.serial.addEventListener('disconnect', this.disconnectListener);
            this.setState('IDENTIFYING');
            this.readTask = this.readLoop();
            const identity = await this.command('ATI');
            if (!/^(?:ELM327\b|vLinker\b)/i.test(identity)) {
                throw new Error('Identité ELM/vLinker non reconnue: ' + identity);
            }
            if (this.closing || this.state !== 'IDENTIFYING') throw new Error('Connexion interrompue');
            this.identity = identity;
            this.setState('CONNECTED', 'Identité déclarée par ATI ; modèle FS non authentifié');
            return identity;
        } catch (error) {
            await this.disconnect(error.message);
            throw error;
        }
    }
    async readLoop() {
        const decoder = new TextDecoder();
        try {
            while (this.reader) {
                const {value, done} = await this.reader.read();
                if (done) throw new Error('Flux série fermé');
                this.accept(decoder.decode(value, {stream: true}));
            }
        } catch (error) {
            if (!this.closing) {
                this.rejectPending(error);
                // Do not await cleanup from its own reader task.
                void this.disconnect(error.message);
            }
        }
    }
    accept(fragment) {
        this.record('RX', fragment);
        this.buffer += fragment;
        if (this.buffer.length > 8192) throw new Error('Réponse série trop longue');
        let index;
        while ((index = this.buffer.indexOf('>')) !== -1) {
            const frame = this.buffer.slice(0, index);
            this.buffer = this.buffer.slice(index + 1);
            const pending = this.pending;
            if (!pending) { this.record('INFO', 'Prompt hors commande ignoré'); continue; }
            const lines = frame.split(/[\r\n]+/).map(line => line.trim()).filter(Boolean)
                .filter(line => line.replace(/\s/g, '').toUpperCase() !== pending.command);
            // Empty startup/duplicate prompts cannot complete identification.
            if (!lines.length) continue;
            this.pending = null;
            clearTimeout(pending.timer);
            const response = lines.join('\n');
            if (lines.some(line => /^(?:\?|ERROR|NO DATA|STOPPED|UNABLE TO CONNECT|BUS ERROR|CAN ERROR|BUFFER FULL|DATA ERROR|LV RESET)$/i.test(line))) {
                pending.reject(new Error('Erreur adaptateur: ' + response));
            } else pending.resolve(response);
        }
    }
    rejectPending(error) {
        if (!this.pending) return;
        clearTimeout(this.pending.timer);
        this.pending.reject(error);
        this.pending = null;
    }
    async command(command) {
        if (!['ATI', 'ATRV'].includes(command)) throw new Error('Commande hors liste adaptateur autorisée');
        if (!this.writer || !['CONNECTED', 'IDENTIFYING'].includes(this.state) || this.closing) throw new Error('Adaptateur non connecté');
        if (this.pending) throw new Error('Une commande est déjà en cours');
        this.buffer = '';
        const response = new Promise((resolve, reject) => {
            this.pending = {command, resolve, reject, timer: setTimeout(() => {
                const error = new Error('Délai dépassé sans réponse complète et prompt');
                this.rejectPending(error);
                void this.disconnect(error.message);
            }, this.timeoutMs)};
        });
        // Attach before writing: unplug/write failure must not leave a rejection unhandled.
        const writing = Promise.resolve().then(() => {
            this.record('TX', command + '\r');
            return this.writer.write(new TextEncoder().encode(command + '\r'));
        }).catch(error => {
            this.rejectPending(error);
            void this.disconnect(error.message);
            throw error;
        });
        const [result] = await Promise.all([response, writing]);
        return result;
    }
    async voltage() {
        const result = await this.command('ATRV');
        // Adapter sentinel: no voltage measurement, not a numeric zero.
        // command() has already retained the original RX fragments in the log.
        if (result === '--.-V') return null;
        if (!/^\d+(?:\.\d+)?V$/i.test(result)) throw new Error('Réponse tension invalide: ' + result);
        return result;
    }
    disconnect(reason = 'Déconnexion demandée') {
        if (this.closing) return this.closing;
        this.closing = this.cleanup(reason).finally(() => { this.closing = null; });
        return this.closing;
    }
    async cleanup(reason) {
        this.setState('CLOSING', reason);
        this.rejectPending(new Error(reason));
        if (this.disconnectListener) this.serial.removeEventListener('disconnect', this.disconnectListener);
        if (this.reader) {
            try { await this.reader.cancel(); } catch (error) { this.record('ERROR', error.message); }
            await this.readTask;
            this.reader.releaseLock();
            this.reader = null;
        }
        if (this.writer) {
            try { await this.writer.abort(); } catch (error) { this.record('ERROR', error.message); }
            this.writer.releaseLock();
            this.writer = null;
        }
        if (this.port) {
            try { await this.port.close(); } catch (error) { this.record('ERROR', error.message); }
            this.port = null;
        }
        this.identity = null;
        this.buffer = '';
        this.setState('DISCONNECTED', reason);
    }
    exportLog() {
        return JSON.stringify({scope: 'ADAPTER_ONLY', cluster_identified: false,
            eeprom_read_available: false, events: this.log}, null, 2);
    }
}

// A future driver must implement identification and read capability separately.
// No default implementation receives a transport or issues commands.
class ClusterDriver {
    capability(context = {}) {
        return {clusterIdentified: false, eepromReadAvailable: false,
            reason: 'Protocole de lecture via processeur non documenté et non validé. ' +
                '93C76 déclarée comme cible, non confirmée pour tous les Wrangler 2012–2018.', context};
    }
    async identify() { throw new Error(this.capability().reason); }
    async readEEPROM() { throw new Error(this.capability().reason); }
}
if (typeof module !== 'undefined') module.exports = {AdapterSerialTransport, ClusterDriver};
