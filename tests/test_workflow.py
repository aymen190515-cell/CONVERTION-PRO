import json

from convertion_pro.hardware.simulator import SimulatedProgrammer
from convertion_pro.core.workflow import ConversionWorkflow


def load_profile():
    with open(
        "vehicles/jeep/wrangler_2012_2018/profile.json",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def test_complete_simulated_conversion(tmp_path):
    hardware = SimulatedProgrammer()
    workflow = ConversionWorkflow(hardware, load_profile())

    safety = workflow.run_safety_check()
    assert safety.passed

    workflow.create_backup(str(tmp_path))
    assert workflow.detect_unit() == "KM"

    converted = workflow.prepare_synthetic_conversion("MI")
    assert b"UNIT=MI" in converted

    assert workflow.program_and_verify(converted)
    assert workflow.detect_unit() == "MI"


def test_write_is_blocked_without_backup():
    hardware = SimulatedProgrammer()
    workflow = ConversionWorkflow(hardware, load_profile())

    workflow.run_safety_check()

    try:
        workflow.program_and_verify(b"TEST")
    except RuntimeError as error:
        assert "backup" in str(error).lower()
    else:
        raise AssertionError("Unsafe write was not blocked.")
