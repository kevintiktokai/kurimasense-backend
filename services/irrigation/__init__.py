"""
KurimaSense AI Irrigation Recommendation Engine
===============================================

Produces *actionable, explainable* irrigation recommendations — not reminders.

Model: a daily FAO-56-style root-zone water balance.

  * Crop demand: ETc = Kc × ET₀, with the stage Kc from the existing
    ``crop_profiles`` knowledge base and FAO ET₀ from Open-Meteo.
  * Supply: effective rainfall over the recent past, recorded irrigation from
    the planner (completed irrigation tasks), and probability-weighted
    forecast rain.
  * Soil: plant-available water capacity from the Soil Intelligence profile
    (``water_holding_capacity``, mm/m), scaled by a stage-dependent root depth,
    gives Total Available Water; the management-allowed depletion fraction
    gives the Readily Available Water trigger.

Decision: compare estimated current depletion to the RAW trigger, net of what
the sky is about to deliver — recommend *irrigate now / irrigate soon / delay
(rain expected) / monitor / no irrigation needed*, with millimetres, minutes
(per irrigation method), a confidence grade, and the reasoning chain.

The engine core (``engine.py``) is pure and unit-tested; ``service.py`` wires
it to fields, soil profiles, weather and the planner. New data sources (soil
moisture probes, satellite ET, IoT) extend :class:`IrrigationInputs` — the
decision core and its consumers do not change.
"""

from .engine import recommend
from .models import DayWeather, IrrigationInputs, IrrigationRecommendation

__all__ = ["recommend", "DayWeather", "IrrigationInputs", "IrrigationRecommendation"]
