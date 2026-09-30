"""Original file/simulation workspace. No programmer or transport imports.

File selection never proves chip identity. Backups are byte-exact ZIP exports,
not programmer writes. Verification compares bytes, not physical memory.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from threading import RLock
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from convertion_pro.hardware.memory_access import M24C32, memory_capability

MAX_BYTES = 8 * 1024 * 1024
MAX_STORED_BYTES = 32 * 1024 * 1024
MAX_SESSIONS = 16


def chip_catalog():
    capability = memory_capability("ST_M24C32", "DIRECT_I2C", "LINUX_I2C_DEV", mode="RANDOM_SEQUENTIAL_READ")
    return {
        "schema_version": 1,
        "hardware_execution_enabled": False,
        "profiles": [{
            "id": "ST_M24C32", "label": "ST M24C32 — EEPROM I²C, 4 096 octets",
            "manufacturer": "STMicroelectronics", "family": "I2C_EEPROM",
            "capacity_bytes": 4096, "regions": capability["regions"],
            "packages_and_masks": "À confirmer depuis le marquage exact ; aucun brochage fourni",
            "required_interface": "DIRECT_I2C", "required_transport": "LINUX_I2C_DEV",
            "adapter_requirement": "Contrôleur I²C direct qualifié, pas un port COM/vLinker",
            "capability": capability,
        }],
        "file_profile": {"id": "RAW_FILE", "label": "Fichier brut — puce non identifiée",
                         "capacity_bytes": None, "hardware_supported": False},
        "planned_families": [
            {"id": name, "status": "REFERENCE_ONLY", "hardware_supported": False}
            for name in ("SPI_EEPROM_NOR", "MICROWIRE", "MCU_DEBUG", "MCU_BOOT", "CONTROLLER_CAN")
        ],
        "limits": {"max_file_bytes": MAX_BYTES, "max_sessions": MAX_SESSIONS,
                   "max_stored_bytes": MAX_STORED_BYTES},
        "operation_status": {"file_import": "IMPLEMENTED", "simulation": "IMPLEMENTED",
                             "backup_export": "IMPLEMENTED", "file_compare": "IMPLEMENTED",
                             "hardware_read": "BLOCKED", "hardware_write": "BLOCKED",
                             "erase": "BLOCKED", "unlock": "BLOCKED"},
    }


def validate_image(data, profile):
    if not isinstance(data, bytes) or not 1 <= len(data) <= MAX_BYTES:
        raise ValueError("Le fichier doit contenir de 1 à 8 Mio d'octets.")
    if profile not in ("RAW_FILE", "ST_M24C32"):
        raise ValueError("Profil inconnu : aucune compatibilité ne peut être déduite.")
    if profile == "ST_M24C32" and len(data) != 4096:
        raise ValueError("La région EEPROM ST M24C32 attend exactement 4096 octets.")


@dataclass
class Snapshot:
    data: bytes
    source: str
    profile: str
    name: str
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    audit: list = field(default_factory=list)

    def metadata(self):
        return {"id": self.id, "source": self.source, "profile": self.profile,
                "name": self.name, "created_at": self.created_at,
                "size_bytes": len(self.data), "sha256": sha256(self.data).hexdigest(),
                "chip_identity_verified": False, "hardware_access": False,
                "region": "EEPROM" if self.profile == "ST_M24C32" else "FILE_BYTES",
                "audit": list(self.audit)}


class Workspace:
    def __init__(self):
        self._items = {}
        self._lock = RLock()

    def _new(self, data, source, profile, name):
        validate_image(data, profile)
        with self._lock:
            if (len(self._items) >= MAX_SESSIONS
                    or sum(len(s.data) for s in self._items.values()) + len(data) > MAX_STORED_BYTES):
                raise ValueError("Espace temporaire plein. Fermer une session avant de continuer.")
            # User filenames are display-only and never used as filesystem paths.
            snapshot = Snapshot(data, source, profile, name.replace('\\', '/').split('/')[-1][:160])
            snapshot.audit.append({"event": "IMPORT_FILE" if source == "FILE" else "CREATE_SIMULATION",
                                   "at": snapshot.created_at, "hardware_access": False})
            self._items[snapshot.id] = snapshot
            return snapshot.metadata()

    def import_file(self, data, profile="RAW_FILE", name="image.bin"):
        return self._new(data, "FILE", profile, name)

    def simulate(self, profile):
        if profile != "ST_M24C32":
            raise ValueError("Démonstration disponible uniquement pour le profil ST M24C32.")
        # Reproducible synthetic pattern; never inserted as a hardware fallback.
        return self._new(bytes(i % 251 for i in range(4096)), "SIMULATED", profile,
                         "SIMULATED-m24c32.bin")

    def _get(self, session):
        try:
            return self._items[session]
        except KeyError:
            raise ValueError("Session inconnue ou fermée.") from None

    def inspect(self, session):
        with self._lock:
            snapshot = self._get(session)
            return {**snapshot.metadata(), "preview_hex": snapshot.data[:256].hex(),
                    "preview_bytes": min(256, len(snapshot.data))}

    def export_backup(self, session):
        with self._lock:
            snapshot = self._get(session)
            event = {"event": "EXPORT_PREPARED", "at": datetime.now(timezone.utc).isoformat(),
                     "note": "Archive générée ; sauvegarde sur disque utilisateur non confirmée."}
            manifest = snapshot.metadata()
            manifest["audit"].append(event)
            output = BytesIO()
            with ZipFile(output, 'w', ZIP_DEFLATED) as archive:
                archive.writestr('memory.bin', snapshot.data)
                archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
            blob = output.getvalue()
            # Internal byte-level verification, not hardware read-back.
            with ZipFile(BytesIO(blob)) as archive:
                if archive.read('memory.bin') != snapshot.data:
                    raise RuntimeError("Vérification interne de la sauvegarde échouée.")
            self._record(snapshot, event)
            return blob

    @staticmethod
    def _record(snapshot, event):
        # Bound memory usage while retaining creation and recent actions.
        snapshot.audit.append(event)
        if len(snapshot.audit) > 100:
            del snapshot.audit[1]

    def compare(self, session, candidate):
        if not isinstance(candidate, bytes) or not 1 <= len(candidate) <= MAX_BYTES:
            raise ValueError("Fichier de comparaison vide ou trop grand.")
        with self._lock:
            snapshot = self._get(session)
            changed = 0
            offsets = []
            for index in range(max(len(snapshot.data), len(candidate))):
                before = snapshot.data[index] if index < len(snapshot.data) else None
                after = candidate[index] if index < len(candidate) else None
                if before != after:
                    changed += 1
                    if len(offsets) < 64:
                        offsets.append({"offset": index, "reference": before, "candidate": after})
            result = {"verification": "FILE_BYTES_ONLY", "hardware_verified": False,
                      "reference_source": snapshot.source, "identical": changed == 0,
                      "reference_size": len(snapshot.data), "candidate_size": len(candidate),
                      "changed_byte_count": changed, "first_differences": offsets,
                      "differences_truncated": changed > len(offsets),
                      "candidate_sha256": sha256(candidate).hexdigest()}
            self._record(snapshot, {"event": "COMPARE_FILE", "at": datetime.now(timezone.utc).isoformat(),
                                    "identical": result["identical"], "hardware_verified": False})
            return result

    def close(self, session):
        with self._lock:
            self._get(session)
            del self._items[session]
            return {"closed": True, "scope": "IN_MEMORY_SESSION_ONLY"}
