"""
Flue-curing a tobacco crop — the barn stages, and choosing a barn.

Pure, no I/O.

Why this exists
---------------
The app went quiet at the point where a tobacco season is won or lost. A
grower can execute a flawless crop and destroy it in the barn in three days,
and until now every screen and the chat had nothing to say about curing.

``postharvest`` covers grain: drying to a moisture target, storage pests, the
larger grain borer. None of that applies to a leaf that has to be held at 85%
humidity for two days on purpose.

PROVENANCE — read this before changing a number
-----------------------------------------------
Every figure here is from the **Tobacco Research Board (Kutsaga)**, Zimbabwe's
statutory tobacco research institution and TIMB's technical counterpart:

* Stage temperatures, humidity, durations and the conditioning figure come from
  the Kutsaga Field Services Division curing guidance
  (https://kutsaga.co.zw/field-services-division/), read directly.
* Barn capacities, tier layouts, energy efficiencies and the plastic-barn bill
  of materials come from the Kutsaga Field Services Division document
  *Barn Designs and Types*
  (https://www.kutsaga.co.zw/wp-content/uploads/2021/09/Barns.pdf), read
  directly.

TIMB's own site returned 503 on every attempt during this work, so nothing here
is sourced from TIMB publications — including their reaping-ripeness guidance,
which is deliberately **absent** rather than reproduced from second-hand
summaries. If you want the ripeness indicators in the product, get them from a
TIMB document someone has actually opened.

.. warning::
   These are the published ranges, not a schedule tuned to a particular barn,
   leaf position or season. Kutsaga is explicit that "the curing period varies
   with the positions of the tobacco leaves on the plants, the type (and thus,
   efficiency) of the curing barn used and the local conditions" — top leaves
   need less time than bottom leaves because they carry less water. A grower
   ramping by the clock rather than by what the leaf is doing will ruin a barn.
   Pending agronomist sign-off before farmer-facing release, like the other
   compiled constants in this package.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

#: Crops this module will speak about. Flue-curing is a tobacco process; asking
#: it about maize must return nothing rather than something.
FLUE_CURED_CROPS = frozenset({"tobacco", "tobacco_flue_cured", "flue_cured_tobacco", "virginia"})

#: Tobacco types this module must **not** speak about.
#:
#: Burley and oriental are air- and sun-cured; dark tobacco is fire-cured. None
#: of them go anywhere near a flue-curing ramp, and running one to 70 °C over
#: seven days destroys the crop. This list exists because the obvious test —
#: ``crop.lower().startswith("tobacco")`` — reads as correct, passes every
#: review, and hands a burley grower a schedule that ruins their barn. It is
#: the same class of mistake as the rest of this codebase's guards: nothing
#: fails, the wrong answer is simply stated with confidence.
NOT_FLUE_CURED_MARKERS: Tuple[str, ...] = (
    "burley",
    "oriental",
    "air_cured",
    "aircured",
    "sun_cured",
    "suncured",
    "fire_cured",
    "firecured",
    "dark",
)


def _normalise(crop: str) -> str:
    """Lowercase, with spaces and hyphens folded to underscores."""
    return crop.strip().lower().replace("-", "_").replace(" ", "_")


@dataclass(frozen=True)
class CuringStage:
    """One stage of the barn cycle."""

    key: str
    name: str
    #: (low, high) °C dry-bulb operating range.
    temperature_c: Tuple[float, float]
    #: (low, high) days.
    duration_days: Tuple[float, float]
    #: Target relative humidity, where the source states one.
    relative_humidity_pct: Optional[float]
    what_happens: str
    watch_for: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "temperature_c": list(self.temperature_c),
            "duration_days": list(self.duration_days),
            "relative_humidity_pct": self.relative_humidity_pct,
            "what_happens": self.what_happens,
            "watch_for": self.watch_for,
        }


#: The three stages, in order, exactly as Kutsaga states them.
#:
#: Note the shape of the ramp: humidity is *held high* through colouring
#: precisely so the leaf does not dry before the colour has fixed, then falls
#: away as the temperature climbs. Rushing the first stage is the classic way
#: to cure a green barn, and no later stage can undo it.
CURING_STAGES: Tuple[CuringStage, ...] = (
    CuringStage(
        key="colouring",
        name="Colouring (yellowing)",
        temperature_c=(30.0, 40.0),
        duration_days=(1.0, 2.0),
        relative_humidity_pct=85.0,
        what_happens=(
            "Colour is fixed by the chemical and enzymatic changes the applied "
            "heat produces in the leaf."
        ),
        watch_for=(
            "Humidity held near 85%. Drying the leaf before the colour has "
            "fixed sets green, and nothing later in the cure recovers it."
        ),
    ),
    CuringStage(
        key="lamina_drying",
        name="Lamina drying",
        temperature_c=(40.0, 50.0),
        duration_days=(2.0, 3.0),
        relative_humidity_pct=None,
        what_happens="Moisture is driven out of the leaf blade.",
        watch_for=(
            "Raise temperature only as fast as the lamina is actually drying. "
            "Running ahead of the leaf scorches it."
        ),
    ),
    CuringStage(
        key="midrib_drying",
        name="Mid-rib (stem) drying",
        temperature_c=(65.0, 70.0),
        duration_days=(4.0, 5.0),
        relative_humidity_pct=None,
        what_happens="The mid-rib, which holds water long after the blade is dry, is dried out.",
        watch_for=(
            "Humidity falls away through this stage. It is the longest of the "
            "three and the one most often cut short."
        ),
    ),
)

#: Moisture added back after the cure so the leaf can be handled without
#: shattering. Kutsaga: the barn is "conditioned" by adding 12 to 15 % moisture
#: back into the leaf.
CONDITIONING_MOISTURE_PCT: Tuple[float, float] = (12.0, 15.0)


@dataclass(frozen=True)
class BarnType:
    """A curing barn a Zimbabwean grower might actually have."""

    key: str
    name: str
    #: Hectares of standing crop one barn can cure, as (typical, ± tolerance).
    hectares: Tuple[float, Optional[float]]
    #: kg of fuel per kg of cured leaf, with the fuel named — the number a
    #: grower budgets against.
    fuel_kg_per_kg_cured: Optional[float]
    fuel: Optional[str]
    tiers: Optional[str]
    suits: str
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        typical, tolerance = self.hectares
        return {
            "key": self.key,
            "name": self.name,
            "hectares": typical,
            "hectares_tolerance": tolerance,
            "fuel_kg_per_kg_cured": self.fuel_kg_per_kg_cured,
            "fuel": self.fuel,
            "tiers": self.tiers,
            "suits": self.suits,
            "notes": self.notes,
        }


#: Barn types at the Tobacco Research Board, with the figures Kutsaga publishes.
BARN_TYPES: Tuple[BarnType, ...] = (
    BarnType(
        key="plastic",
        name="Plastic barn",
        hectares=(0.6, None),
        fuel_kg_per_kg_cured=4.5,
        fuel="wood",
        tiers="3 tiers up × 5 tiers wide",
        suits="beginners and low-income small-scale growers",
        notes=(
            "4 m × 4 m × 4.5 m, holds up to 360 clips (0.5 ha). Reaches 70 °C, "
            "6–7 day turnaround. Built from 500 farm bricks, 37 tree poles "
            "(mapango) and 80 m² of 250 µm black polythene."
        ),
    ),
    BarnType(
        key="rocket",
        name="Rocket barn",
        hectares=(0.7, 0.2),
        fuel_kg_per_kg_cured=4.0,
        fuel="wood",
        tiers="4 tiers up × 5 tiers wide",
        suits="small-scale farmers",
        notes="Wood furnace with natural draught convection.",
    ),
    BarnType(
        key="conventional_up",
        name="Conventional up-draught",
        hectares=(2.0, 0.5),
        fuel_kg_per_kg_cured=None,
        fuel=None,
        tiers="7 tiers up × 5 tiers wide",
        suits="growers on natural convection, no fan",
        notes=(
            "Bottom vents ducted under the flues, top vent exhausts. As "
            "colouring progresses some air leaves through the top vent while "
            "ambient air enters through the bottom."
        ),
    ),
    BarnType(
        key="bulk_curer",
        name="Bulk curer",
        hectares=(2.0, 1.0),
        fuel_kg_per_kg_cured=1.5,
        fuel="coal peas",
        tiers=None,
        suits="growers with coal and racking",
        notes="Leaf held in frames (racks) rather than string or clips.",
    ),
    BarnType(
        key="conventional_down",
        name="Conventional down-draught",
        hectares=(3.0, 0.5),
        fuel_kg_per_kg_cured=2.5,
        fuel="coal cobbles",
        tiers="6 tiers up × 10 tiers wide",
        suits="larger growers",
        notes=(
            "Airtight insulated ceiling, no top vent; a fan recirculates and "
            "reheats the air. Can run as single units or several off one heat "
            "source."
        ),
    ),
    BarnType(
        key="tunnel",
        name="Continuous tunnel system",
        hectares=(120.0, None),
        fuel_kg_per_kg_cured=1.0,
        fuel="coal nuts",
        tiers=None,
        suits="estate scale",
        notes=(
            "Separate colouring, drying and conditioning compartments; trolleys "
            "move through against the airflow. Exhaust air conditions the dry "
            "leaf and is partly recirculated to control the wet bulb."
        ),
    ),
)


#: More barns than a grower would realistically build for one crop. Beyond
#: this the honest answer is "this barn type is not how you cure that area",
#: not a number.
MAX_BARNS = 12

#: A barn rated for more than this multiple of the standing crop is the wrong
#: tool, however efficient it is. Offering a 120 ha continuous tunnel system to
#: someone with 3 ha is not advice, it is noise.
OVERSIZE_FACTOR = 4.0


@dataclass(frozen=True)
class BarnOption:
    """A barn type, and how many of them this crop would need."""

    barn: BarnType
    count: int
    #: What that many barns actually covers, at the barn's typical rating.
    covers_hectares: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.barn.to_dict(),
            "count": self.count,
            "covers_hectares": round(self.covers_hectares, 2),
        }


@dataclass(frozen=True)
class CuringPlan:
    """Everything the app knows about putting this crop through a barn."""

    crop: str
    stages: Tuple[CuringStage, ...]
    total_days: Tuple[float, float]
    conditioning_moisture_pct: Tuple[float, float]
    barn_options: Tuple[BarnOption, ...]
    area_hectares: Optional[float]
    warnings: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "crop": self.crop,
            "stages": [s.to_dict() for s in self.stages],
            "total_days": list(self.total_days),
            "conditioning_moisture_pct": list(self.conditioning_moisture_pct),
            "barn_options": [b.to_dict() for b in self.barn_options],
            "area_hectares": self.area_hectares,
            "warnings": list(self.warnings),
        }


def is_flue_cured(crop: Optional[str]) -> bool:
    """
    Whether flue-curing applies to this crop at all.

    Deliberately not ``startswith("tobacco")`` — see
    :data:`NOT_FLUE_CURED_MARKERS`.
    """
    if not crop:
        return False
    text = _normalise(crop)
    if any(marker in text for marker in NOT_FLUE_CURED_MARKERS):
        return False
    if text in FLUE_CURED_CROPS:
        return True
    return "tobacco" in text or "virginia" in text or "flue_cured" in text


def total_cure_days() -> Tuple[float, float]:
    """The whole barn cycle, low and high, summed from the stages."""
    low = sum(s.duration_days[0] for s in CURING_STAGES)
    high = sum(s.duration_days[1] for s in CURING_STAGES)
    return low, high


def barn_options_for_area(hectares: Optional[float]) -> List[BarnOption]:
    """
    Barn types that could cure this much standing crop, and how many of each.

    Counts rather than filters, because a 5 ha grower does not buy a bigger
    barn — they build four small ones, which is what everyone around them has
    done. An earlier draft returned only barns whose single-unit rating
    exceeded the area, which meant a 5 ha field was offered the 120 ha
    continuous tunnel system and nothing else.

    Every workable option is returned rather than one recommendation: fuel is
    the binding constraint here, not efficiency. A grower with no coal cannot
    use a bulk curer however good its 1.5 kg/kg figure is, and a grower cutting
    their own wood is making a land decision as much as a curing one. That is
    theirs to make.

    Sizing uses each barn's *typical* rating, not the top of its tolerance. A
    barn run at its stated maximum becomes the bottleneck at peak reaping, and
    leaf that waits does not wait in good condition.
    """
    if hectares is None or hectares <= 0:
        return []

    options: List[BarnOption] = []
    for barn in BARN_TYPES:
        typical = barn.hectares[0]
        if typical <= 0:
            continue
        if typical > hectares * OVERSIZE_FACTOR:
            continue
        count = math.ceil(hectares / typical)
        if count > MAX_BARNS:
            continue
        options.append(
            BarnOption(barn=barn, count=count, covers_hectares=count * typical)
        )
    return sorted(options, key=lambda o: (o.count, o.barn.hectares[0]))


def fuel_required_kg(barn: BarnType, cured_leaf_kg: float) -> Optional[float]:
    """
    Fuel to cure this much leaf in this barn type.

    Returns ``None`` where Kutsaga publishes no efficiency figure for the barn
    rather than borrowing a neighbouring barn's number — this is the figure a
    grower budgets wood or coal against, and a plausible invented one is worse
    than a gap.
    """
    if barn.fuel_kg_per_kg_cured is None:
        return None
    if cured_leaf_kg is None or cured_leaf_kg <= 0:
        return None
    return barn.fuel_kg_per_kg_cured * cured_leaf_kg


def stage_by_key(key: str) -> Optional[CuringStage]:
    for stage in CURING_STAGES:
        if stage.key == key:
            return stage
    return None


def build_curing_plan(
    crop: Optional[str],
    *,
    area_hectares: Optional[float] = None,
) -> Optional[CuringPlan]:
    """
    The barn plan for this crop, or ``None`` if flue-curing does not apply.

    ``None`` rather than an empty plan is the contract the rest of this package
    uses: the caller can tell "we have nothing to say" from "we have this", and
    a screen that gets nothing renders nothing rather than an empty heading
    that reads like an answer.
    """
    if not is_flue_cured(crop):
        return None

    warnings: List[str] = [
        "These are published ranges, not a schedule for your barn. Curing time "
        "varies with leaf position on the plant, barn type and local "
        "conditions — top leaves carry less water and need less time. Ramp by "
        "what the leaf is doing, not by the clock.",
    ]
    options = barn_options_for_area(area_hectares)
    if area_hectares and not options:
        warnings.append(
            f"No standard barn type sizes sensibly to {area_hectares:g} ha "
            f"(the largest practical layout here is {MAX_BARNS} barns). Size "
            "this with your extension officer."
        )

    return CuringPlan(
        crop=str(crop),
        stages=CURING_STAGES,
        total_days=total_cure_days(),
        conditioning_moisture_pct=CONDITIONING_MOISTURE_PCT,
        barn_options=tuple(options),
        area_hectares=area_hectares,
        warnings=tuple(warnings),
    )
