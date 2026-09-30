"""Documented Linux i2c-dev transport. Not available on Windows or via vLinker.

No scan, port open, device access or dependency import occurs at module import.
No write-memory/erase operation is exposed. Experimental; not hardware tested.
"""
import sys
from .memory_access import MemoryAccessError


class LinuxI2CReadTransport:
    kind = "LINUX_I2C_DEV"
    source = "HARDWARE"

    def __init__(self, bus_number: int):
        if type(bus_number) is not int or bus_number < 0:
            raise ValueError("Explicit nonnegative Linux bus number required")
        self.bus_number = bus_number
        self.connection = f"/dev/i2c-{bus_number}"
        self._bus = None
        self._messages = None

    def __enter__(self):
        if self._bus is not None:
            raise MemoryAccessError("Transport is already open")
        if sys.platform != "linux":
            raise MemoryAccessError("Linux i2c-dev is required; a COM port is not an I2C controller")
        from smbus2 import SMBus, i2c_msg, I2cFunc
        bus = SMBus(self.bus_number)
        try:
            if not (bus.funcs & I2cFunc.I2C):
                raise MemoryAccessError("Adapter does not support combined I2C transactions")
        except Exception:
            bus.close()
            raise
        self._bus, self._messages = bus, i2c_msg
        return self

    def __exit__(self, *args):
        bus, self._bus = self._bus, None
        self._messages = None
        if bus is not None:
            bus.close()

    def read_at(self, device_address: int, address: bytes, length: int) -> bytes:
        if self._bus is None:
            raise MemoryAccessError("Transport is not open")
        if (not 0x50 <= device_address <= 0x57 or not isinstance(address, bytes)
                or len(address) != 2 or not 1 <= length <= 32
                or int.from_bytes(address, "big") + length > 4096):
            raise MemoryAccessError("Invalid M24C32 read transaction")
        # The write-direction message contains ONLY the address pointer, never
        # EEPROM data. i2c_rdwr performs a repeated START, not an intervening STOP.
        pointer = self._messages.write(device_address, address)
        response = self._messages.read(device_address, length)
        self._bus.i2c_rdwr(pointer, response)
        return bytes(response)
