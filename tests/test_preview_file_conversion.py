import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_PATH = ROOT / "preview.py"

spec = importlib.util.spec_from_file_location(
    "convertion_pro_preview_file",
    PREVIEW_PATH,
)

preview_module = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(preview_module)

client = TestClient(preview_module.app)


def make_km_memory():
    memory = bytearray([0xFF] * 1024)
    memory[0x68] = 0x04
    memory[0x69] = 0x12
    return bytes(memory)


def convert(
    data,
    source="KM",
    target="MI",
    organization="X16",
):
    return client.post(
        (
            "/api/file/convert"
            f"?source_unit={source}"
            f"&target_unit={target}"
            f"&memory_organization={organization}"
        ),
        content=data,
        headers={
            "Content-Type":
                "application/octet-stream"
        },
    )


def test_file_api_converts_real_request_bytes():
    original = make_km_memory()

    response = convert(original)

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["verified"] is True
    assert data["source"] == "FILE"

    converted = bytes.fromhex(
        data["data_hex"]
    )

    assert len(converted) == 1024
    assert converted[0x68] == 0x02
    assert converted[0x69] == 0x0E


def test_file_api_reports_exact_changes():
    response = convert(
        make_km_memory()
    )

    data = response.json()

    assert data["changed_byte_count"] == 2

    assert [
        item["offset"]
        for item in data["changes"]
    ] == [0x68, 0x69]

    assert data["changes"][0]["before_hex"] == "04"
    assert data["changes"][0]["after_hex"] == "02"

    assert data["changes"][1]["before_hex"] == "12"
    assert data["changes"][1]["after_hex"] == "0E"


def test_file_api_is_explicitly_hardware_free():
    response = convert(
        make_km_memory()
    )

    data = response.json()

    assert (
        data["physical_cluster_required"]
        is False
    )

    assert data["hardware_access"] is False
    assert data["profile_source"] == "USER_SELECTED"


def test_file_api_round_trip():
    original = make_km_memory()

    to_miles = convert(
        original,
        "KM",
        "MI",
    ).json()

    miles_data = bytes.fromhex(
        to_miles["data_hex"]
    )

    back_to_km = convert(
        miles_data,
        "MI",
        "KM",
    ).json()

    restored = bytes.fromhex(
        back_to_km["data_hex"]
    )

    assert restored == original


def test_file_api_rejects_wrong_size():
    response = convert(
        bytes([0xFF] * 512)
    )

    data = response.json()

    assert data["success"] is False
    assert data["verified"] is False

    assert (
        "EEPROM size does not match"
        in data["detail"]
    )


def test_file_api_rejects_empty_file():
    response = convert(b"")

    data = response.json()

    assert data["success"] is False

    assert (
        "Uploaded file is empty"
        in data["detail"]
    )



def test_file_api_supports_x8_organization():
    from convertion_pro.core.memory_layout import (
        swap_word_bytes,
    )

    x16_km = make_km_memory()
    x8_km = swap_word_bytes(x16_km)

    response = convert(
        x8_km,
        "KM",
        "MI",
        organization="X8",
    )

    data = response.json()

    assert data["success"] is True
    assert data["verified"] is True
    assert data["memory_organization"] == "X8"

    converted = bytes.fromhex(
        data["data_hex"]
    )

    assert converted[0x68] == 0x0E
    assert converted[0x69] == 0x02


def test_file_api_x8_round_trip():
    from convertion_pro.core.memory_layout import (
        swap_word_bytes,
    )

    x8_original = swap_word_bytes(
        make_km_memory()
    )

    miles = convert(
        x8_original,
        "KM",
        "MI",
        organization="X8",
    ).json()

    miles_data = bytes.fromhex(
        miles["data_hex"]
    )

    restored = convert(
        miles_data,
        "MI",
        "KM",
        organization="X8",
    ).json()

    assert bytes.fromhex(
        restored["data_hex"]
    ) == x8_original


def detect(data):
    return client.post(
        "/api/file/detect",
        content=data,
        headers={
            "Content-Type":
                "application/octet-stream"
        },
    )


def test_file_detection_api_detects_x8():
    memory = bytearray([0xFF] * 1024)

    memory[0x120:0x127] = b"CONTACT"
    memory[0x140:0x146] = b"DEALER"

    data = detect(
        bytes(memory)
    ).json()

    assert data["success"] is True
    assert data["detected"] is True
    assert (
        data["memory_organization"]
        == "X8"
    )
    assert data["confidence"] == "HIGH"


def test_file_detection_api_detects_x16():
    from convertion_pro.core.memory_layout import (
        swap_word_bytes,
    )

    x8 = bytearray([0xFF] * 1024)

    x8[0x120:0x127] = b"CONTACT"
    x8[0x140:0x146] = b"DEALER"

    x16 = swap_word_bytes(
        bytes(x8)
    )

    data = detect(x16).json()

    assert data["success"] is True
    assert data["detected"] is True
    assert (
        data["memory_organization"]
        == "X16"
    )
    assert data["confidence"] == "HIGH"


def test_file_detection_api_reports_ambiguous():
    data = detect(
        bytes([0xFF] * 1024)
    ).json()

    assert data["success"] is True
    assert data["detected"] is False
    assert (
        data["memory_organization"]
        is None
    )
    assert (
        data["confidence"]
        == "AMBIGUOUS"
    )


def test_file_detection_api_rejects_wrong_size():
    data = detect(
        bytes([0xFF] * 512)
    ).json()

    assert data["success"] is False
    assert data["detected"] is False
    assert data["confidence"] == "ERROR"


def test_file_convert_auto_detects_x8():
    memory = bytearray([0xFF] * 1024)

    memory[0x120:0x127] = b"CONTACT"
    memory[0x140:0x146] = b"DEALER"

    # Give the validated conversion bytes valid values.
    memory[0x68] = 0x04
    memory[0x69] = 0x12

    response = convert(
        bytes(memory),
        "KM",
        "MI",
        organization="AUTO",
    )

    data = response.json()

    assert data["success"] is True
    assert data["memory_organization"] == "X8"
    assert data["organization_source"] == "AUTO_DETECTED"
    assert data["detection_confidence"] == "HIGH"


def test_file_convert_auto_detects_x16():
    from convertion_pro.core.memory_layout import (
        swap_word_bytes,
    )

    x8 = bytearray([0xFF] * 1024)

    x8[0x120:0x127] = b"CONTACT"
    x8[0x140:0x146] = b"DEALER"

    # X16 canonical values after swapping.
    x8[0x68] = 0x12
    x8[0x69] = 0x04

    x16 = swap_word_bytes(
        bytes(x8)
    )

    response = convert(
        x16,
        "KM",
        "MI",
        organization="AUTO",
    )

    data = response.json()

    assert data["success"] is True
    assert data["memory_organization"] == "X16"
    assert data["organization_source"] == "AUTO_DETECTED"
    assert data["detection_confidence"] == "HIGH"


def test_file_convert_auto_refuses_ambiguous():
    response = convert(
        bytes([0xFF] * 1024),
        "KM",
        "MI",
        organization="AUTO",
    )

    data = response.json()

    assert data["success"] is False

    assert (
        "could not be detected"
        in data["detail"]
    )


def make_toyota_memory(
    size: int,
    values: dict[int, int],
) -> bytes:
    data = bytearray([0xFF] * size)

    for offset, value in values.items():
        data[offset] = value

    return bytes(data)


def convert_toyota(
    body: bytes,
    vehicle_key: str,
    source: str = "CANADA",
    target: str = "USA",
):
    return client.post(
        "/api/file/convert",
        params={
            "source_unit": source,
            "target_unit": target,
            "memory_organization": "AUTO",
            "vehicle_key": vehicle_key,
        },
        content=body,
        headers={
            "Content-Type":
                "application/octet-stream"
        },
    )


def test_toyota_rav4_api_conversion():
    original = make_toyota_memory(
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

    response = convert_toyota(
        original,
        "toyota_rav4",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["verified"] is True
    assert data["hardware_access"] is False
    assert data["vehicle"]["make"] == "Toyota"
    assert data["vehicle"]["model"] == "RAV4"
    assert data["processor"] == "RH850 R7F701401"
    assert data["changed_byte_count"] == 6

    offsets = {
        item["offset"]
        for item in data["changes"]
    }

    assert offsets == {
        0x502,
        0x504,
        0x542,
        0x544,
        0x582,
        0x584,
    }


def test_toyota_tundra_gas_api_conversion():
    original = make_toyota_memory(
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

    response = convert_toyota(
        original,
        "toyota_tundra_gas",
    )

    data = response.json()

    assert data["success"] is True
    assert data["vehicle"]["model"] == "Tundra Gas"
    assert data["changed_byte_count"] == 6


def test_toyota_highlander_variant_auto_detect():
    original = make_toyota_memory(
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

    response = convert_toyota(
        original,
        "toyota_highlander_limited",
    )

    data = response.json()

    assert data["success"] is True
    assert (
        data["variant"]
        == "Highlander Limited Variant C"
    )


def test_toyota_rejects_wrong_model_values():
    original = bytes([0xFF] * 0xC05)

    response = convert_toyota(
        original,
        "toyota_tundra_gas",
    )

    data = response.json()

    assert data["success"] is False
    assert data["verified"] is False

    assert (
        "No validated Toyota variant matches"
        in data["detail"]
    )
