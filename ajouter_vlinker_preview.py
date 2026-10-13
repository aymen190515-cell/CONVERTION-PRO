"""Ajoute un bouton de test USB à l'aperçu FastAPI de Conversion Pro.

Depuis la racine du dépôt dans Codespaces : python3 ajouter_vlinker_preview.py
Le bouton utilise Web Serial dans le navigateur local, pas le serveur Codespaces.
"""

from pathlib import Path

path = Path("preview.py")
source = path.read_text(encoding="utf-8")
marker = 'id="cp-vlinker-button"'

if marker in source:
    print("Bouton vLinker déjà présent; aucun changement.")
    raise SystemExit(0)

if source.count("<script>") != 1 or source.count("</script>") != 1:
    raise SystemExit("Structure du HTML inattendue : aucun fichier modifié.")

panel = '''
<div id="cp-vlinker-panel" style="position:fixed;right:16px;bottom:16px;z-index:9999;
background:#101924;color:#f4f7fb;border:1px solid #26384b;border-radius:10px;
padding:12px;max-width:310px;box-shadow:0 8px 24px #0008">
  <button id="cp-vlinker-button" type="button" onclick="cpTestVLinker()"
    style="background:#1687ff;color:white;border:0;border-radius:7px;padding:9px 12px">
    Tester le vLinker USB
  </button>
  <div id="cp-vlinker-status" role="status" style="margin-top:8px;font-size:13px">
    Aucun câble testé
  </div>
</div>
'''

javascript = '''
async function cpTestVLinker() {
    const status = document.getElementById('cp-vlinker-status');
    const button = document.getElementById('cp-vlinker-button');
    if (!('serial' in navigator)) {
        status.textContent = 'Ouvre cette page dans Chrome ou Edge sur ton PC.';
        return;
    }
    button.disabled = true;
    let port, reader, writer, timer;
    try {
        // La sélection doit suivre le clic sur le bouton.
        port = await navigator.serial.requestPort();
        await port.open({baudRate: 115200});
        status.textContent = 'Port USB ouvert. Identification en cours…';
        reader = port.readable.getReader();
        writer = port.writable.getWriter();
        await writer.write(new TextEncoder().encode('ATI\\r'));

        const reponse = await Promise.race([
            (async () => {
                const decoder = new TextDecoder();
                let texte = '';
                while (texte.length < 4096) {
                    const {value, done} = await reader.read();
                    if (done) break;
                    texte += decoder.decode(value, {stream:true});
                    if (texte.includes('>')) break;
                }
                return texte;
            })(),
            new Promise((_, reject) => {
                timer = setTimeout(() => reject(new Error('Aucune réponse ATI')), 3000);
            })
        ]);
        const identite = reponse.replaceAll('>', '')
            .split(/[\\r\\n]+/).map(x => x.trim())
            .filter(x => x && x.toUpperCase() !== 'ATI').join(' ');
        status.textContent = identite && identite !== '?'
            ? 'Interface détectée : ' + identite
            : 'Port USB ouvert; identification incomplète.';
    } catch (erreur) {
        status.textContent = erreur.name === 'NotFoundError'
            ? 'Sélection annulée.'
            : erreur.message === 'Aucune réponse ATI'
                ? 'Port USB ouvert, mais interface sans réponse. Une alimentation OBD peut être nécessaire.'
                : 'Connexion impossible : ' + erreur.message;
    } finally {
        clearTimeout(timer);
        if (reader) {
            try { await reader.cancel(); } catch (_) {}
            reader.releaseLock();
        }
        if (writer) writer.releaseLock();
        if (port) {
            try { await port.close(); } catch (_) {}
        }
        button.disabled = false;
    }
}
'''

updated = source.replace("<script>", panel + "<script>", 1)
updated = updated.replace("</script>", javascript + "\n</script>", 1)
compile(updated, str(path), "exec")
path.write_text(updated, encoding="utf-8")
print("Bouton de test vLinker ajouté dans preview.py.")
