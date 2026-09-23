from convertion_pro.core.jeep_wrangler import (
    OFFSET_68,
    OFFSET_69,
    changed_offsets,
    convert_km_to_miles,
    convert_miles_to_km,
)


def test_synthetic_dumps_are_same_size(
    synthetic_jeep_km_dump,
    synthetic_jeep_miles_dump,
):
    assert len(synthetic_jeep_km_dump) == 1024
    assert len(synthetic_jeep_miles_dump) == 1024


def test_synthetic_dumps_only_differ_at_unit_offsets(
    synthetic_jeep_km_dump,
    synthetic_jeep_miles_dump,
):
    assert changed_offsets(
        synthetic_jeep_km_dump,
        synthetic_jeep_miles_dump,
    ) == [OFFSET_68, OFFSET_69]


def test_km_to_miles_matches_expected_dump(
    synthetic_jeep_km_dump,
    synthetic_jeep_miles_dump,
):
    converted = convert_km_to_miles(
        synthetic_jeep_km_dump
    )

    assert converted == synthetic_jeep_miles_dump


def test_miles_to_km_matches_expected_dump(
    synthetic_jeep_km_dump,
    synthetic_jeep_miles_dump,
):
    converted = convert_miles_to_km(
        synthetic_jeep_miles_dump
    )

    assert converted == synthetic_jeep_km_dump


def test_km_to_miles_changes_only_0x68_and_0x69(
    synthetic_jeep_km_dump,
):
    converted = convert_km_to_miles(
        synthetic_jeep_km_dump
    )

    assert changed_offsets(
        synthetic_jeep_km_dump,
        converted,
    ) == [OFFSET_68, OFFSET_69]


def test_miles_to_km_changes_only_0x68_and_0x69(
    synthetic_jeep_miles_dump,
):
    converted = convert_miles_to_km(
        synthetic_jeep_miles_dump
    )

    assert changed_offsets(
        synthetic_jeep_miles_dump,
        converted,
    ) == [OFFSET_68, OFFSET_69]
