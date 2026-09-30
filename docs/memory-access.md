# Memory access status and integration contract

This change does not make a vLinker read an EEPROM through a cluster connector.
No production chip/access/transport combination is marked VALIDATED. The HTTP
hardware-read action stays blocked and never returns a synthetic fallback.
SIMULATED data and opened FILE data retain their own provenance.

## What is implemented

- `memory_access.py` keys capabilities by exact chip family, access interface,
  transport, and (for CAN) controller protocol variant. Vehicle labels are not
  protocol selectors. Direct I2C, direct SPI, processor debug and controller CAN
  are different interfaces; only one documented I2C candidate is included.
- Regions have names, offsets and byte sizes. An unsupported combination cannot
  inherit support from another chip, transport or controller.
- A capability distinguishes UNSUPPORTED, DOCUMENTED_UNVALIDATED and VALIDATED.
  Documentation and a bench validation record are required for the last state.
  Records are reviewed integration evidence, not proof created by a UI toggle.
- Identity confirmation is bound to a chip, connection and device address. The
  I2C candidate requires physical-marking/datasheet evidence; this is operator
  confirmation, not automatic electronic identification. An ACK, adapter identity,
  voltage or an all-FF buffer does not identify a chip or validate its contents.
- `MemoryReader` checks qualification, implementation, identity and region before
  dispatch. It returns exact-size data, provenance and SHA-256. It never pads,
  returns a partial dump, substitutes a demo, or interprets a hash as proof that
  the correct physical device was read. Callers own an exclusive transport session
  and must close it; concurrent access and hot-swapping are not supported.
- `/api/advanced/memory-capability` reports passive capability metadata. It does
  not open hardware. No HTTP endpoint opens the I2C transport, accepts a bus path,
  or promotes a capability to VALIDATED.

## Documented direct-I2C candidate, not physically qualified

ST's M24C32 documentation describes a 4096-byte EEPROM and a random-address read
using a two-byte address followed by a repeated START and sequential read. The
implementation covers only that main memory region, not identification/OTP pages.
It bounds every request to the region and processes at most 32 bytes per transfer.
The pointer-setting phase is a write-direction I2C transaction, **not a write of
EEPROM contents**. No write-memory, erase or unlock operation is implemented.

References reviewed:

- [ST DS0952, sections 5.2.1 and 5.2.3](https://www.st.com/resource/en/datasheet/m24c32-r.pdf)
- [Linux i2c-dev combined transactions](https://docs.kernel.org/i2c/dev-interface.html)
- [smbus2 API](https://smbus2.readthedocs.io/en/latest/api.html)

`linux_i2c.py` contains a concrete smbus2/i2c-dev implementation, with lazy import
and explicit context-managed opening. Importing it has no hardware effects.
The optional `i2c` dependency installs smbus2 only on Linux. The default Windows
installation gains no driver and cannot use COM3 as an I2C controller.

The candidate requires direct SDA/SCL access through a supported I2C controller
with combined-transaction support. Exact chip marking, package, voltage, address
straps, bus ownership and electrical setup must be verified first. Cluster 12 V
power is not an EEPROM supply specification. This is not a wiring instruction or
a claim that in-circuit access is safe on the user's board. A generic "24C32"
selection is deliberately not aliased to the confirmed ST family.

Tests exercise the algorithm and transport lifecycle with fake buses only. No
Linux driver installation, actual I2C device, Windows USB-I2C adapter, target chip
or electrical behavior has been validated. Production capability remains
DOCUMENTED_UNVALIDATED. The low-level private routine is development code, not a
supported user action. Before enabling dispatch, a maintainer must qualify an
exact adapter/setup and attach a genuine validation record. There is no shortcut
in the preview UI or API to bypass that requirement.

## CAN through a cluster controller remains unsupported

The presence of a 24C32 in two clusters does not imply identical CAN access.
For the first controller implementation, obtain documented addressing/transport,
exact controller and firmware identification, read service and permitted regions,
session/security prerequisites, framing, length limits, timing, error responses
and an authorized vendor API or protocol specification. A commercial feature
listing or a mileage-specific operation is not a full EEPROM dump protocol.

No such protocol is implemented for GJ7T-10849-AJ, vLinker ELM, SPC56xx, RH850 or
any other cluster. This is a lack of validated documentation, not proof of
physical impossibility. No speculative CAN/UDS commands or proprietary unlocks
are included.

## Integration and validation sequence

1. Preserve and compare the active Codespace changes before applying this patch.
2. Merge the provenance fix and passive registry independently of hardware work.
3. Confirm the exact chip marking and choose direct access versus a documented
   controller protocol. Obtain the required adapter and authoritative protocol.
4. Qualify a dedicated, authorized bench setup against known data, boundary and
   disconnect/error cases; record adapter, chip, firmware and electrical limits.
5. Only then register VALIDATED capability and connect a separately reviewed local
   execution flow. A Codespaces server has no direct access to PC USB hardware.

Keep all hardware-read actions disabled until those steps are complete. Do not
apply or push over an actively edited Codespace without reviewing its working tree.
