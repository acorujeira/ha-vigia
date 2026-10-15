"""Geometry helpers."""
from custom_components.vigia.geo import cluster_count, offset


def test_cluster_count_merges_nearby_detections():
    lat, lon = 41.8, -8.3
    a = {"lat": lat, "lon": lon}
    b = dict(zip(("lat", "lon"), offset(lat, lon, 0.4, 90)))
    c = dict(zip(("lat", "lon"), offset(lat, lon, 1.0, 90)))  # chains to a through b
    far = dict(zip(("lat", "lon"), offset(lat, lon, 10, 0)))
    assert cluster_count([], 1.2) == 0
    assert cluster_count([a], 1.2) == 1
    assert cluster_count([a, b, c], 1.2) == 1
    assert cluster_count([a, b, c, far], 1.2) == 2
