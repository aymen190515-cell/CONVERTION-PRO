import pytest

from convertion_pro.core.toyota_rh850 import (
    ToyotaRH850ConversionError,
    convert_region,
    identify_variant,
)


def memory_with_values(
    size: int,
    values: dict[int, int],
) -> bytes:
    data = bytearray([0xFF] * size)

    for offset, value in values.items():
        data[offset] = value

    return bytes(data)


def test_tundra_gas_canada_to_usa():
    original = memory_with_values(
        0xC05,
        {
            0xB82: 0xDC,
            0xB84: 0x05,
            0xBC2: 0xDD,
            0xBC4: 0x05,
            0xC02: 0xDE,
            0xC04: 0x05,
        },
    )

    converted, variant = convert_region(
        original,
        "tundra_gas",
        "CANADA",
        "USA",
    )

    assert variant.name == "Tundra Gas"
    assert converted[0xB82] == 0xDA
    assert converted[0xB84] == 0x03
    assert converted[0xBC2] == 0xDB
    assert converted[0xBC4] == 0x03
    assert converted[0xC02] == 0xDC
    assert converted[0xC04] == 0x03


def test_tundra_round_trip():
    original = memory_with_values(
        0xC05,
        {
            0xB82: 0xDC,
            0xB84: 0x05,
            0xBC2: 0xDD,
            0xBC4: 0x05,
            0xC02: 0xDE,
            0xC04: 0x05,
        },
    )

    usa, _ = convert_region(
        original,
        "tundra_gas",
        "CANADA",
        "USA",
    )

    restored, _ = convert_region(
        usa,
        "tundra_gas",
        "USA",
        "CANADA",
    )

    assert restored == original


def test_highlander_variant_is_detected():
    data = memory_with_values(
        0x7C05,
        {
            0x7B82: 0xA0,
            0x7B84: 0x08,
            0x7BC2: 0xA1,
            0x7BC4: 0x08,
            0x7C02: 0xA2,
            0x7C04: 0x08,
        },
    )

    variant = identify_variant(
        data,
        "highlander_limited",
        "CANADA",
    )

    assert (
        variant.name
        == "Highlander Limited Variant C"
    )


def test_grand_highlander_variant_c_uses_exact_table():
    data = memory_with_values(
        0xB85,
        {
            0xB02: 0xD9,
            0xB04: 0x04,
            0xB42: 0xDA,
            0xB44: 0x04,
            0xB82: 0xDB,
            0xB84: 0x04,
        },
    )

    converted, variant = convert_region(
        data,
        "grand_highlander",
        "CANADA",
        "USA",
    )

    assert (
        variant.name
        == "Grand Highlander Variant C"
    )

    assert converted[0xB02] == 0xD6
    assert converted[0xB04] == 0x01
    assert converted[0xB42] == 0xD7
    assert converted[0xB44] == 0x01
    assert converted[0xB82] == 0xD8
    assert converted[0xB84] == 0x01


def test_rav4_canada_to_usa():
    data = memory_with_values(
        0x585,
        {
            0x502: 0xBF,
            0x504: 0x05,
            0x542: 0xC0,
            0x544: 0x05,
            0x582: 0xC1,
            0x584: 0x05,
        },
    )

    converted, _ = convert_region(
        data,
        "rav4",
        "CANADA",
        "USA",
    )

    assert converted[0x502] == 0xBE
    assert converted[0x504] == 0x01
    assert converted[0x542] == 0xBF
    assert converted[0x544] == 0x01
    assert converted[0x582] == 0xC0
    assert converted[0x584] == 0x01


def test_unknown_values_are_refused():
    data = bytes([0xFF] * 0xC05)

    with pytest.raises(
        ToyotaRH850ConversionError,
        match="No validated Toyota variant",
    ):
        convert_region(
            data,
            "tundra_gas",
            "CANADA",
            "USA",
        )
