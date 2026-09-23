# CONVERTION-PRO

Professional automotive instrument-cluster conversion platform.

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
