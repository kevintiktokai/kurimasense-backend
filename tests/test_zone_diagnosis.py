"""
Zone diagnosis tests — services/zones/diagnosis.py.

Two things carry the weight: the point-in-polygon attribution (putting a
farmer's own observation on the wrong part of their field is worse than not
showing it), and the restraint about naming causes (a farmer who walks to a
zone expecting waterlogging and finds armyworm stops trusting the map).
"""

import pytest

from services.zones.diagnosis import (
    MATERIAL_NDVI_GAP,
    SEVERE_NDVI_GAP,
    attribute_observations,
    diagnose_zones,
    field_mean_ndvi,
    point_in_ring,
)

# A unit square, open ring.
SQUARE = [
    {"lat": 0.0, "lon": 0.0},
    {"lat": 0.0, "lon": 1.0},
    {"lat": 1.0, "lon": 1.0},
    {"lat": 1.0, "lon": 0.0},
]


def zone(index, label, ndvi, polygon=None, area_share=0.25):
    return {
        "index": index, "label": label, "ndvi": ndvi,
        "polygon": polygon if polygon is not None else SQUARE,
        "area_share": area_share,
    }


def obs(lat, lon, category="pest"):
    return {"lat": lat, "lon": lon, "category": category}


# --- Geometry ----------------------------------------------------------------

def test_a_point_inside_the_ring_is_inside():
    assert point_in_ring(0.5, 0.5, SQUARE) is True


def test_points_outside_the_ring_are_outside():
    for lat, lon in [(1.5, 0.5), (-0.5, 0.5), (0.5, 1.5), (0.5, -0.5)]:
        assert point_in_ring(lat, lon, SQUARE) is False


def test_a_point_level_with_a_vertex_is_not_double_counted():
    # The classic ray-casting bug: counting both edges meeting at a vertex
    # flips `inside` twice and reports an interior point as outside.
    assert point_in_ring(0.0, 0.5, SQUARE) is True


def test_an_L_shaped_zone_excludes_its_missing_corner():
    l_shape = [
        {"lat": 0.0, "lon": 0.0},
        {"lat": 0.0, "lon": 1.0},
        {"lat": 0.5, "lon": 1.0},
        {"lat": 0.5, "lon": 0.5},
        {"lat": 1.0, "lon": 0.5},
        {"lat": 1.0, "lon": 0.0},
    ]
    assert point_in_ring(0.25, 0.25, l_shape) is True
    assert point_in_ring(0.75, 0.75, l_shape) is False   # the cut-out corner


def test_a_degenerate_ring_contains_nothing():
    assert point_in_ring(0.5, 0.5, []) is False
    assert point_in_ring(0.5, 0.5, [{"lat": 0, "lon": 0}]) is False


# --- Attribution -------------------------------------------------------------

def test_an_observation_lands_in_the_zone_that_contains_it():
    far = [
        {"lat": 10.0, "lon": 10.0}, {"lat": 10.0, "lon": 11.0},
        {"lat": 11.0, "lon": 11.0}, {"lat": 11.0, "lon": 10.0},
    ]
    grouped = attribute_observations(
        [zone(0, "A", 0.5), zone(1, "B", 0.5, polygon=far)],
        [obs(0.5, 0.5), obs(10.5, 10.5)],
    )
    assert len(grouped[0]) == 1
    assert len(grouped[1]) == 1


def test_an_observation_outside_every_zone_is_dropped_not_snapped():
    # A pin outside the mapped boundary is not evidence about any zone in it.
    grouped = attribute_observations([zone(0, "A", 0.5)], [obs(50.0, 50.0)])
    assert grouped == {}


def test_observations_without_coordinates_are_skipped():
    grouped = attribute_observations(
        [zone(0, "A", 0.5)],
        [{"category": "pest"}, {"lat": None, "lon": 1}, {"lat": "x", "lon": "y"}],
    )
    assert grouped == {}


def test_an_observation_is_attributed_to_one_zone_only():
    grouped = attribute_observations(
        [zone(0, "A", 0.5), zone(1, "B", 0.5)],   # overlapping polygons
        [obs(0.5, 0.5)],
    )
    assert sum(len(v) for v in grouped.values()) == 1


# --- Field mean --------------------------------------------------------------

def test_field_mean_is_area_weighted():
    zones = [zone(0, "A", 0.8, area_share=0.75), zone(1, "B", 0.4, area_share=0.25)]
    assert field_mean_ndvi(zones) == pytest.approx(0.7, abs=0.001)


def test_unanalysed_zones_do_not_drag_the_mean_down():
    zones = [zone(0, "A", 0.6), zone(1, "B", None)]
    assert field_mean_ndvi(zones) == pytest.approx(0.6)


def test_no_analysed_zones_means_no_mean():
    assert field_mean_ndvi([zone(0, "A", None)]) is None
    assert field_mean_ndvi([]) is None


# --- Diagnosis ---------------------------------------------------------------

def test_being_slightly_below_average_is_not_a_finding():
    # Half of any field is below its own average — that is arithmetic.
    zones = [zone(0, "North-West", 0.70), zone(1, "North-East", 0.66)]
    out = diagnose_zones(zones)
    assert all(z["severity"] == "ok" for z in out)


def test_a_materially_behind_zone_is_flagged_with_both_numbers():
    zones = [
        zone(0, "North-West", 0.72), zone(1, "North-East", 0.40),
        zone(2, "South-West", 0.70), zone(3, "South-East", 0.71),
    ]
    out = diagnose_zones(zones)
    worst = out[0]
    assert worst["label"] == "North-East"
    assert worst["severity"] in ("watch", "problem")
    assert "0.40" in worst["summary"]


def test_severity_escalates_with_the_size_of_the_gap():
    # Note the gap is measured against the field MEAN, which a weak zone pulls
    # down toward itself — so a zone has to be further behind its neighbours
    # than the raw threshold to clear it. Three healthy zones plus one weak.
    healthy = [zone(i, chr(65 + i), 0.72) for i in range(3)]

    mild = diagnose_zones(healthy + [zone(3, "D", 0.58)])
    severe = diagnose_zones(healthy + [zone(3, "D", 0.45)])

    assert MATERIAL_NDVI_GAP <= mild[0]["gap_vs_field"] < SEVERE_NDVI_GAP
    assert mild[0]["severity"] == "watch"

    assert severe[0]["gap_vs_field"] >= SEVERE_NDVI_GAP
    assert severe[0]["severity"] == "problem"


def test_worst_zone_comes_first():
    zones = [zone(0, "A", 0.72), zone(1, "B", 0.35), zone(2, "C", 0.55)]
    out = diagnose_zones(zones)
    assert [z["label"] for z in out] == ["B", "C", "A"]


def test_a_scouting_pin_in_the_zone_becomes_a_named_cause():
    zones = [zone(0, "North-West", 0.72, polygon=SQUARE), zone(1, "North-East", 0.35, polygon=[
        {"lat": 5.0, "lon": 5.0}, {"lat": 5.0, "lon": 6.0},
        {"lat": 6.0, "lon": 6.0}, {"lat": 6.0, "lon": 5.0},
    ])]
    out = diagnose_zones(zones, observations=[obs(5.5, 5.5, "disease")])
    worst = out[0]
    assert worst["observation_count"] == 1
    assert any("disease" in c for c in worst["causes"])
    assert "check what you logged" in worst["action"]


def test_a_weak_zone_with_no_evidence_admits_it_rather_than_guessing():
    # Naming an unevidenced cause is worse than admitting ignorance: a farmer
    # who walks expecting waterlogging and finds armyworm stops trusting it.
    out = diagnose_zones([zone(0, "A", 0.72), zone(1, "B", 0.35)])
    worst = out[0]
    assert any("Nothing recorded here explains it" in c for c in worst["causes"])
    assert "Scout" in worst["action"]


def test_soil_context_is_offered_as_possible_not_asserted():
    out = diagnose_zones(
        [zone(0, "A", 0.72), zone(1, "B", 0.35)],
        soil={"drainage": "poorly drained"},
    )
    causes = out[0]["causes"]
    assert any(c.startswith("Possible:") for c in causes)


def test_soil_context_is_not_attached_to_healthy_zones():
    out = diagnose_zones(
        [zone(0, "A", 0.70), zone(1, "B", 0.69)],
        soil={"drainage": "poorly drained"},
    )
    assert all(z["causes"] == [] for z in out)


def test_unanalysed_zones_are_reported_as_unknown_not_healthy():
    out = diagnose_zones([zone(0, "A", None)])
    assert out[0]["severity"] == "unknown"
    assert "not been analysed" in out[0]["summary"]


def test_comparison_is_within_the_field_not_against_an_absolute():
    # A young crop is low everywhere; an absolute threshold would call every
    # zone a problem, which is a calendar reading rather than a diagnosis.
    young = diagnose_zones([zone(0, "A", 0.25), zone(1, "B", 0.24)])
    assert all(z["severity"] == "ok" for z in young)


def test_diagnosis_serialises_for_the_api():
    out = diagnose_zones([zone(0, "A", 0.72), zone(1, "B", 0.35)])
    assert set(out[0]) >= {"index", "label", "ndvi", "gap_vs_field", "severity",
                           "summary", "causes", "observation_count", "action"}
