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

    if catalog.get("schema_version") != 1:
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
