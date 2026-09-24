"""
Toyota / Lexus RH850 R7F701401 regional conversion rules.

Source data describes Canadian -> USA conversions.

Safety philosophy:
- identify an exact known variant before conversion
- verify every expected Canadian byte before changing anything
- modify only explicitly validated offsets
- never guess between variants
"""

from dataclasses import dataclass


class ToyotaRH850ConversionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ToyotaVariant:
    name: str
    changes: dict[int, tuple[int, int]]


# ------------------------------------------------------------------
# TOYOTA
# ------------------------------------------------------------------

TOYOTA_RULES: dict[str, tuple[ToyotaVariant, ...]] = {

    "tundra_gas": (
        ToyotaVariant(
            name="Tundra Gas",
            changes={
                0xB82: (0xDC, 0xDA),
                0xB84: (0x05, 0x03),
                0xBC2: (0xDD, 0xDB),
                0xBC4: (0x05, 0x03),
                0xC02: (0xDE, 0xDC),
                0xC04: (0x05, 0x03),
            },
        ),
    ),

    "tundra_hybrid": (
        ToyotaVariant(
            name="Tundra Hybrid",
            changes={
                0xB82: (0xDD, 0xDB),
                0xB84: (0x06, 0x04),
                0xBC2: (0xDE, 0xDC),
                0xBC4: (0x06, 0x04),
                0xC02: (0xDF, 0xDD),
                0xC04: (0x06, 0x04),
            },
        ),
    ),

    "venza_hybrid": (
        ToyotaVariant(
            name="Venza Hybrid",
            changes={
                0x8C2: (0xD0, 0xCF),
                0x8C4: (0x04, 0x03),
                0x902: (0xD1, 0xD0),
                0x904: (0x04, 0x03),
                0x942: (0xD2, 0xD1),
                0x944: (0x04, 0x03),
            },
        ),
    ),

    "highlander_limited": (
        ToyotaVariant(
            name="Highlander Limited Variant A",
            changes={
                0x7B82: (0x9E, 0x9D),
                0x7B84: (0x06, 0x05),
                0x7BC2: (0x9F, 0x9E),
                0x7BC4: (0x06, 0x05),
                0x7C02: (0xA0, 0x9F),
                0x7C04: (0x06, 0x05),
            },
        ),
        ToyotaVariant(
            name="Highlander Limited Variant B",
            changes={
                0x8C2: (0xD4, 0xD3),
                0x8C4: (0x08, 0x07),
                0x902: (0xD5, 0xD4),
                0x904: (0x08, 0x07),
                0x942: (0xD6, 0xD5),
                0x944: (0x08, 0x07),
            },
        ),
        ToyotaVariant(
            name="Highlander Limited Variant C",
            changes={
                0x7B82: (0xA0, 0x9F),
                0x7B84: (0x08, 0x07),
                0x7BC2: (0xA1, 0xA0),
                0x7BC4: (0x08, 0x07),
                0x7C02: (0xA2, 0xA1),
                0x7C04: (0x08, 0x07),
            },
        ),
        ToyotaVariant(
            name="Highlander Limited Variant D",
            changes={
                0x8C2: (0xD2, 0xD1),
                0x8C4: (0x06, 0x05),
                0x902: (0xD3, 0xD2),
                0x904: (0x06, 0x05),
                0x942: (0xD4, 0xD3),
                0x944: (0x06, 0x05),
            },
        ),
    ),

    "grand_highlander": (
        ToyotaVariant(
            name="Grand Highlander Variant A",
            changes={
                0xB04: (0x02, 0x06),
                0xB44: (0x02, 0x06),
                0xB84: (0x02, 0x06),
            },
        ),
        ToyotaVariant(
            name="Grand Highlander Variant B",
            changes={
                0xB02: (0xD8, 0xD6),
                0xB04: (0x03, 0x01),
                0xB42: (0xD9, 0xD7),
                0xB44: (0x03, 0x01),
                0xB82: (0xDA, 0xD8),
                0xB84: (0x03, 0x01),
            },
        ),
        ToyotaVariant(
            name="Grand Highlander Variant C",
            changes={
                0xB02: (0xD9, 0xD6),
                0xB04: (0x04, 0x01),
                0xB42: (0xDA, 0xD7),
                0xB44: (0x04, 0x01),
                0xB82: (0xDB, 0xD8),
                0xB84: (0x04, 0x01),
            },
        ),
    ),

    "sequoia_hybrid": (
        ToyotaVariant(
            name="Sequoia Hybrid",
            changes={
                0xB82: (0xD8, 0xD7),
                0xB84: (0x01, 0x00),
                0xBC2: (0xD9, 0xD8),
                0xBC4: (0x01, 0x00),
                0xC02: (0xDA, 0xD9),
                0xC04: (0x01, 0x00),
            },
        ),
    ),

    "corolla": (
        ToyotaVariant(
            name="Corolla",
            changes={
                0xB04: (0x84, 0x83),
                0xB44: (0x84, 0x83),
                0xB84: (0x84, 0x83),
            },
        ),
    ),

    "sienna": (
        ToyotaVariant(
            name="Sienna",
            changes={
                0x8C2: (0xD4, 0xDE),
                0x8C4: (0x08, 0x12),
                0x902: (0xD5, 0xDF),
                0x904: (0x08, 0x12),
                0x942: (0xD6, 0xE0),
                0x944: (0x08, 0x12),
            },
        ),
    ),

    "crown_signia": (
        ToyotaVariant(
            name="Crown Signia",
            changes={
                0xB04: (0xC6, 0xCA),
                0xB44: (0xC6, 0xCA),
                0xB84: (0xC6, 0xCA),
            },
        ),
    ),

    "rav4": (
        ToyotaVariant(
            name="RAV4",
            changes={
                0x502: (0xBF, 0xBE),
                0x504: (0x05, 0x01),
                0x542: (0xC0, 0xBF),
                0x544: (0x05, 0x01),
                0x582: (0xC1, 0xC0),
                0x584: (0x05, 0x01),
            },
        ),
    ),
}


def get_variants(model_key: str) -> tuple[ToyotaVariant, ...]:
    try:
        return TOYOTA_RULES[model_key]
    except KeyError as error:
        raise ToyotaRH850ConversionError(
            f"Unsupported Toyota model: {model_key}"
        ) from error


def matching_canadian_variants(
    data: bytes,
    model_key: str,
) -> list[ToyotaVariant]:

    variants = get_variants(model_key)
    matches = []

    for variant in variants:
        if all(
            offset < len(data)
            and data[offset] == canadian
            for offset, (canadian, _usa)
            in variant.changes.items()
        ):
            matches.append(variant)

    return matches


def matching_usa_variants(
    data: bytes,
    model_key: str,
) -> list[ToyotaVariant]:

    variants = get_variants(model_key)
    matches = []

    for variant in variants:
        if all(
            offset < len(data)
            and data[offset] == usa
            for offset, (_canadian, usa)
            in variant.changes.items()
        ):
            matches.append(variant)

    return matches


def identify_variant(
    data: bytes,
    model_key: str,
    source_region: str,
) -> ToyotaVariant:

    region = source_region.upper().strip()

    if region == "CANADA":
        matches = matching_canadian_variants(
            data,
            model_key,
        )
    elif region == "USA":
        matches = matching_usa_variants(
            data,
            model_key,
        )
    else:
        raise ToyotaRH850ConversionError(
            "Unsupported source region. "
            "Expected CANADA or USA."
        )

    if not matches:
        raise ToyotaRH850ConversionError(
            "No validated Toyota variant matches "
            "the loaded memory data."
        )

    if len(matches) > 1:
        raise ToyotaRH850ConversionError(
            "Toyota variant detection is ambiguous."
        )

    return matches[0]


def convert_region(
    data: bytes,
    model_key: str,
    source_region: str,
    target_region: str,
) -> tuple[bytes, ToyotaVariant]:

    source = source_region.upper().strip()
    target = target_region.upper().strip()

    if source == target:
        raise ToyotaRH850ConversionError(
            "Source and target regions are identical."
        )

    if {source, target} != {"CANADA", "USA"}:
        raise ToyotaRH850ConversionError(
            "Supported Toyota regional conversion is "
            "CANADA <-> USA."
        )

    variant = identify_variant(
        data,
        model_key,
        source,
    )

    result = bytearray(data)

    for offset, (
        canadian,
        usa,
    ) in variant.changes.items():

        expected = (
            canadian
            if source == "CANADA"
            else usa
        )

        replacement = (
            usa
            if target == "USA"
            else canadian
        )

        if result[offset] != expected:
            raise ToyotaRH850ConversionError(
                f"Unexpected value at 0x{offset:X}."
            )

        result[offset] = replacement

    return bytes(result), variant
