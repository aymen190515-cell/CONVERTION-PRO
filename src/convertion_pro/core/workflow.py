from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
import hashlib


@dataclass
class SafetyReport:
    programmer: bool
    cable: bool
    voltage: bool
    communication: bool
    profile: bool

    @property
    def passed(self) -> bool:
        return all([
            self.programmer,
            self.cable,
            self.voltage,
            self.communication,
            self.profile,
        ])


class ConversionWorkflow:
    def __init__(self, hardware, profile: dict):
        self.hardware = hardware
        self.profile = profile
        self.original_data: bytes | None = None
        self.backup_path: Path | None = None

    def run_safety_check(self) -> SafetyReport:
        programmer = self.hardware.connect()
        cable = self.hardware.identify_cable() == self.profile["required_cable"]

        voltage_value = self.hardware.measure_voltage()
        voltage = (
            self.profile["voltage_min"]
            <= voltage_value
            <= self.profile["voltage_max"]
        )

        cluster_id = self.hardware.identify_cluster()
        communication = bool(cluster_id)
        profile = cluster_id == self.profile["cluster_id"]

        return SafetyReport(
            programmer=programmer,
            cable=cable,
            voltage=voltage,
            communication=communication,
            profile=profile,
        )

    def create_backup(self, directory: str = "data/backups") -> Path:
        self.original_data = self.hardware.read_memory()

        if not self.original_data:
            raise RuntimeError("Cannot create an empty backup.")

        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        digest = hashlib.sha256(self.original_data).hexdigest()[:12]

        self.backup_path = target / f"original_{stamp}_{digest}.bin"
        self.backup_path.write_bytes(self.original_data)

        return self.backup_path

    def detect_unit(self) -> str:
        data = self.hardware.read_memory()

        if b"UNIT=KM" in data:
            return "KM"

        if b"UNIT=MI" in data:
            return "MI"

        raise RuntimeError("Unit could not be detected.")

    def prepare_synthetic_conversion(self, target_unit: str) -> bytes:
        if self.original_data is None or self.backup_path is None:
            raise RuntimeError("Mandatory original backup has not been created.")

        if target_unit not in {"KM", "MI"}:
            raise ValueError("Unsupported target unit.")

        data = self.hardware.read_memory()

        if target_unit == "MI":
            return data.replace(b"UNIT=KM", b"UNIT=MI")

        return data.replace(b"UNIT=MI", b"UNIT=KM")

    def program_and_verify(self, converted_data: bytes) -> bool:
        if self.backup_path is None:
            raise RuntimeError("WRITE BLOCKED: original backup is mandatory.")

        self.hardware.write_memory(converted_data)

        if not self.hardware.verify_memory(converted_data):
            raise RuntimeError("Read-back verification failed.")

        return True
