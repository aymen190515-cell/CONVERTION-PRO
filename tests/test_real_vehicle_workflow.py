import json

from convertion_pro.core.workflow import ConversionWorkflow
from convertion_pro.hardware.simulator import SimulatedProgrammer


def load_profile():
    with open(
        "vehicles/jeep/wrangler_2012_2018/profile.json",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def make_programmer(memory: bytes):
    hardware = SimulatedProgrammer()
    hardware.memory = bytearray(memory)
    return hardware


def test_complete_jeep_km_to_miles_workflow(
    tmp_path,
    synthetic_jeep_km_dump,
    synthetic_jeep_miles_dump,
):
    hardware = make_programmer(
        synthetic_jeep_km_dump
    )

    workflow = ConversionWorkflow(
        hardware,
        load_profile(),
    )

    result = workflow.convert_and_program(
        source_unit="KM",
        target_unit="MI",
        backup_directory=str(tmp_path),
    )

    assert result.verified is True

    assert (
        hardware.read_memory()
        == synthetic_jeep_miles_dump
    )

    assert (
        result.backup_path.read_bytes()
        == synthetic_jeep_km_dump
    )

    assert (
        result.converted_data
        == synthetic_jeep_miles_dump
    )


def test_complete_jeep_miles_to_km_workflow(
    tmp_path,
    synthetic_jeep_km_dump,
    synthetic_jeep_miles_dump,
):
    hardware = make_programmer(
        synthetic_jeep_miles_dump
    )

    workflow = ConversionWorkflow(
        hardware,
        load_profile(),
    )

    result = workflow.convert_and_program(
        source_unit="MI",
        target_unit="KM",
        backup_directory=str(tmp_path),
    )

    assert result.verified is True

    assert (
        hardware.read_memory()
        == synthetic_jeep_km_dump
    )

    assert (
        result.backup_path.read_bytes()
        == synthetic_jeep_miles_dump
    )

    assert (
        result.converted_data
        == synthetic_jeep_km_dump
    )


def test_real_write_blocked_if_safety_not_run(
    synthetic_jeep_km_dump,
):
    hardware = make_programmer(
        synthetic_jeep_km_dump
    )

    workflow = ConversionWorkflow(
        hardware,
        load_profile(),
    )

    converted = bytearray(
        synthetic_jeep_km_dump
    )

    converted[0x68] -= 2
    converted[0x69] -= 4

    try:
        workflow.program_and_verify(
            bytes(converted)
        )

    except RuntimeError as error:
        assert "safety" in str(error).lower()

    else:
        raise AssertionError(
            "Unsafe EEPROM write was not blocked."
        )
