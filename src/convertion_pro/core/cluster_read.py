"""Vehicle-bound read dispatch. No transport opening or private dump access."""
from typing import Protocol
import hashlib
import json
from pathlib import Path

from .vehicle_catalog import get_vehicle
from .workflow import ConversionWorkflow
from convertion_pro.hardware.simulator import SimulatedProgrammer


class ClusterDriver(Protocol):
    def read(self, vehicle: dict, profile: dict) -> dict: ...


class SyntheticJeepDriver:
    def read(self, vehicle, profile):
        if vehicle['key'] != 'jeep_wrangler_2012_2018':
            raise ValueError('Ce pilote synthétique ne correspond pas au véhicule sélectionné.')
        size = profile['memory']['size_bytes']
        if size != 1024:
            raise ValueError('Synthetic driver requires its exact 1024-byte profile.')
        memory = bytearray([0xFF] * size)
        memory[0x68], memory[0x69] = 0x04, 0x12
        programmer = SimulatedProgrammer(memory)
        if not ConversionWorkflow(programmer, profile).run_safety_check().passed:
            raise ValueError('Simulated safety check failed.')
        data = programmer.read_memory()
        return {
            'success': True, 'source': 'SIMULATED', 'hardware_access': False,
            'read_only': True, 'memory_read_supported': False,
            'cluster_identified': False, 'programmer_ready': False,
            'vehicle_key': vehicle['key'],
            'vehicle': 'SIMULATED Jeep Wrangler 2012-2018 demo',
            'cluster_profile_id': vehicle['cluster_profile']['id'],
            'driver_id': 'SYNTHETIC_JEEP_1024',
            'filename': vehicle['key'] + '_SIMULATED.bin',
            'memory_type': profile['memory']['type'], 'memory_size': len(data),
            'data_hex': data.hex(), 'sha256': hashlib.sha256(data).hexdigest(),
            'cluster_id': programmer.identify_cluster(),
            'cable': programmer.identify_cable(),
            'voltage': programmer.measure_voltage(), 'current': programmer.measure_current(),
            'current_validated': False,
            'annotations': [{'offset': offset, 'label': f'Validated conversion offset 0x{offset:X}'}
                            for offset in (0x68, 0x69)],
        }


SIMULATION_DRIVERS: dict[str, ClusterDriver] = {'SYNTHETIC_JEEP_1024': SyntheticJeepDriver()}


class VehicleReadService:
    def __init__(self, catalog):
        self.catalog = catalog

    def capabilities(self, vehicle_key):
        vehicle = get_vehicle(self.catalog, vehicle_key)
        profile = vehicle.get('cluster_profile') or {}
        simulation = (
            profile.get('simulation_driver') in SIMULATION_DRIVERS
            and vehicle_key == 'jeep_wrangler_2012_2018'
            and bool(vehicle.get('profile_path'))
        )
        if not vehicle['hardware'].get('physical_workflow_enabled'):
            reason = vehicle.get('connection_guide', {}).get('blocked_reason') or 'Hardware véhicule désactivé.'
        elif not profile.get('exact_identity_confirmed'):
            reason = 'Profil exact du cluster et de sa puce non confirmé ; protocole de lecture via processeur non documenté et non validé.'
        else:
            reason = 'Aucun pilote matériel avec protocole documenté et validé pour ce profil.'
        return {
            'vehicle_key': vehicle_key, 'cluster_profile_id': profile.get('id'),
            'simulation_driver': profile.get('simulation_driver') if simulation else None,
            'simulation_available': simulation,
            'hardware_driver': None, 'hardware_read_available': False,
            'cluster_identified': False, 'programmer_ready': False,
            'reason': reason,
        }

    def read(self, vehicle_key, mode):
        if mode not in ('SIMULATED', 'HARDWARE'):
            raise ValueError('Mode de lecture inconnu.')
        capabilities = self.capabilities(vehicle_key)
        if mode == 'HARDWARE':
            # No hardware driver is registered. No adapter or simulation fallback.
            raise ValueError(capabilities['reason'])
        if not capabilities['simulation_available']:
            raise ValueError('Aucun pilote de simulation pour ce véhicule ; aucun repli vers Jeep.')
        vehicle = get_vehicle(self.catalog, vehicle_key)
        profile = json.loads(Path(vehicle['profile_path']).read_text(encoding='utf-8'))
        return SIMULATION_DRIVERS[capabilities['simulation_driver']].read(vehicle, profile)
