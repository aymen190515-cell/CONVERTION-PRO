from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def assets_root() -> Path:
    return project_root() / "assets"


def cluster_asset(profile_id: str, view: str = "front") -> Path:
    return assets_root() / "clusters" / profile_id / f"{view}.png"


def cable_asset(cable_id: str) -> Path:
    return assets_root() / "cables" / f"{cable_id}.png"


def branding_asset(filename: str) -> Path:
    return assets_root() / "branding" / filename
