from convertion_pro.core.vehicle_catalog import (
    get_make,
    get_vehicle,
    load_vehicle_catalog,
)


def test_catalog_loads():
    catalog = load_vehicle_catalog()

    assert catalog["schema_version"] == 1
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
