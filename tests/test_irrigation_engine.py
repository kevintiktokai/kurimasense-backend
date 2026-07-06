"""
Hermetic tests for the pure irrigation decision core (services/irrigation/engine).

Scenario style: build IrrigationInputs directly (no DB/weather I/O) and assert
on the action, amounts and the explanation chain.
"""

from datetime import date, timedelta

from services.irrigation.engine import recommend
from services.irrigation.models import DayWeather, IrrigationInputs

TODAY = date(2026, 7, 6)


def make_inputs(**overrides) -> IrrigationInputs:
    """A maize field mid-season with 14 dry, hot past days and a dry forecast."""
    past = [
        DayWeather(date=(TODAY - timedelta(days=14 - i)).isoformat(), et0=5.0, precip=0.0)
        for i in range(14)
    ]
    forecast = [
        DayWeather(date=(TODAY + timedelta(days=i)).isoformat(), et0=5.0, precip=0.0,
                   precip_probability=5.0)
        for i in range(7)
    ]
    defaults = dict(
        field_id="f1",
        field_name="North Block",
        crop="Maize",
        stage_name="Vegetative",
        kc=1.0,
        days_since_planting=60,
        awc_mm_per_m=140.0,
        awc_source="soil_profile",
        root_depth_m=0.5,          # TAW = 70mm, RAW = 35mm
        past=past,
        forecast=forecast,
        method="sprinkler",
    )
    defaults.update(overrides)
    return IrrigationInputs(**defaults)


def test_dry_spell_triggers_irrigate_now_with_amount_and_duration():
    rec = recommend(make_inputs(), today=TODAY)
    # 14 dry days at 5mm/day ETc from a 17.5mm start pins depletion at TAW.
    assert rec.action == "irrigate_now"
    assert rec.recommended_mm > 0
    assert rec.recommended_mm <= rec.taw_mm
    assert rec.duration_minutes and rec.duration_minutes > 0
    assert rec.water_deficit_mm >= rec.raw_trigger_mm
    assert any("trigger" in r for r in rec.reasoning)
    assert rec.headline.startswith("Irrigate today")


def test_recent_heavy_rain_means_no_irrigation_needed():
    past = [
        DayWeather(date=(TODAY - timedelta(days=14 - i)).isoformat(), et0=4.0,
                   precip=85.0 if i == 12 else 0.0)  # big storm two days ago
        for i in range(14)
    ]
    rec = recommend(make_inputs(past=past), today=TODAY)
    assert rec.action == "not_needed"
    assert rec.recommended_mm == 0
    assert rec.next_review_date is not None


def test_imminent_reliable_rain_delays_irrigation():
    forecast = [
        DayWeather(date=TODAY.isoformat(), et0=5.0, precip=40.0, precip_probability=90.0),
        DayWeather(date=(TODAY + timedelta(days=1)).isoformat(), et0=5.0, precip=25.0,
                   precip_probability=85.0),
    ] + [
        DayWeather(date=(TODAY + timedelta(days=i)).isoformat(), et0=5.0, precip=0.0,
                   precip_probability=10.0)
        for i in range(2, 7)
    ]
    rec = recommend(make_inputs(forecast=forecast), today=TODAY)
    assert rec.action == "delay_rain_expected"
    assert rec.recommended_mm == 0
    assert rec.expected_rain_mm_3d > 20
    assert any("rain" in r.lower() for r in rec.reasoning)


def test_unreliable_forecast_rain_does_not_stop_irrigation():
    # Same rain volumes but at 30% probability — engine should not gamble.
    forecast = [
        DayWeather(date=(TODAY + timedelta(days=i)).isoformat(), et0=5.0,
                   precip=30.0 if i < 2 else 0.0, precip_probability=30.0)
        for i in range(7)
    ]
    rec = recommend(make_inputs(forecast=forecast), today=TODAY)
    assert rec.action == "irrigate_now"


def test_planner_irrigation_record_resets_the_balance():
    irrigation_day = (TODAY - timedelta(days=2)).isoformat()
    rec = recommend(make_inputs(irrigation_dates=[irrigation_day]), today=TODAY)
    # Refilled 2 days ago; only ~2 days of ETc depleted since.
    assert rec.action in ("not_needed", "monitor")
    assert rec.water_deficit_mm < rec.raw_trigger_mm
    assert any("irrigation" in r.lower() and irrigation_day in r for r in rec.reasoning)


def test_sensor_reading_overrides_model_and_lifts_confidence():
    low = recommend(make_inputs(measured_soil_moisture_depletion_mm=5.0), today=TODAY)
    assert low.action in ("not_needed", "monitor")
    assert low.confidence >= 0.85
    assert "soil_moisture_sensor" in low.data_sources


def test_soil_profile_source_raises_confidence_over_default():
    with_profile = recommend(make_inputs(awc_source="soil_profile"), today=TODAY)
    without = recommend(make_inputs(awc_source="default"), today=TODAY)
    assert with_profile.confidence > without.confidence
    assert any("soil profile" in r.lower() for r in with_profile.reasoning)
    assert any("assumed" in r.lower() for r in without.reasoning)


def test_drip_method_changes_duration():
    sprinkler = recommend(make_inputs(method="sprinkler"), today=TODAY)
    drip = recommend(make_inputs(method="drip"), today=TODAY)
    assert sprinkler.action == drip.action == "irrigate_now"
    assert drip.duration_minutes > sprinkler.duration_minutes  # slower application rate


def test_every_recommendation_is_explainable_and_serialisable():
    rec = recommend(make_inputs(), today=TODAY)
    assert len(rec.reasoning) >= 4
    payload = rec.to_dict()
    for key in ("action", "headline", "reasoning", "water_deficit_mm", "recommended_mm",
                "confidence", "confidence_label", "data_sources"):
        assert key in payload
    assert payload["confidence_label"] in ("high", "medium", "low")
