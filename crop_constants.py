"""
KurimaSense Crop Constants
===========================
Single source of truth for all crop-level constants.
Every module that needs crop base temperatures, default yields,
water requirements, or transplant flags imports from HERE.
"""

# ---------------------------------------------------------------------------
# Base temperatures for Growing Degree Day (GDD) calculation (°C)
# Keys are LOWERCASE to normalise lookups: use CROP_BASE_TEMPS[name.lower()]
# Sources: FAO Crop Water Information, CIMMYT, Kutsaga, SeedCo, UZ Crop Science
# ---------------------------------------------------------------------------
CROP_BASE_TEMPS: dict[str, float] = {
    # Cereals & grains
    "maize": 10.0,
    "sorghum": 10.0,
    "finger millet": 12.0,
    "pearl millet": 12.0,
    "wheat": 4.0,
    # Cash crops
    "tobacco": 10.0,
    "cotton": 15.6,
    "sunflower": 6.0,
    "paprika": 12.0,
    "sesame": 15.0,
    "tea": 12.5,
    "coffee": 10.0,
    # Legumes & oilseeds
    "soybeans": 10.0,
    "soybean": 10.0,
    "groundnuts": 13.0,
    "groundnut": 13.0,
    "sugar beans": 10.0,
    "cowpeas": 10.0,
    "bambara nuts": 12.0,
    "peas": 4.4,
    "snow peas": 4.4,
    "green beans": 10.0,
    # Vegetables & root crops
    "tomato": 10.0,
    "potato": 7.0,
    "sweet potato": 15.0,
    "cabbage": 4.4,
    "onion": 4.4,
    "butternut": 10.0,
    "green pepper": 12.0,
    "garlic": 0.0,
    "carrot": 4.4,
    "cassava": 15.0,
    "covo": 4.4,
    "mustard": 4.4,
    "rape": 5.0,
    # Fruits & perennials
    "blueberries": 7.0,
    "strawberries": 7.0,
    "avocado": 10.0,
    "banana": 14.0,
    "citrus": 13.0,
    "macadamia": 10.0,
}


# ---------------------------------------------------------------------------
# Default yields (tonnes/ha) — fallback when no variety-specific data exists
# Keys are LOWERCASE with spaces (match crop_name.lower())
# ---------------------------------------------------------------------------
DEFAULT_YIELDS: dict[str, float] = {
    "maize": 6.0,
    "tobacco": 2.0,
    "soybean": 2.5,
    "soybeans": 2.5,
    "wheat": 4.5,
    "tomato": 40.0,
    "cabbage": 50.0,
    "potato": 25.0,
    "cotton": 2.5,
    "groundnuts": 2.0,
    "sunflower": 2.0,
    "sorghum": 3.0,
    "sugar beans": 2.0,
    "sweet potato": 20.0,
    "finger millet": 1.5,
    "pearl millet": 1.5,
    "cowpeas": 1.2,
    "bambara nuts": 1.0,
    "butternut": 20.0,
    "paprika": 2.5,
    "peas": 6.0,
    "snow peas": 5.0,
    "blueberries": 8.0,
    "green beans": 10.0,
    "tea": 3.0,
    "sesame": 0.8,
    "cassava": 20.0,
    "garlic": 8.0,
    "strawberries": 25.0,
    "green pepper": 30.0,
    "onion": 30.0,
    "carrot": 25.0,
    "coffee": 2.0,
    "avocado": 12.0,
    "banana": 30.0,
    "citrus": 20.0,
    "macadamia": 3.5,
    "covo": 15.0,
    "mustard": 12.0,
    "rape": 15.0,
}


# ---------------------------------------------------------------------------
# Crop water requirements (mm over full season)
# ---------------------------------------------------------------------------
CROP_WATER_REQUIREMENTS: dict[str, float] = {
    "maize": 500.0,
    "sorghum": 400.0,
    "finger millet": 350.0,
    "pearl millet": 300.0,
    "wheat": 400.0,
    "tobacco": 450.0,
    "cotton": 700.0,
    "sunflower": 500.0,
    "paprika": 600.0,
    "sesame": 350.0,
    "tea": 1200.0,
    "coffee": 1500.0,
    "soybeans": 450.0,
    "soybean": 450.0,
    "groundnuts": 400.0,
    "sugar beans": 350.0,
    "cowpeas": 300.0,
    "bambara nuts": 300.0,
    "peas": 350.0,
    "snow peas": 350.0,
    "green beans": 350.0,
    "tomato": 600.0,
    "potato": 500.0,
    "sweet potato": 500.0,
    "cabbage": 380.0,
    "onion": 400.0,
    "butternut": 400.0,
    "green pepper": 550.0,
    "garlic": 350.0,
    "carrot": 350.0,
    "cassava": 500.0,
    "covo": 350.0,
    "mustard": 300.0,
    "rape": 350.0,
    "blueberries": 600.0,
    "strawberries": 500.0,
    "avocado": 1000.0,
    "banana": 1200.0,
    "citrus": 900.0,
    "macadamia": 1000.0,
}


# ---------------------------------------------------------------------------
# Transplanted crops — these use transplant_date for GDD, not planting_date
# Values are Title Case to match CropType enum values
# ---------------------------------------------------------------------------
TRANSPLANTED_CROPS: list[str] = [
    "Tomato",
    "Cabbage",
    "Onion",
    "Potato",
    "Paprika",
    "Green Pepper",
    "Strawberries",
    "Tea",
    "Blueberries",
    "Coffee",
    "Tobacco",
    "Covo",
    "Rape",
    "Mustard",
]


def get_base_temp(crop_name: str, default: float = 10.0) -> float:
    """Get base temperature for GDD calculation, case-insensitive."""
    return CROP_BASE_TEMPS.get(crop_name.lower().strip(), default)


def get_default_yield(crop_name: str, default: float = 5.0) -> float:
    """Get default yield for a crop, case-insensitive."""
    key = crop_name.lower().strip()
    return DEFAULT_YIELDS.get(key, default)


def get_water_requirement(crop_name: str, default: float = 500.0) -> float:
    """Get total season water requirement in mm."""
    return CROP_WATER_REQUIREMENTS.get(crop_name.lower().strip(), default)


def is_transplanted(crop_name: str) -> bool:
    """Check if a crop is transplanted (vs direct-seeded)."""
    return crop_name.strip() in TRANSPLANTED_CROPS


# ---------------------------------------------------------------------------
# Per-crop / per-stage weights for the satellite index ensemble used by the
# yield model. Indices: ndvi, evi, ndre, ndmi, savi, sar.
#
# Stages (bucketed from growth_stage_percent):
#   - vegetative   : 0   ≤ pct < 40
#   - reproductive : 40  ≤ pct < 70
#   - grain_fill   : 70  ≤ pct ≤ 100  (used for any "ripening / fill" phase)
#
# Weights for a given (crop, stage) MUST sum to 1.0. The ensemble factor is
# Σ(weight_i × per_index_factor_i). Per-index factors live in yield_model.py.
#
# Choices reflect crop physiology:
#   - tobacco      : NDRE emphasis grows late season (canopy chlorophyll /
#                    nitrogen status driving leaf quality at topping & cure).
#   - maize        : NDMI emphasis during grain fill (kernel water content /
#                    end-of-season drought stress is the main yield lever).
#   - cotton       : NDRE consistently high — boll set & retention track
#                    canopy nitrogen status, which red-edge captures best.
#   - soybean      : NDMI rises in reproductive (R3-R5 pod fill is moisture
#                    sensitive); NDVI saturates so its share drops late.
#   - sorghum      : NDVI dominant early; NDMI shares with NDVI later as
#                    the crop is grown in drier zones.
#   - groundnuts   : NDMI heavy throughout — pod fill is highly moisture
#                    dependent and crop sits low in the canopy.
#   - wheat        : NDRE in reproductive (head emergence to anthesis); NDMI
#                    during grain fill matters for protein/test weight.
# ---------------------------------------------------------------------------
INDEX_NAMES: list[str] = ["ndvi", "evi", "ndre", "ndmi", "savi", "sar"]


CROP_INDEX_WEIGHTS: dict[str, dict[str, dict[str, float]]] = {
    "maize": {
        "vegetative":   {"ndvi": 0.40, "evi": 0.20, "ndre": 0.15, "ndmi": 0.15, "savi": 0.05, "sar": 0.05},
        "reproductive": {"ndvi": 0.30, "evi": 0.20, "ndre": 0.20, "ndmi": 0.20, "savi": 0.05, "sar": 0.05},
        "grain_fill":   {"ndvi": 0.20, "evi": 0.15, "ndre": 0.15, "ndmi": 0.35, "savi": 0.05, "sar": 0.10},
    },
    "tobacco": {
        "vegetative":   {"ndvi": 0.35, "evi": 0.20, "ndre": 0.20, "ndmi": 0.15, "savi": 0.05, "sar": 0.05},
        "reproductive": {"ndvi": 0.25, "evi": 0.15, "ndre": 0.30, "ndmi": 0.20, "savi": 0.05, "sar": 0.05},
        "grain_fill":   {"ndvi": 0.15, "evi": 0.10, "ndre": 0.40, "ndmi": 0.25, "savi": 0.05, "sar": 0.05},
    },
    "cotton": {
        "vegetative":   {"ndvi": 0.30, "evi": 0.20, "ndre": 0.25, "ndmi": 0.15, "savi": 0.05, "sar": 0.05},
        "reproductive": {"ndvi": 0.25, "evi": 0.15, "ndre": 0.30, "ndmi": 0.20, "savi": 0.05, "sar": 0.05},
        "grain_fill":   {"ndvi": 0.20, "evi": 0.15, "ndre": 0.30, "ndmi": 0.25, "savi": 0.05, "sar": 0.05},
    },
    "soybean": {
        "vegetative":   {"ndvi": 0.35, "evi": 0.25, "ndre": 0.15, "ndmi": 0.15, "savi": 0.05, "sar": 0.05},
        "reproductive": {"ndvi": 0.25, "evi": 0.20, "ndre": 0.15, "ndmi": 0.30, "savi": 0.05, "sar": 0.05},
        "grain_fill":   {"ndvi": 0.20, "evi": 0.15, "ndre": 0.15, "ndmi": 0.35, "savi": 0.05, "sar": 0.10},
    },
    "sorghum": {
        "vegetative":   {"ndvi": 0.40, "evi": 0.20, "ndre": 0.10, "ndmi": 0.20, "savi": 0.05, "sar": 0.05},
        "reproductive": {"ndvi": 0.30, "evi": 0.15, "ndre": 0.15, "ndmi": 0.30, "savi": 0.05, "sar": 0.05},
        "grain_fill":   {"ndvi": 0.20, "evi": 0.10, "ndre": 0.15, "ndmi": 0.40, "savi": 0.05, "sar": 0.10},
    },
    "groundnuts": {
        "vegetative":   {"ndvi": 0.30, "evi": 0.20, "ndre": 0.15, "ndmi": 0.25, "savi": 0.05, "sar": 0.05},
        "reproductive": {"ndvi": 0.20, "evi": 0.15, "ndre": 0.15, "ndmi": 0.35, "savi": 0.05, "sar": 0.10},
        "grain_fill":   {"ndvi": 0.15, "evi": 0.10, "ndre": 0.15, "ndmi": 0.40, "savi": 0.05, "sar": 0.15},
    },
    "wheat": {
        "vegetative":   {"ndvi": 0.40, "evi": 0.20, "ndre": 0.15, "ndmi": 0.15, "savi": 0.05, "sar": 0.05},
        "reproductive": {"ndvi": 0.25, "evi": 0.15, "ndre": 0.30, "ndmi": 0.20, "savi": 0.05, "sar": 0.05},
        "grain_fill":   {"ndvi": 0.20, "evi": 0.10, "ndre": 0.20, "ndmi": 0.35, "savi": 0.05, "sar": 0.10},
    },
}


# Default weights for any crop missing from CROP_INDEX_WEIGHTS.
DEFAULT_INDEX_WEIGHTS: dict[str, dict[str, float]] = {
    "vegetative":   {"ndvi": 0.40, "evi": 0.20, "ndre": 0.15, "ndmi": 0.15, "savi": 0.05, "sar": 0.05},
    "reproductive": {"ndvi": 0.30, "evi": 0.20, "ndre": 0.20, "ndmi": 0.20, "savi": 0.05, "sar": 0.05},
    "grain_fill":   {"ndvi": 0.25, "evi": 0.15, "ndre": 0.15, "ndmi": 0.30, "savi": 0.05, "sar": 0.10},
}


def get_index_weights(crop_name: str, stage_bucket: str) -> dict[str, float]:
    """
    Return the index-weight dict for a (crop, stage_bucket) pair.

    Falls back to DEFAULT_INDEX_WEIGHTS[stage_bucket] when the crop has no
    bespoke weights. Stage names: vegetative, reproductive, grain_fill.
    """
    crop_key = crop_name.lower().strip()
    table = CROP_INDEX_WEIGHTS.get(crop_key, DEFAULT_INDEX_WEIGHTS)
    return table.get(stage_bucket, DEFAULT_INDEX_WEIGHTS[stage_bucket])
