import json
from pathlib import Path
import shutil
import subprocess

import pytest

from convertion_pro.core.vehicle_catalog import (
    VehicleCatalogError,
    get_make,
    get_vehicle,
    load_vehicle_catalog,
)


def test_catalog_loads():
    catalog = load_vehicle_catalog()

    assert catalog["schema_version"] == 2
    assert len(catalog["makes"]) == 2


def test_jeep_profile_is_registered():
    catalog = load_vehicle_catalog()

    jeep = get_vehicle(
        catalog,
        "jeep_wrangler_2012_2018",
    )

    assert jeep["conversion"]["type"] == "UNIT"
    assert jeep["hardware"][
        "physical_workflow_enabled"
    ] is True

    assert jeep["profile_path"] == (
        "vehicles/jeep/"
        "wrangler_2012_2018/profile.json"
    )


def test_toyota_rh850_is_file_only_for_now():
    catalog = load_vehicle_catalog()

    tundra = get_vehicle(
        catalog,
        "toyota_tundra_gas",
    )

    assert tundra["conversion"]["type"] == "REGION"

    assert tundra["hardware"][
        "physical_workflow_enabled"
    ] is False

    assert tundra["hardware"]["processor"] == (
        "RH850 R7F701401"
    )


def test_make_lookup():
    catalog = load_vehicle_catalog()

    toyota = get_make(
        catalog,
        "toyota",
    )

    assert toyota["label"] == "Toyota"
    assert len(toyota["vehicles"]) == 10


def test_connection_guide_preserves_vehicle_behavior():
    catalog = load_vehicle_catalog()
    jeep = get_vehicle(catalog, "jeep_wrangler_2012_2018")
    assert jeep["connection_guide"] == {
        "eyebrow": "JEEP · WRANGLER 2012–2018",
        "cluster_lines": ["JEEP", "WRANGLER"],
        "method": "Bench",
        "cable": "CP-JEEP-004",
        "supply": "12.0 V",
        "power_state": "OFF",
        "steps": [
            "Connect CP-JEEP-004 to the instrument cluster.",
            "Connect the universal end to the programmer.",
            "Keep cluster power OFF until verification.",
        ],
        "proceed_enabled": True,
        "blocked_reason": None,
    }
    for vehicle in get_make(catalog, "toyota")["vehicles"]:
        guide = vehicle["connection_guide"]
        assert guide == {
            "eyebrow": "TOYOTA · " + vehicle["label"].upper(),
            "cluster_lines": ["TOYOTA", vehicle["label"].upper()],
            "method": "RH850",
            "cable": "NOT CONFIGURED",
            "supply": "NOT CONFIGURED",
            "power_state": "OFF",
            "steps": [
                "Processor profile: RH850 R7F701401.",
                "Toyota hardware communication profile is not implemented yet.",
                "Connection pinout, supply and access method must be validated before programming.",
            ],
            "proceed_enabled": False,
            "blocked_reason": "RH850 DRIVER REQUIRED",
        }
        assert vehicle["hardware"]["physical_workflow_enabled"] is False


@pytest.mark.parametrize("field,value", [
    ("method", ""), ("cable", None), ("supply", 12),
    ("power_state", False), ("eyebrow", ""),
    ("steps", []), ("steps", [1]), ("cluster_lines", "Jeep"),
    ("proceed_enabled", "false"), ("blocked_reason", "blocked"),
])
def test_invalid_connection_guide_is_rejected(tmp_path, field, value):
    catalog = load_vehicle_catalog()
    catalog["makes"][0]["vehicles"][0]["connection_guide"][field] = value
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(catalog))
    with pytest.raises(VehicleCatalogError):
        load_vehicle_catalog(path)


@pytest.mark.parametrize("change", ["missing", "enable", "reason"])
def test_disabled_hardware_guide_validation(tmp_path, change):
    catalog = load_vehicle_catalog()
    vehicle = catalog["makes"][1]["vehicles"][0]
    if change == "missing":
        del vehicle["connection_guide"]
    elif change == "enable":
        vehicle["connection_guide"]["proceed_enabled"] = True
        vehicle["connection_guide"]["blocked_reason"] = None
    else:
        vehicle["connection_guide"]["blocked_reason"] = None
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(catalog))
    with pytest.raises(VehicleCatalogError):
        load_vehicle_catalog(path)


def test_preview_connection_guide_renders_catalog_data():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is required to exercise the guide renderer")
    source = (Path(__file__).resolve().parents[1] / "preview.py").read_text()
    mapping = source.split("const VEHICLE_CATALOG = {};", 1)[1].split(
        "const RECENT_VEHICLES_STORAGE_KEY", 1
    )[0]
    function = source.split("function openConnectionGuide(){", 1)[1].split(
        "function openFileConversion(){", 1
    )[0]
    catalog = load_vehicle_catalog()
    # An unknown make ensures rendering does not depend on Jeep/Toyota keys.
    generic = json.loads(json.dumps(catalog["makes"][0]))
    generic["key"] = "custom"
    generic["vehicles"][0]["key"] = "custom_vehicle"
    generic["vehicles"][0]["connection_guide"]["method"] = "Custom method"
    catalog["makes"].append(generic)
    script = '''
const assert = require("node:assert/strict");
class Element {
    constructor(){ this.children = []; this.textContent = ""; }
    replaceChildren(){ this.children = []; }
    appendChild(child){ this.children.push(child); }
}
const elements = {};
const document = {
    getElementById: id => elements[id] ||= new Element(),
    createElement: tag => Object.assign(new Element(), {tag}),
    createTextNode: text => ({textContent: text})
};
let selectedVehicle;
const updateSelectedVehicle = () => {};
const rememberSelectedVehicle = () => {};
const show = screen => assert.equal(screen, "guide");
const VEHICLE_CATALOG = {};
const VEHICLE_CATALOG_SOURCE = CATALOG;
MAPPING
function openConnectionGuide(){ FUNCTION
for(const vehicles of Object.values(VEHICLE_CATALOG)){
    for(const vehicle of vehicles){
        selectedVehicle = vehicle;
        openConnectionGuide();
        const guide = vehicle.connectionGuide;
        for(const [id, field] of [
            ["guideVehicleEyebrow", "eyebrow"],
            ["guideConnectionMethod", "method"],
            ["guideRequiredCable", "cable"],
            ["guideSupply", "supply"],
            ["guidePowerState", "power_state"]
        ]) assert.equal(elements[id].textContent, guide[field]);
        assert.deepEqual(elements.guideClusterScreen.children
            .filter(child => child.tag !== "br")
            .map(child => child.textContent), guide.cluster_lines);
        assert.deepEqual(elements.guideSteps.children.map((item, index) => {
            assert.equal(item.children[0].textContent, String(index + 1));
            assert.equal(item.children[0].className, "num");
            return item.children[1].textContent.trim();
        }), guide.steps);
        assert.equal(elements.guideProceedButton.disabled, !guide.proceed_enabled);
        assert.equal(elements.guideProceedButton.textContent,
            guide.proceed_enabled ? "Proceed →" : guide.blocked_reason);
    }
}
'''
    script = script.replace("CATALOG;", json.dumps(catalog) + ";")
    script = script.replace("MAPPING", mapping).replace("FUNCTION", function)
    subprocess.run([node, "-e", script], check=True, capture_output=True, text=True)


def test_legacy_catalog_without_guides_remains_readable(tmp_path):
    catalog = load_vehicle_catalog()
    catalog["schema_version"] = 1
    for make in catalog["makes"]:
        for vehicle in make["vehicles"]:
            del vehicle["connection_guide"]
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(catalog))
    loaded = load_vehicle_catalog(path)
    assert loaded["schema_version"] == 1
    for make in loaded["makes"]:
        for vehicle in make["vehicles"]:
            guide = vehicle["connection_guide"]
            assert guide["proceed_enabled"] is False
            assert guide["blocked_reason"] == "CONNECTION GUIDE REQUIRED"
            assert guide["power_state"] == "OFF"
            for field in ("method", "cable", "supply"):
                assert guide[field] == "NOT CONFIGURED"
            original = get_vehicle(catalog, vehicle["key"])
            assert vehicle["hardware"] == original["hardware"]
    # Normalization never rewrites the user's legacy file.
    assert json.loads(path.read_text()) == catalog


def test_legacy_catalog_with_explicit_guides_preserves_them(tmp_path):
    catalog = load_vehicle_catalog()
    catalog["schema_version"] = 1
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps(catalog))
    assert load_vehicle_catalog(path) == catalog


@pytest.mark.parametrize("version", [0, 3, "2", None])
def test_unsupported_catalog_version_is_rejected(tmp_path, version):
    catalog = load_vehicle_catalog()
    catalog["schema_version"] = version
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(catalog))
    with pytest.raises(VehicleCatalogError, match="Unsupported"):
        load_vehicle_catalog(path)
