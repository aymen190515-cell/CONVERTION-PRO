from convertion_pro.assets import (
    assets_root,
    cluster_asset,
    cable_asset,
)


def test_assets_root_points_to_project_assets():
    assert assets_root().name == "assets"


def test_cluster_asset_path():
    path = cluster_asset("jeep_wrangler_2012_2018", "front")
    assert path.as_posix().endswith(
        "assets/clusters/jeep_wrangler_2012_2018/front.png"
    )


def test_cable_asset_path():
    path = cable_asset("CP-JEEP-004")
    assert path.as_posix().endswith(
        "assets/cables/CP-JEEP-004.png"
    )
