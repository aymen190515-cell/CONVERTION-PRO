"""No real bus, serial port, sysfs device or hardware dependency is opened."""
from dataclasses import replace
from types import SimpleNamespace
import sys
import pytest

from convertion_pro.hardware.memory_access import (
    Access, AccessKey, CapabilityRegistry, ConfirmedIdentity, M24C32,
    MemoryAccessError, MemoryReader, Region, Support, _read_m24c32,
    memory_capability,
)
from convertion_pro.hardware.linux_i2c import LinuxI2CReadTransport


class FakeI2C:
    kind = "LINUX_I2C_DEV"
    connection = "TEST-ONLY"
    source = "SIMULATED"

    def __init__(self):
        self.calls = []

    def read_at(self, address, pointer, length):
        self.calls.append((address, pointer, length))
        start = int.from_bytes(pointer, 'big')
        return bytes((i % 251 for i in range(start, start + length)))


def identity(**changes):
    return replace(ConfirmedIdentity("ST_M24C32", "PHYSICAL_MARKING_AND_DATASHEET",
                                     "TEST FIXTURE ONLY", "TEST-ONLY", 0x50), **changes)


def test_production_capability_is_unvalidated_and_never_opens_transport():
    bus = FakeI2C()
    with pytest.raises(MemoryAccessError, match="no physical validation"):
        MemoryReader().read(M24C32.key, "EEPROM", bus, identity())
    assert bus.calls == []
    data = memory_capability("ST_M24C32", "DIRECT_I2C", "LINUX_I2C_DEV", mode="RANDOM_SEQUENTIAL_READ")
    assert data["status"] == "DOCUMENTED_UNVALIDATED"
    assert data["memory_read_supported"] is False
    assert data["regions"] == [{"name": "EEPROM", "start": 0, "size": 4096}]


@pytest.mark.parametrize("chip,access,transport,controller", [
    ("ST_M24C32", "CONTROLLER_CAN", "VLINKER_ELM", ""),
    ("ST_M24C32", "CONTROLLER_CAN", "VLINKER_ELM", "GJ7T-10849-AJ"),
    ("24C32", "DIRECT_I2C", "LINUX_I2C_DEV", ""),
    ("RH850", "PROCESSOR_DEBUG", "UNSPECIFIED", ""),
    ("ST_M24C32", "DIRECT_SPI", "LINUX_I2C_DEV", ""),
])
def test_chip_does_not_imply_controller_protocol(chip, access, transport, controller):
    assert memory_capability(chip, access, transport, controller)["status"] == "UNSUPPORTED"


def test_documented_read_uses_16bit_pointer_and_exact_end_without_wrap():
    bus = FakeI2C()
    data = _read_m24c32(bus, identity(), 0, 4096)
    assert data == bytes(i % 251 for i in range(4096))
    assert len(bus.calls) == 128
    assert bus.calls[0] == (0x50, b'\x00\x00', 32)
    assert bus.calls[-1] == (0x50, b'\x0f\xe0', 32)
    assert _read_m24c32(bus, identity(), 4095, 1) == bytes([4095 % 251])


@pytest.mark.parametrize("offset,length", [(-1,1),(0,0),(4095,2),(4096,1),(True,1)])
def test_invalid_region_is_rejected_without_io(offset, length):
    bus = FakeI2C()
    with pytest.raises(MemoryAccessError):
        _read_m24c32(bus, identity(), offset, length)
    assert not bus.calls


@pytest.mark.parametrize("changes", [
    {"chip":"24C32"}, {"connection":"OTHER"}, {"evidence":""},
    {"method":"ELM_ACK"}, {"device_address":0x58},
])
def test_identity_requires_session_bound_physical_evidence(changes):
    bus = FakeI2C()
    with pytest.raises(MemoryAccessError):
        _read_m24c32(bus, identity(**changes))
    assert not bus.calls


@pytest.mark.parametrize("failure", [b'', OSError('timeout')])
def test_partial_or_failed_reads_never_return_a_padded_dump(failure):
    bus = FakeI2C()
    def fail(*args):
        if isinstance(failure, Exception):
            raise failure
        return failure
    bus.read_at = fail
    with pytest.raises(MemoryAccessError):
        _read_m24c32(bus, identity())


def test_registry_validation_and_region_dispatch_preserve_simulated_provenance():
    with pytest.raises(ValueError, match="validation record"):
        CapabilityRegistry((replace(M24C32, status=Support.VALIDATED),))
    test_entry = replace(M24C32, status=Support.VALIDATED,
                         validation_record="UNIT TEST ONLY, NOT HARDWARE QUALIFICATION")
    reader = MemoryReader(CapabilityRegistry((test_entry,)))
    result = reader.read(M24C32.key, "EEPROM", FakeI2C(), identity(), confirmed_preconditions=M24C32.preconditions)
    assert result["source"] == "SIMULATED"
    assert result["memory_size"] == 4096
    assert len(result["sha256"]) == 64
    with pytest.raises(MemoryAccessError, match="region"):
        reader.read(M24C32.key, "IDENTIFICATION_PAGE", FakeI2C(), identity())
    with pytest.raises(MemoryAccessError, match="No read implementation"):
        MemoryReader(CapabilityRegistry((test_entry,)), {}).read(
            M24C32.key, "EEPROM", FakeI2C(), identity(), confirmed_preconditions=M24C32.preconditions)


def test_linux_backend_uses_combined_transaction_and_closes(monkeypatch):
    calls = []
    class Bus:
        funcs = 1
        def __init__(self, number):
            calls.append(("open", number))
        def i2c_rdwr(self, pointer, response):
            calls.append(("combined", pointer, len(response)))
            response[:] = b'\x19' * len(response)
        def close(self):
            calls.append(("close",))
    messages = SimpleNamespace(write=lambda address, pointer:(address, pointer),
                               read=lambda address, count:bytearray(count))
    monkeypatch.setitem(sys.modules, 'smbus2', SimpleNamespace(
        SMBus=Bus, i2c_msg=messages, I2cFunc=SimpleNamespace(I2C=1)))
    monkeypatch.setattr(sys, 'platform', 'linux')
    transport = LinuxI2CReadTransport(8)
    assert calls == []
    with transport:
        assert transport.read_at(0x50, b'\x01\x20', 4) == b'\x19'*4
    assert calls == [("open",8),("combined",(0x50,b'\x01\x20'),4),("close",)]
    with pytest.raises(MemoryAccessError, match="not open"):
        transport.read_at(0x50, b'\x00\x00', 1)


def test_windows_cannot_be_treated_as_linux_i2c(monkeypatch):
    monkeypatch.setattr(sys, 'platform', 'win32')
    with pytest.raises(MemoryAccessError, match="COM port"):
        with LinuxI2CReadTransport(0):
            pytest.fail("Must not open a real device")
