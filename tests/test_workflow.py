import json

from convertion_pro.hardware.simulator import SimulatedProgrammer
from convertion_pro.core.workflow import ConversionWorkflow


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


def test_complete_simulated_hardware_workflow(
    tmp_path,
    synthetic_jeep_km_dump,
):
    hardware = make_programmer(
        synthetic_jeep_km_dump
    )

    workflow = ConversionWorkflow(
        hardware,
        load_profile(),
    )

    safety = workflow.run_safety_check()

    assert safety.passed

    backup = workflow.create_backup(
        str(tmp_path)
    )

    assert backup.exists()

    assert (
        backup.read_bytes()
        == synthetic_jeep_km_dump
    )


def test_write_is_blocked_without_backup(
    synthetic_jeep_km_dump,
):
    hardware = make_programmer(
        synthetic_jeep_km_dump
    )

    workflow = ConversionWorkflow(
        hardware,
        load_profile(),
    )

    workflow.run_safety_check()

    try:
        workflow.program_and_verify(
            synthetic_jeep_km_dump
        )

    except RuntimeError as error:
        assert "backup" in str(error).lower()

    else:
        raise AssertionError(
            "Unsafe write was not blocked."
        )
