import json
from pathlib import Path

import pytest

from convertion_pro.core.workflow import (
    ConversionWorkflow,
)
from convertion_pro.hardware.simulator import (
    SimulatedProgrammer,
)


ROOT = Path(__file__).resolve().parents[1]

PROFILE_PATH = (
    ROOT
    / "vehicles"
    / "jeep"
    / "wrangler_2012_2018"
    / "profile.json"
)


def make_workflow():
    profile = json.loads(
        PROFILE_PATH.read_text(
            encoding="utf-8"
        )
    )

    return ConversionWorkflow(
        SimulatedProgrammer(),
        profile,
    )


def make_km_memory():
    memory = bytearray([0xFF] * 1024)

    memory[0x68] = 0x04
    memory[0x69] = 0x12

    return bytes(memory)


def test_file_conversion_km_to_miles():
    workflow = make_workflow()
    original = make_km_memory()

    converted = workflow.convert_file_data(
        original,
        "KM",
        "MI",
    )

    assert len(converted) == 1024

    assert converted[0x68] == 0x02
    assert converted[0x69] == 0x0E

    changed = [
        index
        for index, (before, after)
        in enumerate(zip(original, converted))
        if before != after
    ]

    assert changed == [0x68, 0x69]


def test_file_conversion_miles_to_km():
    workflow = make_workflow()

    memory = bytearray([0xFF] * 1024)

    memory[0x68] = 0x02
    memory[0x69] = 0x0E

    original = bytes(memory)

    converted = workflow.convert_file_data(
        original,
        "MI",
        "KM",
    )

    assert converted[0x68] == 0x04
    assert converted[0x69] == 0x12


def test_file_conversion_does_not_modify_original():
    workflow = make_workflow()

    original = make_km_memory()

    workflow.convert_file_data(
        original,
        "KM",
        "MI",
    )

    assert original[0x68] == 0x04
    assert original[0x69] == 0x12


def test_file_conversion_rejects_wrong_size():
    workflow = make_workflow()

    invalid = bytes([0xFF] * 512)

    with pytest.raises(
        RuntimeError,
        match="EEPROM size does not match",
    ):
        workflow.convert_file_data(
            invalid,
            "KM",
            "MI",
        )


def test_word_byte_swap_is_reversible():
    from convertion_pro.core.memory_layout import (
        swap_word_bytes,
    )

    original = bytes([
        0x12, 0x34,
        0x56, 0x78,
        0xAB, 0xCD,
    ])

    swapped = swap_word_bytes(original)

    assert swapped == bytes([
        0x34, 0x12,
        0x78, 0x56,
        0xCD, 0xAB,
    ])

    assert swap_word_bytes(swapped) == original


def test_x8_is_normalized_to_x16():
    from convertion_pro.core.memory_layout import (
        to_canonical_x16,
        swap_word_bytes,
    )

    x16 = make_km_memory()
    x8 = swap_word_bytes(x16)

    normalized = to_canonical_x16(
        x8,
        "X8",
    )

    assert normalized == x16


def test_file_conversion_supports_x8():
    from convertion_pro.core.memory_layout import (
        swap_word_bytes,
    )

    workflow = make_workflow()

    x16_km = make_km_memory()
    x8_km = swap_word_bytes(x16_km)

    converted_x8 = workflow.convert_file_data(
        x8_km,
        "KM",
        "MI",
        memory_organization="X8",
    )

    # X8 layout must remain X8.
    assert converted_x8[0x68] == 0x0E
    assert converted_x8[0x69] == 0x02

    # Normalizing the result must produce the
    # already-validated X16 Miles representation.
    normalized = swap_word_bytes(
        converted_x8
    )

    assert normalized[0x68] == 0x02
    assert normalized[0x69] == 0x0E


def test_x8_conversion_round_trip():
    from convertion_pro.core.memory_layout import (
        swap_word_bytes,
    )

    workflow = make_workflow()

    x16_original = make_km_memory()
    x8_original = swap_word_bytes(
        x16_original
    )

    miles_x8 = workflow.convert_file_data(
        x8_original,
        "KM",
        "MI",
        memory_organization="X8",
    )

    restored_x8 = workflow.convert_file_data(
        miles_x8,
        "MI",
        "KM",
        memory_organization="X8",
    )

    assert restored_x8 == x8_original


def test_detect_memory_organization_x8():
    from convertion_pro.core.memory_layout import (
        detect_memory_organization,
    )

    memory = bytearray([0xFF] * 1024)

    # Readable structure directly in raw representation.
    memory[0x120:0x127] = b"CONTACT"
    memory[0x140:0x146] = b"DEALER"

    result = detect_memory_organization(
        bytes(memory)
    )

    assert result["detected"] is True
    assert result["organization"] == "X8"
    assert result["confidence"] == "HIGH"
    assert "CONTACT" in result["raw_matches"]
    assert "DEALER" in result["raw_matches"]


def test_detect_memory_organization_x16():
    from convertion_pro.core.memory_layout import (
        detect_memory_organization,
        swap_word_bytes,
    )

    x8 = bytearray([0xFF] * 1024)

    x8[0x120:0x127] = b"CONTACT"
    x8[0x140:0x146] = b"DEALER"

    # Produce the corresponding pair-swapped X16 dump.
    x16 = swap_word_bytes(
        bytes(x8)
    )

    result = detect_memory_organization(
        x16
    )

    assert result["detected"] is True
    assert result["organization"] == "X16"
    assert result["confidence"] == "HIGH"
    assert "CONTACT" in result["swapped_matches"]
    assert "DEALER" in result["swapped_matches"]


def test_detect_memory_organization_ambiguous():
    from convertion_pro.core.memory_layout import (
        detect_memory_organization,
    )

    memory = bytes([0xFF] * 1024)

    result = detect_memory_organization(
        memory
    )

    assert result["detected"] is False
    assert result["organization"] is None
    assert result["confidence"] == "AMBIGUOUS"


def test_detect_memory_organization_rejects_wrong_size():
    from convertion_pro.core.memory_layout import (
        detect_memory_organization,
        MemoryOrganizationError,
    )

    import pytest

    with pytest.raises(
        MemoryOrganizationError
    ):
        detect_memory_organization(
            bytes([0xFF] * 512)
        )
