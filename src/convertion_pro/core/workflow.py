from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
import hashlib

from convertion_pro.core.jeep_wrangler import (
    convert_km_to_miles,
    convert_miles_to_km,
)


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


@dataclass
class ConversionResult:
    source_unit: str
    target_unit: str
    original_data: bytes
    converted_data: bytes
    backup_path: Path
    verified: bool


class ConversionWorkflow:
    def __init__(self, hardware, profile: dict):
        self.hardware = hardware
        self.profile = profile

        self.original_data: bytes | None = None
        self.backup_path: Path | None = None
        self.safety_report: SafetyReport | None = None

    def run_safety_check(self) -> SafetyReport:
        programmer = self.hardware.connect()

        cable = (
            self.hardware.identify_cable()
            == self.profile["required_cable"]
        )

        voltage_value = self.hardware.measure_voltage()

        voltage = (
            self.profile["voltage_min"]
            <= voltage_value
            <= self.profile["voltage_max"]
        )

        cluster_id = self.hardware.identify_cluster()

        communication = bool(cluster_id)

        profile_match = (
            cluster_id == self.profile["cluster_id"]
        )

        self.safety_report = SafetyReport(
            programmer=programmer,
            cable=cable,
            voltage=voltage,
            communication=communication,
            profile=profile_match,
        )

        return self.safety_report

    def _require_safe_state(self) -> None:
        if self.safety_report is None:
            raise RuntimeError(
                "WRITE BLOCKED: safety check has not been performed."
            )

        if not self.safety_report.passed:
            raise RuntimeError(
                "WRITE BLOCKED: safety check failed."
            )

    def create_backup(
        self,
        directory: str = "data/backups",
    ) -> Path:

        self._require_safe_state()

        # READ EEPROM FROM HARDWARE
        self.original_data = self.hardware.read_memory()

        if not self.original_data:
            raise RuntimeError(
                "Cannot create an empty backup."
            )

        expected_size = (
            self.profile
            .get("memory", {})
            .get("size_bytes")
        )

        if (
            expected_size is not None
            and len(self.original_data) != expected_size
        ):
            raise RuntimeError(
                "EEPROM size does not match vehicle profile. "
                f"Expected {expected_size} bytes, "
                f"received {len(self.original_data)} bytes."
            )

        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )

        digest = hashlib.sha256(
            self.original_data
        ).hexdigest()[:12]

        self.backup_path = (
            target
            / f"original_{stamp}_{digest}.bin"
        )

        self.backup_path.write_bytes(
            self.original_data
        )

        # Verify backup on disk before allowing any write.
        if self.backup_path.read_bytes() != self.original_data:
            raise RuntimeError(
                "Backup verification failed."
            )

        return self.backup_path

    def prepare_vehicle_conversion(
        self,
        source_unit: str,
        target_unit: str,
    ) -> bytes:

        if (
            self.original_data is None
            or self.backup_path is None
        ):
            raise RuntimeError(
                "Mandatory original backup has not been created."
            )

        if source_unit == target_unit:
            raise ValueError(
                "Source and target units are identical."
            )

        supported = {"KM", "MI"}

        if (
            source_unit not in supported
            or target_unit not in supported
        ):
            raise ValueError(
                "Unsupported unit conversion."
            )

        make = self.profile.get("make")
        model = self.profile.get("model")
        generation = self.profile.get("generation")

        if (
            make == "Jeep"
            and model == "Wrangler"
            and generation == "2012-2018"
        ):
            if source_unit == "KM" and target_unit == "MI":
                return convert_km_to_miles(
                    self.original_data
                )

            if source_unit == "MI" and target_unit == "KM":
                return convert_miles_to_km(
                    self.original_data
                )

        raise RuntimeError(
            "No validated conversion algorithm "
            "is available for this vehicle profile."
        )

    def program_and_verify(
        self,
        converted_data: bytes,
    ) -> bool:

        self._require_safe_state()

        if (
            self.original_data is None
            or self.backup_path is None
        ):
            raise RuntimeError(
                "WRITE BLOCKED: original backup is mandatory."
            )

        if not self.backup_path.exists():
            raise RuntimeError(
                "WRITE BLOCKED: backup file no longer exists."
            )

        if (
            self.backup_path.read_bytes()
            != self.original_data
        ):
            raise RuntimeError(
                "WRITE BLOCKED: backup integrity check failed."
            )

        if len(converted_data) != len(self.original_data):
            raise RuntimeError(
                "WRITE BLOCKED: converted EEPROM size changed."
            )

        # WRITE TO HARDWARE
        self.hardware.write_memory(
            converted_data
        )

        # READ BACK FROM HARDWARE
        read_back = self.hardware.read_memory()

        # BYTE-FOR-BYTE VERIFICATION
        if read_back != converted_data:
            raise RuntimeError(
                "Read-back verification failed."
            )

        # Keep hardware-level verification as a second check.
        if not self.hardware.verify_memory(
            converted_data
        ):
            raise RuntimeError(
                "Hardware verification failed."
            )

        return True

    def convert_and_program(
        self,
        source_unit: str,
        target_unit: str,
        backup_directory: str = "data/backups",
    ) -> ConversionResult:
        """
        Complete vehicle conversion operation:

        SAFETY
        -> READ
        -> BACKUP
        -> CONVERT
        -> WRITE
        -> READ BACK
        -> VERIFY
        """

        safety = self.run_safety_check()

        if not safety.passed:
            raise RuntimeError(
                "Conversion blocked because safety checks failed."
            )

        self.create_backup(
            backup_directory
        )

        converted = self.prepare_vehicle_conversion(
            source_unit,
            target_unit,
        )

        verified = self.program_and_verify(
            converted
        )

        return ConversionResult(
            source_unit=source_unit,
            target_unit=target_unit,
            original_data=self.original_data,
            converted_data=converted,
            backup_path=self.backup_path,
            verified=verified,
        )

    # ---------------------------------------------------------
    # Legacy simulation methods
    # Kept temporarily so the existing V0.1 tests/UI still work.
    # ---------------------------------------------------------

    def detect_unit(self) -> str:
        data = self.hardware.read_memory()

        if b"UNIT=KM" in data:
            return "KM"

        if b"UNIT=MI" in data:
            return "MI"

        raise RuntimeError(
            "Unit could not be detected."
        )

    def prepare_synthetic_conversion(
        self,
        target_unit: str,
    ) -> bytes:

        if (
            self.original_data is None
            or self.backup_path is None
        ):
            raise RuntimeError(
                "Mandatory original backup has not been created."
            )

        if target_unit not in {"KM", "MI"}:
            raise ValueError(
                "Unsupported target unit."
            )

        data = self.hardware.read_memory()

        if target_unit == "MI":
            return data.replace(
                b"UNIT=KM",
                b"UNIT=MI",
            )

        return data.replace(
            b"UNIT=MI",
            b"UNIT=KM",
        )
