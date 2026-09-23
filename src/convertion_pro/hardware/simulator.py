from .base import HardwareInterface


class SimulatedProgrammer(HardwareInterface):
    """
    Development-only programmer.

    Uses synthetic memory so the complete application workflow can
    be tested without connecting to a real vehicle or cluster.
    """

    def __init__(self):
        self.connected = False
        self.memory = bytearray(b"CPTEST|UNIT=KM|DATA=SIMULATED")

    def connect(self) -> bool:
        self.connected = True
        return True

    def identify_cable(self) -> str:
        return "CP-JEEP-004"

    def measure_voltage(self) -> float:
        return 12.4

    def measure_current(self) -> float:
        return 0.42

    def identify_cluster(self) -> str:
        return "SIM-JEEP-WRANGLER-2012-2018"

    def read_memory(self) -> bytes:
        return bytes(self.memory)

    def write_memory(self, data: bytes) -> None:
        if not self.connected:
            raise RuntimeError("Programmer is not connected.")
        self.memory = bytearray(data)

    def verify_memory(self, expected: bytes) -> bool:
        return bytes(self.memory) == expected
