import pytest


@pytest.fixture
def synthetic_jeep_km_dump():
    """
    Synthetic 1024-byte EEPROM image.

    Contains no data copied from a real vehicle.
    Only the validated unit-conversion offsets are meaningful.
    """
    data = bytearray([0xFF] * 1024)

    data[0x68] = 0x04
    data[0x69] = 0x12

    return bytes(data)


@pytest.fixture
def synthetic_jeep_miles_dump(synthetic_jeep_km_dump):
    data = bytearray(synthetic_jeep_km_dump)

    data[0x68] -= 2
    data[0x69] -= 4

    return bytes(data)
