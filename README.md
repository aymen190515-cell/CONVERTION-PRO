# CONVERTION-PRO

Professional automotive instrument-cluster conversion platform.

## Install and run locally (Windows / PowerShell)

Use Python 3.12 or newer. Run these commands from the repository root
(the directory containing `pyproject.toml`):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pip check
```

If `python` opens the Microsoft Store, use `py -3.12` or the full path to
an installed Python executable for the first command. Environment activation
is not required. For running without the test tools, install `-e .` instead.
The project declares the desktop and preview dependencies in `pyproject.toml`.

Start the web preview:

```powershell
.\.venv\Scripts\python.exe preview.py
```

Open <http://127.0.0.1:8000> in your browser. The server listens only on this
computer. Stop it with Ctrl+C. If port 8000 is occupied, use:

```powershell
.\.venv\Scripts\python.exe -m uvicorn preview:app --host 127.0.0.1 --port 8001
```

Start the desktop interface separately:

```powershell
.\.venv\Scripts\python.exe main.py
```

Keep the working directory at the repository root: profiles, assets and runtime
data use repository-relative paths. The editable installation makes the
`src/convertion_pro` package importable without setting `PYTHONPATH`.

## Tests and preview limitations

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The automated tests use synthetic data and `SimulatedProgrammer`; they do not
require a vehicle, programmer, or private EEPROM dumps. Preview API tests also
require `httpx`, included in the `dev` extra.

The preview is a development interface, not a validated hardware integration.
Use synthetic files for local testing and do not connect automotive hardware.
The `/api/convert` demonstration currently requires the private files
`tests/fixtures/jeep_wrangler_2012_2018/17_wrangler_km.bin` and
`17_wrangler_mil.bin`. These are intentionally not distributed; on a clean
checkout this endpoint reports a missing fixture. File conversion and the
synthetic read-memory demonstration can be tested without them. Do not commit
private dumps or treat simulated success as validation on a real vehicle.

## V0.1

The first milestone implements the complete technician workflow using a simulated programmer:

Select Vehicle → Connection Guide → Safety Check → Convert → Verify → Complete

## Architecture

- Desktop UI
- Core workflow engine
- Hardware abstraction layer
- Simulated programmer
- Vehicle profile system
- Mandatory backup manager
- Verification engine
- Operation logging

## Safety invariants

CONVERTION-PRO must never write unless:

1. the programmer is detected;
2. the correct cable is identified;
3. supply voltage is valid;
4. communication with the cluster is verified;
5. the cluster profile matches;
6. an original backup has been created.

Every write must be followed by read-back verification.

V0.1 uses synthetic test data only. It contains no real vehicle memory maps, security bypasses, or odometer-manipulation routines.
