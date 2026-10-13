from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CATALOG_PATH = Path(
    "vehicles/catalog.json"
)


class VehicleCatalogError(RuntimeError):
    pass


def load_vehicle_catalog(
    path: Path | str = DEFAULT_CATALOG_PATH,
) -> dict[str, Any]:
    path = Path(path)

    if not path.exists():
        raise VehicleCatalogError(
            f"Vehicle catalog not found: {path}"
        )

    try:
        catalog = json.loads(
            path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise VehicleCatalogError(
            f"Invalid vehicle catalog JSON: {error}"
        ) from error

    schema_version = catalog.get("schema_version")
    if schema_version not in (1, 2):
        raise VehicleCatalogError(
            "Unsupported vehicle catalog schema."
        )

    makes = catalog.get("makes")

    if not isinstance(makes, list) or not makes:
        raise VehicleCatalogError(
            "Vehicle catalog contains no makes."
        )

    make_keys: set[str] = set()
    vehicle_keys: set[str] = set()

    for make in makes:
        make_key = make.get("key")
        make_label = make.get("label")
        vehicles = make.get("vehicles")

        if not make_key or not make_label:
            raise VehicleCatalogError(
                "Every make requires key and label."
            )

        if make_key in make_keys:
            raise VehicleCatalogError(
                f"Duplicate make key: {make_key}"
            )

        make_keys.add(make_key)

        if not isinstance(vehicles, list):
            raise VehicleCatalogError(
                f"Make {make_key} has invalid vehicles."
            )

        for vehicle in vehicles:
            key = vehicle.get("key")

            if not key:
                raise VehicleCatalogError(
                    f"Vehicle under {make_key} has no key."
                )

            if key in vehicle_keys:
                raise VehicleCatalogError(
                    f"Duplicate vehicle key: {key}"
                )

            vehicle_keys.add(key)

            if not vehicle.get("label"):
                raise VehicleCatalogError(
                    f"{key} has no label."
                )

            if not vehicle.get("file_label"):
                raise VehicleCatalogError(
                    f"{key} has no file_label."
                )

            conversion = vehicle.get(
                "conversion"
            )

            if not isinstance(conversion, dict):
                raise VehicleCatalogError(
                    f"{key} has no conversion profile."
                )

            if conversion.get("type") not in {
                "UNIT",
                "REGION",
            }:
                raise VehicleCatalogError(
                    f"{key} has invalid conversion type."
                )

            hardware = vehicle.get("hardware")

            if not isinstance(hardware, dict):
                raise VehicleCatalogError(
                    f"{key} has no hardware profile."
                )

            guide = vehicle.get("connection_guide")
            # Version 1 did not require a guide. Keep those catalogs readable
            # without guessing wiring or granting hardware access.
            if schema_version == 1 and "connection_guide" not in vehicle:
                guide = vehicle["connection_guide"] = {
                    "eyebrow": make_label.upper() + " · " + vehicle["label"].upper(),
                    "cluster_lines": [make_label.upper(), vehicle["label"].upper()],
                    "method": "NOT CONFIGURED",
                    "cable": "NOT CONFIGURED",
                    "supply": "NOT CONFIGURED",
                    "power_state": "OFF",
                    "steps": ["Connection guide is not configured for this vehicle."],
                    "proceed_enabled": False,
                    "blocked_reason": "CONNECTION GUIDE REQUIRED",
                }
            if not isinstance(guide, dict):
                raise VehicleCatalogError(
                    f"{key} has no connection guide."
                )

            for field in (
                "eyebrow", "method", "cable", "supply", "power_state",
            ):
                value = guide.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise VehicleCatalogError(
                        f"{key} has invalid connection guide {field}."
                    )

            for field in ("cluster_lines", "steps"):
                values = guide.get(field)
                if (
                    not isinstance(values, list)
                    or not values
                    or any(
                        not isinstance(value, str) or not value.strip()
                        for value in values
                    )
                ):
                    raise VehicleCatalogError(
                        f"{key} has invalid connection guide {field}."
                    )

            enabled = guide.get("proceed_enabled")
            if not isinstance(enabled, bool):
                raise VehicleCatalogError(
                    f"{key} has invalid connection guide proceed_enabled."
                )
            reason = guide.get("blocked_reason")
            if enabled:
                if hardware.get("physical_workflow_enabled") is not True:
                    raise VehicleCatalogError(
                        f"{key} cannot proceed with physical workflow disabled."
                    )
                if reason is not None:
                    raise VehicleCatalogError(
                        f"{key} has a blocked reason while proceed is enabled."
                    )
            elif not isinstance(reason, str) or not reason.strip():
                raise VehicleCatalogError(
                    f"{key} requires a connection guide blocked reason."
                )

    return catalog


def iter_vehicles(
    catalog: dict[str, Any],
):
    for make in catalog["makes"]:
        for vehicle in make["vehicles"]:
            yield make, vehicle


def get_vehicle(
    catalog: dict[str, Any],
    vehicle_key: str,
) -> dict[str, Any]:
    for _, vehicle in iter_vehicles(catalog):
        if vehicle["key"] == vehicle_key:
            return vehicle

    raise VehicleCatalogError(
        f"Unknown vehicle key: {vehicle_key}"
    )


def get_make(
    catalog: dict[str, Any],
    make_key: str,
) -> dict[str, Any]:
    for make in catalog["makes"]:
        if make["key"] == make_key:
            return make

    raise VehicleCatalogError(
        f"Unknown make key: {make_key}"
    )
