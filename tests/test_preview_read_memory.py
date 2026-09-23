import hashlib
import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_PATH = ROOT / "preview.py"

spec = importlib.util.spec_from_file_location(
    "convertion_pro_preview",
    PREVIEW_PATH,
)

if spec is None or spec.loader is None:
    raise RuntimeError(
        "Unable to load preview.py for API tests."
    )

preview_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview_module)

app = preview_module.app


client = TestClient(app)


def read_memory():
    response = client.post(
        "/api/advanced/read-memory"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True

    return payload


def test_read_memory_returns_expected_metadata():
    payload = read_memory()

    assert payload["read_only"] is True
    assert payload["vehicle"] == "Jeep Wrangler 2012–2018"
    assert payload["memory_type"] == "EEPROM"
    assert payload["memory_size"] == 1024

    assert (
        payload["cluster_id"]
        == "SIM-JEEP-WRANGLER-2012-2018"
    )

    assert payload["cable"] == "CP-JEEP-004"

    assert payload["voltage"] == 12.4
    assert payload["current"] == 0.42
    assert payload["current_validated"] is False


def test_read_memory_returns_complete_memory_image():
    payload = read_memory()

    memory = bytes.fromhex(
        payload["data_hex"]
    )

    assert len(memory) == 1024
    assert len(payload["data_hex"]) == 2048

    assert memory[0x68] == 0x04
    assert memory[0x69] == 0x12

    assert memory[0x67] == 0xFF
    assert memory[0x6A] == 0xFF


def test_read_memory_sha256_matches_returned_data():
    payload = read_memory()

    memory = bytes.fromhex(
        payload["data_hex"]
    )

    expected_sha256 = hashlib.sha256(
        memory
    ).hexdigest()

    assert payload["sha256"] == expected_sha256


def test_read_memory_annotations_match_validated_offsets():
    payload = read_memory()

    offsets = {
        item["offset"]
        for item in payload["annotations"]
    }

    assert offsets == {0x68, 0x69}


def identify_cluster():
    response = client.post(
        "/api/advanced/identify-cluster"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True

    return payload


def test_identify_cluster_is_explicitly_simulated():
    payload = identify_cluster()

    assert (
        payload["identification_mode"]
        == "SIMULATED"
    )

    assert (
        payload["physical_identification"]
        is False
    )


def test_identify_cluster_matches_selected_profile():
    payload = identify_cluster()

    assert (
        payload["expected"]["cluster_id"]
        == "SIM-JEEP-WRANGLER-2012-2018"
    )

    assert (
        payload["detected"]["cluster_id"]
        == payload["expected"]["cluster_id"]
    )

    assert (
        payload["expected"]["cable"]
        == "CP-JEEP-004"
    )

    assert (
        payload["detected"]["cable"]
        == payload["expected"]["cable"]
    )

    validation = payload["validation"]

    assert validation["cluster_match"] is True
    assert validation["cable_match"] is True
    assert validation["voltage_valid"] is True
    assert validation["profile_match"] is True


def test_identify_cluster_returns_profile_information():
    payload = identify_cluster()

    assert payload["vehicle"] == {
        "make": "Jeep",
        "model": "Wrangler",
        "generation": "2012-2018",
    }

    assert payload["connection_method"] == "BENCH"

    assert (
        payload["expected"]["memory_type"]
        == "EEPROM"
    )

    assert (
        payload["expected"]["memory_size"]
        == 1024
    )


def test_identify_cluster_current_is_monitoring_only():
    payload = identify_cluster()

    assert payload["detected"]["voltage"] == 12.4
    assert payload["detected"]["current"] == 0.42

    assert (
        payload["validation"]["current_validated"]
        is False
    )
