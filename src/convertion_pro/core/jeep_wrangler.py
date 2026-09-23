"""
Jeep Wrangler 2012-2018 EEPROM unit conversion.

Validated vehicle rule:

KM -> MI
    0x68 = current value - 2
    0x69 = current value - 4

MI -> KM
    0x68 = current value + 2
    0x69 = current value + 4

This module modifies only the two unit-configuration bytes.
"""

OFFSET_68 = 0x68
OFFSET_69 = 0x69

MINIMUM_SIZE = OFFSET_69 + 1


class JeepWranglerConversionError(RuntimeError):
    pass


def _validate_dump(data: bytes) -> None:
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("EEPROM data must be bytes.")

    if len(data) < MINIMUM_SIZE:
        raise JeepWranglerConversionError(
            f"EEPROM dump is too small: {len(data)} bytes."
        )


def convert_km_to_miles(data: bytes) -> bytes:
    """
    Convert Jeep Wrangler EEPROM unit configuration from KM to Miles.
    """
    _validate_dump(data)

    result = bytearray(data)

    if result[OFFSET_68] < 2:
        raise JeepWranglerConversionError(
            "Invalid KM value at EEPROM offset 0x68."
        )

    if result[OFFSET_69] < 4:
        raise JeepWranglerConversionError(
            "Invalid KM value at EEPROM offset 0x69."
        )

    result[OFFSET_68] -= 2
    result[OFFSET_69] -= 4

    return bytes(result)


def convert_miles_to_km(data: bytes) -> bytes:
    """
    Convert Jeep Wrangler EEPROM unit configuration from Miles to KM.
    """
    _validate_dump(data)

    result = bytearray(data)

    if result[OFFSET_68] > 0xFD:
        raise JeepWranglerConversionError(
            "Invalid Miles value at EEPROM offset 0x68."
        )

    if result[OFFSET_69] > 0xFB:
        raise JeepWranglerConversionError(
            "Invalid Miles value at EEPROM offset 0x69."
        )

    result[OFFSET_68] += 2
    result[OFFSET_69] += 4

    return bytes(result)


def changed_offsets(before: bytes, after: bytes) -> list[int]:
    """
    Return every EEPROM offset changed between two dumps.
    """
    if len(before) != len(after):
        raise JeepWranglerConversionError(
            "EEPROM size changed during conversion."
        )

    return [
        index
        for index, (old, new) in enumerate(zip(before, after))
        if old != new
    ]
