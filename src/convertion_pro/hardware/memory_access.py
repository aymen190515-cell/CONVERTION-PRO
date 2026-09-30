"""Chip/access/transport capabilities. No device discovery or I/O on import.

An EEPROM part number is not a CAN protocol. All production combinations are
unqualified until a bench validation record exists; none is supplied here.
"""
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
import hashlib


class Access(StrEnum):
    DIRECT_I2C = "DIRECT_I2C"
    DIRECT_SPI = "DIRECT_SPI"
    PROCESSOR_DEBUG = "PROCESSOR_DEBUG"
    CONTROLLER_CAN = "CONTROLLER_CAN"


class Support(StrEnum):
    UNSUPPORTED = "UNSUPPORTED"
    DOCUMENTED_UNVALIDATED = "DOCUMENTED_UNVALIDATED"
    VALIDATED = "VALIDATED"


class ReadEffect(StrEnum):
    UNKNOWN = "UNKNOWN"
    NO_NONVOLATILE_WRITE = "NO_NONVOLATILE_WRITE"
    MAY_ERASE_OR_WRITE = "MAY_ERASE_OR_WRITE"


class MemoryAccessError(RuntimeError):
    pass


@dataclass(frozen=True)
class Region:
    name: str
    start: int
    size: int

    def __post_init__(self):
        if not self.name or self.start < 0 or self.size <= 0:
            raise ValueError("Invalid memory region")


@dataclass(frozen=True)
class AccessKey:
    chip: str
    access: Access
    transport: str
    # Required for controller-mediated access: firmware/protocol variant,
    # not merely the chip contained inside the cluster.
    controller_protocol: str = ""
    mode: str = ""
    package: str = ""
    mask: str = ""


@dataclass(frozen=True)
class Capability:
    key: AccessKey
    status: Support
    regions: tuple[Region, ...]
    documentation: tuple[str, ...]
    reason: str
    validation_record: str = ""
    read_effect: ReadEffect = ReadEffect.UNKNOWN
    preconditions: tuple[str, ...] = ()


@dataclass(frozen=True)
class ConfirmedIdentity:
    chip: str
    method: str
    evidence: str
    # Confirmation is bound to this explicit connection and I2C address.
    # It is not inferred from an ACK, adapter name, vehicle selector or FF data.
    connection: str
    device_address: int


class I2CReadTransport(Protocol):
    kind: str
    connection: str
    source: str

    def read_at(self, device_address: int, address: bytes, length: int) -> bytes:
        """Atomic address-pointer write + repeated-start read; no data write."""
        ...


class CapabilityRegistry:
    def __init__(self, capabilities=()):
        self._entries = {}
        for capability in capabilities:
            if capability.key in self._entries:
                raise ValueError("Duplicate chip/access/transport combination")
            if capability.key.access == Access.CONTROLLER_CAN and not capability.key.controller_protocol:
                raise ValueError("CAN access requires an exact controller protocol")
            if capability.status != Support.UNSUPPORTED and not capability.documentation:
                raise ValueError("A supported protocol requires documentation")
            if capability.status == Support.VALIDATED and not capability.validation_record:
                raise ValueError("Validated capability requires a bench validation record")
            if capability.status == Support.VALIDATED and not capability.key.mode:
                raise ValueError("Validated capability requires an explicit operation mode")
            if len({r.name for r in capability.regions}) != len(capability.regions):
                raise ValueError("Duplicate region")
            self._entries[capability.key] = capability

    def lookup(self, key: AccessKey) -> Capability:
        return self._entries.get(key, Capability(
            key, Support.UNSUPPORTED, (), (),
            "No documented driver exists for this chip/access/transport/controller combination.",
        ))

    def require_validated(self, key: AccessKey, region: str) -> Region:
        capability = self.lookup(key)
        if capability.status != Support.VALIDATED:
            raise MemoryAccessError(capability.reason)
        if capability.read_effect != ReadEffect.NO_NONVOLATILE_WRITE:
            raise MemoryAccessError("Read mode may erase/write memory or has unknown effects; blocked")
        for item in capability.regions:
            if item.name == region:
                return item
        raise MemoryAccessError("Memory region is not supported")


M24C32 = Capability(
    AccessKey("ST_M24C32", Access.DIRECT_I2C, "LINUX_I2C_DEV", mode="RANDOM_SEQUENTIAL_READ"),
    Support.DOCUMENTED_UNVALIDATED,
    (Region("EEPROM", 0, 4096),),
    ("https://www.st.com/resource/en/datasheet/m24c32-r.pdf#page=14",
     "https://docs.kernel.org/i2c/dev-interface.html",
     "https://smbus2.readthedocs.io/en/latest/api.html"),
    "Direct I2C reader is implemented from documentation but has no physical validation. "
    "Requires a confirmed ST M24C32, a direct I2C controller and verified electrical setup; "
    "vLinker/ELM CAN is not this transport. No HTTP hardware execution is enabled.",
    read_effect=ReadEffect.NO_NONVOLATILE_WRITE,
    preconditions=("Exact chip/package marking confirmed", "Electrical limits and bus ownership verified",
                   "Exact I2C adapter and combined transaction behavior bench qualified"),
)
REGISTRY = CapabilityRegistry((M24C32,))


def memory_capability(chip="", access="", transport="", controller_protocol="", mode="", package="", mask=""):
    """Passive metadata only; safe for a remote preview to query."""
    try:
        key = AccessKey(chip, Access(access), transport, controller_protocol, mode, package, mask)
    except ValueError:
        return {"status": Support.UNSUPPORTED, "memory_read_supported": False,
                "reason": "Select a documented chip, access interface and transport."}
    entry = REGISTRY.lookup(key)
    return {
        "chip": chip, "access": access, "transport": transport,
        "controller_protocol": controller_protocol,
        "mode": mode, "package": package, "mask": mask,
        "status": entry.status,
        "memory_read_supported": (entry.status == Support.VALIDATED
                                  and entry.read_effect == ReadEffect.NO_NONVOLATILE_WRITE),
        "regions": [{"name": r.name, "start": r.start, "size": r.size} for r in entry.regions],
        "documentation": list(entry.documentation), "reason": entry.reason,
        "read_effect": entry.read_effect, "preconditions": list(entry.preconditions),
        "hardware_access": False,
    }


def _read_m24c32(transport: I2CReadTransport, identity: ConfirmedIdentity,
               offset: int = 0, length: int = 4096) -> bytes:
    """Low-level, unqualified direct-I2C implementation, NOT an HTTP action.

    ST DS0952 sections 5.2.1/5.2.3. Does not auto-identify a chip. Integration
    must first require_validated() and obtain session-bound identity evidence.
    Tests inject a fake transport; this function never supplies fallback bytes.
    """
    if transport.kind != "LINUX_I2C_DEV":
        raise MemoryAccessError("This implementation requires direct Linux I2C, not serial/CAN")
    if (identity.chip != "ST_M24C32" or identity.method != "PHYSICAL_MARKING_AND_DATASHEET"
            or not identity.evidence.strip() or identity.connection != transport.connection):
        raise MemoryAccessError("Chip identity and this connection must be explicitly confirmed")
    if not 0x50 <= identity.device_address <= 0x57:
        raise MemoryAccessError("Invalid M24C32 device address")
    if type(offset) is not int or type(length) is not int or offset < 0 or length <= 0 or offset + length > 4096:
        raise MemoryAccessError("Read is outside the documented 4096-byte EEPROM region")
    chunks = []
    try:
        for position in range(offset, offset + length, 32):
            count = min(32, offset + length - position)
            data = transport.read_at(identity.device_address, position.to_bytes(2, "big"), count)
            if not isinstance(data, bytes) or len(data) != count:
                raise MemoryAccessError("Incomplete read; no dump was returned")
            chunks.append(data)
    except MemoryAccessError:
        raise
    except Exception as exc:
        raise MemoryAccessError("Transport failed; no dump was returned") from exc
    return b"".join(chunks)


class MemoryReader:
    """Dispatch only an explicitly registered and qualified combination.

    Caller owns the exclusive transport session and closes it. No probing,
    fallback, aliasing of chips, or automatic opening of a transport occurs.
    """
    def __init__(self, registry=REGISTRY, drivers=None):
        self.registry = registry
        self.drivers = {M24C32.key: _read_m24c32} if drivers is None else dict(drivers)

    def read(self, key, region_name, transport, identity, *, confirmed_preconditions=()):
        region = self.registry.require_validated(key, region_name)
        if not set(self.registry.lookup(key).preconditions).issubset(confirmed_preconditions):
            raise MemoryAccessError("Required bench preconditions have not been confirmed")
        driver = self.drivers.get(key)
        if driver is None:
            raise MemoryAccessError("No read implementation is registered for this combination")
        if (transport.kind != key.transport or identity.chip != key.chip
                or identity.connection != transport.connection or not identity.evidence.strip()
                or transport.source not in ("HARDWARE", "SIMULATED")):
            raise MemoryAccessError("Identity, transport and provenance do not match the requested chip")
        try:
            data = driver(transport, identity, region.start, region.size)
        except MemoryAccessError:
            raise
        except Exception as exc:
            raise MemoryAccessError("Read failed; no dump was returned") from exc
        if not isinstance(data, bytes) or len(data) != region.size:
            raise MemoryAccessError("Incomplete region; no dump was returned")
        return {"source": transport.source, "chip": key.chip,
                "access": key.access, "transport": key.transport,
                "controller_protocol": key.controller_protocol,
                "identity_method": identity.method, "region": region.name,
                "offset": region.start, "memory_size": len(data),
                "data": data, "sha256": hashlib.sha256(data).hexdigest()}
