"""
End-to-end-ish integration test (Step F).

Simulates how the consumer screens render off a single FieldState document and
verifies that no two screens can display contradictory information about the same
field — because they all read the same canonical source.
"""

from datetime import datetime, timedelta

from services.field_state.aggregator import assemble_field_state

NOW = datetime(2026, 6, 5, 22, 0, 0)

HEALTHY = {"Thriving", "Strong"}
POOR = {"Critical", "Distressed", "Stressed"}


def _field(**over):
    base = {
        "id": "22222222-2222-2222-2222-222222222222",
        "user_id": "tenant-X",
        "name": "Field 7",
        "crop_type": "Maize",
        "variety": "SC727",
        "planting_date": (NOW - timedelta(days=70)).date().isoformat(),
        "size_hectares": 8.0,
        "natural_region": "II",
        "polygon_coordinates": [{"lat": -17.8, "lon": 31.0}],
    }
    base.update(over)
    return base


def _render_field_detail(fs):
    """What the Field Detail screen would show: a single health badge + NDVI label,
    both sourced from the aggregator (no local thresholds)."""
    return {
        "badge_label": fs.kurima_score.label,
        "badge_color": fs.kurima_score.color,
        "ndvi_value": fs.indices.current.ndvi,
        "ndvi_label": fs.indices.current.ndvi_label,
        "insight": fs.kurima_score.primary_driver,
    }


def _render_dashboard(fs):
    """Dashboard 'AVG KurimaScore' card + recommended action + risks."""
    return {
        "avg_kurima_score": fs.kurima_score.score,
        "recommended_action": fs.kurima_score.recommended_action,
        "active_risks": len(fs.alerts),
    }


def test_field_detail_has_no_excellent_over_critical():
    """The flagged bug: 'EXCELLENT HEALTH' badge over a 'Critical' NDVI.
    With a low NDVI at a high-expectation stage, the badge must NOT be healthy."""
    fs = assemble_field_state(
        field_row=_field(), requester_id="tenant-X",
        daily_logs=[{"log_date": "2026-06-04", "ndvi": 0.21, "soil_moisture": 13, "cloud_cover": 4}],
        variety_in_database=True, input_record_count=1, now=NOW,
    )
    detail = _render_field_detail(fs)
    # Badge and NDVI label tell the SAME story.
    assert not (detail["badge_label"] in HEALTHY and detail["ndvi_label"] in POOR), (
        f"Contradiction: badge={detail['badge_label']} over ndvi_label={detail['ndvi_label']}"
    )
    assert detail["badge_label"] in POOR
    assert detail["ndvi_label"] in POOR


def test_dashboard_and_detail_agree():
    """Two different screens reading the same FieldState reach the same conclusion."""
    fs = assemble_field_state(
        field_row=_field(), requester_id="tenant-X",
        daily_logs=[{"log_date": "2026-06-04", "ndvi": 0.21, "soil_moisture": 13, "cloud_cover": 4}],
        variety_in_database=True, input_record_count=1, now=NOW,
    )
    detail = _render_field_detail(fs)
    dash = _render_dashboard(fs)
    # The dashboard's numeric score and the detail badge are derived from one score.
    from services.field_state.classifiers import label_for_score
    assert label_for_score(dash["avg_kurima_score"])[0] == detail["badge_label"]
    # Recommended action is present and shared (not hard-coded copy).
    assert dash["recommended_action"]


def test_agronomist_insight_never_field_not_found():
    """The insight panel reads kurima_score.* from the aggregator, so an existing
    field with data always yields real content — never 'Field not found'."""
    fs = assemble_field_state(
        field_row=_field(), requester_id="tenant-X",
        daily_logs=[{"log_date": "2026-06-04", "ndvi": 0.55, "soil_moisture": 35, "cloud_cover": 4}],
        variety_in_database=True, input_record_count=1, now=NOW,
    )
    assert fs.kurima_score.primary_driver
    assert fs.kurima_score.likely_cause
    assert fs.kurima_score.recommended_action
    assert "not found" not in (fs.kurima_score.primary_driver or "").lower()


def test_crop_health_trend_uses_kurima_score_0_100():
    """The Crop Health Trends chart must plot KurimaScore (0-100), not raw NDVI."""
    logs = [{"log_date": f"2026-05-{d:02d}", "ndvi": 0.3 + d * 0.01, "soil_moisture": 30} for d in range(1, 28)]
    fs = assemble_field_state(
        field_row=_field(), requester_id="tenant-X", daily_logs=logs,
        variety_in_database=True, input_record_count=1, now=NOW,
    )
    assert len(fs.indices.trend_30d) >= 20
    for pt in fs.indices.trend_30d:
        assert pt.kurima_score is None or 0 <= pt.kurima_score <= 100


def test_plan_item_flagged_against_water_deficit():
    """A foliar-feed plan item during a high-severity water/canopy alert is flagged
    'review against current conditions'."""
    fs = assemble_field_state(
        field_row=_field(), requester_id="tenant-X",
        daily_logs=[{"log_date": "2026-06-04", "ndvi": 0.18, "soil_moisture": 10, "cloud_cover": 4}],
        agri_raw={"water_balance": {"weekly_precipitation": 0.5, "weekly_et": 23.8, "balance": -23.3}},
        plan_rows=[{"id": "t1", "title": "Apply foliar feed", "activity_type": "fertilize",
                    "task_date": "2026-06-06", "is_ai_generated": True}],
        variety_in_database=True, input_record_count=1, now=NOW,
    )
    item = fs.active_plan_items[0]
    assert item.contextualized_to_current_conditions is False
    assert "review" in (item.notes or "").lower()
