from abc import ABC, abstractmethod


class HardwareInterface(ABC):
    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def identify_cable(self) -> str:
        pass

    @abstractmethod
    def measure_voltage(self) -> float:
        pass

    @abstractmethod
    def measure_current(self) -> float:
        pass

    @abstractmethod
    def identify_cluster(self) -> str:
        pass

    @abstractmethod
    def read_memory(self) -> bytes:
        pass

    @abstractmethod
    def write_memory(self, data: bytes) -> None:
        pass

    @abstractmethod
    def verify_memory(self, expected: bytes) -> bool:
        pass
