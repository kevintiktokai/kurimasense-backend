"""
KurimaSense Agronomic Yield Model
==================================
Provides scientifically-grounded yield predictions based on:
- Variety-specific yield potentials from database
- Growth stage progress
- NDVI health trajectory
- Water balance / rainfall adequacy
- Input application history
- Disease/pest risk factors

This replaces AI-hallucinated yields with data-driven projections.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json

from database import get_db_connection
from proactive_intelligence import get_variety_info, calculate_growth_stage


@dataclass
class YieldProjection:
    """Structured yield projection result."""
    projected_yield: float  # tonnes/ha
    yield_potential: float  # max achievable tonnes/ha
    confidence_bands: Dict[str, float]  # low, mid, high
    confidence_score: float  # 0.0 - 1.0
    confidence_factors: List[str]  # Human-readable factors
    yield_gap_analysis: str  # Explanation of gap
    methodology: str  # Version/method used
    adjustment_factors: Dict[str, float]  # Breakdown of adjustments
    disclaimer: str  # Legal disclaimer


# Zimbabwe Natural Region yield multipliers
# Based on average rainfall reliability
NATURAL_REGION_MULTIPLIERS = {
    "I": {"maize": 1.2, "tobacco": 1.15, "soybean": 1.1, "default": 1.1},
    "II": {"maize": 1.0, "tobacco": 1.0, "soybean": 1.0, "default": 1.0},
    "IIa": {"maize": 1.05, "tobacco": 1.0, "soybean": 1.0, "default": 1.0},
    "IIb": {"maize": 0.95, "tobacco": 0.95, "soybean": 0.95, "default": 0.95},
    "III": {"maize": 0.85, "tobacco": 0.8, "soybean": 0.85, "default": 0.85},
    "IV": {"maize": 0.6, "tobacco": 0.4, "soybean": 0.65, "default": 0.6},
    "V": {"maize": 0.3, "tobacco": 0.2, "soybean": 0.35, "default": 0.3}
}

# Crop-specific base temperatures for GDD calculation
CROP_BASE_TEMPS = {
    "maize": 10.0,
    "tobacco": 10.0,
    "soybean": 10.0,
    "wheat": 4.4,
    "tomato": 10.0,
    "cabbage": 4.4,
    "potato": 7.0,
    "cotton": 15.6,
    "groundnuts": 13.0,
    "sunflower": 8.0,
    "sorghum": 10.0
}

# Standard yield disclaimer
YIELD_DISCLAIMER = """
⚠️ YIELD ESTIMATE DISCLAIMER: This projection is based on variety data, current 
field conditions, and weather patterns. Actual yields depend on many factors 
including rainfall variability, pest/disease pressure, input quality, and 
management practices. Use this as guidance only, not a guarantee. Consult 
local Agritex officers for farm-specific recommendations.
"""


def get_regional_multiplier(
    lat: float, 
    lon: float, 
    crop: str
) -> Tuple[str, float]:
    """
    Determine Zimbabwe Natural Region based on coordinates and return yield multiplier.
    
    Note: This is a simplified mapping. In production, use actual GIS boundaries.
    """
    # Simplified Zimbabwe regional mapping based on latitude/longitude
    # Real implementation should use proper GIS shapefiles
    
    # Approximate regions (very simplified):
    # Region I: Eastern Highlands (high rainfall) - around Mutare, Nyanga
    # Region II: Mashonaland Central/East - good rainfall
    # Region III: Central plateau - moderate rainfall
    # Region IV: Matabeleland, southern lowveld - low rainfall
    # Region V: Extreme south/west - very low rainfall
    
    region = "II"  # Default to Region II
    
    # Eastern Highlands (Region I)
    if lon > 32.5 and lat > -19.5:
        region = "I"
    # Mashonaland (Region II)
    elif lat > -18.5 and lon < 32.0:
        region = "II"
    # Central areas (Region III)
    elif -19.5 < lat < -18.0:
        region = "III"
    # Southern/western areas (Region IV)
    elif lat < -20.5 or lon < 28.0:
        region = "IV"
    # Extreme south (Region V)
    elif lat < -21.5:
        region = "V"
    
    crop_lower = crop.lower()
    multipliers = NATURAL_REGION_MULTIPLIERS.get(region, NATURAL_REGION_MULTIPLIERS["II"])
    multiplier = multipliers.get(crop_lower, multipliers.get("default", 1.0))
    
    return region, multiplier


def calculate_ndvi_factor(ndvi_history: List[float]) -> Tuple[float, str]:
    """
    Calculate yield adjustment factor based on NDVI trajectory.
    
    Returns (factor, explanation)
    - Factor range: 0.6 - 1.15
    - Higher NDVI = healthier crop = higher yield potential
    """
    if not ndvi_history:
        return 0.85, "No satellite data available (using conservative estimate)"
    
    # Use recent readings (last 7 days preferred)
    recent = ndvi_history[-7:] if len(ndvi_history) >= 7 else ndvi_history
    avg_ndvi = sum(recent) / len(recent)
    
    # Check for declining trend (stress indicator)
    if len(ndvi_history) >= 3:
        trend = ndvi_history[-1] - ndvi_history[-3]
        is_declining = trend < -0.05
    else:
        is_declining = False
    
    # Calculate factor based on NDVI value
    # NDVI interpretation:
    # < 0.2: Bare soil or dead vegetation
    # 0.2-0.4: Sparse vegetation or stressed crop
    # 0.4-0.6: Moderate vegetation vigor
    # 0.6-0.8: Healthy, vigorous crop
    # > 0.8: Very healthy, dense canopy
    
    if avg_ndvi < 0.2:
        factor = 0.6
        explanation = f"Very low NDVI ({avg_ndvi:.2f}) indicates severe stress or crop failure"
    elif avg_ndvi < 0.4:
        factor = 0.75
        explanation = f"Low NDVI ({avg_ndvi:.2f}) indicates crop stress - check for pests, diseases, or water deficit"
    elif avg_ndvi < 0.6:
        factor = 0.9
        explanation = f"Moderate NDVI ({avg_ndvi:.2f}) - crop developing normally"
    elif avg_ndvi < 0.8:
        factor = 1.0
        explanation = f"Good NDVI ({avg_ndvi:.2f}) - healthy crop canopy"
    else:
        factor = 1.1
        explanation = f"Excellent NDVI ({avg_ndvi:.2f}) - optimal canopy development"
    
    # Penalize declining trend
    if is_declining:
        factor *= 0.95
        explanation += " (declining trend detected)"
    
    return round(factor, 2), explanation


def calculate_water_factor(
    cumulative_rainfall_mm: float,
    days_since_planting: int,
    crop: str,
    growth_stage_percent: float
) -> Tuple[float, str]:
    """
    Calculate yield adjustment factor based on water availability.
    
    Returns (factor, explanation)
    """
    # Crop water requirements (mm for full season)
    CROP_WATER_REQUIREMENTS = {
        "maize": 500,
        "tobacco": 450,
        "soybean": 450,
        "wheat": 400,
        "tomato": 600,
        "cabbage": 400,
        "potato": 500,
        "cotton": 700,
        "groundnuts": 400,
        "sunflower": 600,
        "sorghum": 400,
        "default": 500
    }
    
    crop_lower = crop.lower()
    total_requirement = CROP_WATER_REQUIREMENTS.get(crop_lower, 500)
    
    # Expected water received by current growth stage
    expected_water = total_requirement * (growth_stage_percent / 100)
    
    if expected_water == 0:
        return 1.0, "Early stage - water assessment pending"
    
    # Calculate adequacy ratio
    adequacy = cumulative_rainfall_mm / expected_water
    
    if adequacy >= 1.2:
        return 1.05, f"Adequate rainfall ({cumulative_rainfall_mm:.0f}mm) - no water stress"
    elif adequacy >= 0.9:
        return 1.0, f"Sufficient rainfall ({cumulative_rainfall_mm:.0f}mm vs {expected_water:.0f}mm expected)"
    elif adequacy >= 0.7:
        factor = 0.85
        explanation = f"Moderate water deficit ({cumulative_rainfall_mm:.0f}mm vs {expected_water:.0f}mm needed)"
    elif adequacy >= 0.5:
        factor = 0.7
        explanation = f"Significant water stress ({adequacy:.0%} of requirement met)"
    else:
        factor = 0.5
        explanation = f"Severe drought stress - only {adequacy:.0%} of water requirement received"
    
    return round(factor, 2), explanation


def calculate_input_factor(
    fertilizer_history: Optional[str],
    crop: str,
    growth_stage_percent: float
) -> Tuple[float, str]:
    """
    Calculate yield adjustment factor based on recorded inputs.
    
    Returns (factor, explanation)
    """
    if not fertilizer_history or fertilizer_history.strip().lower() in ['none', 'n/a', '']:
        if growth_stage_percent < 30:
            return 0.9, "No inputs recorded yet - early season"
        else:
            return 0.75, "No fertilizer application recorded - likely nutrient limited"
    
    fert_lower = fertilizer_history.lower()
    
    # Check for key fertilizers (Zimbabwe common inputs)
    has_basal = any(x in fert_lower for x in ['compound d', 'compound c', 'basal', 'npk'])
    has_topdress = any(x in fert_lower for x in ['an', 'ammonium nitrate', 'top dress', 'urea', 'topdress'])
    has_foliar = any(x in fert_lower for x in ['foliar', 'zinc', 'boron', 'manganese'])
    
    score = 0.8  # Base score
    explanations = []
    
    if has_basal:
        score += 0.1
        explanations.append("basal fertilizer applied")
    if has_topdress:
        score += 0.1
        explanations.append("top-dressing applied")
    if has_foliar:
        score += 0.05
        explanations.append("foliar nutrition recorded")
    
    factor = min(1.15, score)
    explanation = "Inputs recorded: " + ", ".join(explanations) if explanations else "Basic inputs recorded"
    
    return round(factor, 2), explanation


def calculate_variety_factor(
    variety_info: Optional[Dict[str, Any]],
    weather_data: Optional[Dict[str, Any]]
) -> Tuple[float, str]:
    """
    Calculate yield factor based on variety characteristics and current conditions.
    
    Returns (factor, explanation)
    """
    if not variety_info:
        return 0.9, "Variety not in database - using conservative estimate"
    
    chars = variety_info.get('characteristics', {})
    factor = 1.0
    reasons = []
    
    # Drought tolerance assessment
    drought_tolerance = chars.get('drought_tolerance', 'moderate')
    if weather_data:
        humidity = weather_data.get('humidity', 50)
        if humidity < 40 and drought_tolerance in ['low']:
            factor *= 0.9
            reasons.append(f"{variety_info.get('variety_name')} has low drought tolerance")
        elif drought_tolerance in ['very high', 'excellent'] and humidity < 40:
            factor *= 1.05
            reasons.append(f"{variety_info.get('variety_name')} is drought-tolerant variety")
    
    # Disease resistance assessment
    disease_resistance = chars.get('disease_resistance', [])
    if isinstance(disease_resistance, list) and len(disease_resistance) >= 3:
        factor *= 1.05
        reasons.append("strong disease resistance package")
    elif not disease_resistance:
        factor *= 0.95
        reasons.append("limited disease resistance - scout carefully")
    
    # GLS tolerance (critical for maize in Zimbabwe)
    gls_tolerance = chars.get('gls_tolerance', 'moderate')
    if gls_tolerance in ['very high', 'excellent']:
        factor *= 1.02
    elif gls_tolerance == 'low':
        factor *= 0.95
        reasons.append("susceptible to Grey Leaf Spot")
    
    explanation = f"Variety factors: {', '.join(reasons)}" if reasons else "Variety performing within expectations"
    
    return round(factor, 2), explanation


def calculate_confidence_score(
    has_variety_data: bool,
    has_ndvi: bool,
    ndvi_count: int,
    has_weather: bool,
    has_inputs: bool,
    days_since_planting: int,
    growth_stage_percent: float
) -> Tuple[float, List[str]]:
    """
    Calculate confidence score for the projection.
    
    Returns (score, factors_list)
    """
    score = 0.5  # Base confidence
    factors = []
    
    if has_variety_data:
        score += 0.15
        factors.append("✓ Variety data from KurimaSense database")
    else:
        factors.append("⚠ Variety not in database - using estimates")
    
    if has_ndvi:
        if ndvi_count >= 7:
            score += 0.15
            factors.append(f"✓ {ndvi_count} satellite observations")
        else:
            score += 0.08
            factors.append(f"○ Limited satellite data ({ndvi_count} observations)")
    else:
        factors.append("⚠ No satellite imagery available")
    
    if has_weather:
        score += 0.1
        factors.append("✓ Weather data integrated")
    
    if has_inputs:
        score += 0.05
        factors.append("✓ Input records considered")
    else:
        factors.append("○ No input records to factor in")
    
    # Higher confidence later in season
    if growth_stage_percent >= 70:
        score += 0.1
        factors.append("✓ Late season - high prediction confidence")
    elif growth_stage_percent >= 40:
        score += 0.05
        factors.append("○ Mid-season - moderate confidence")
    else:
        factors.append("○ Early season - lower confidence typical")
    
    return round(min(0.95, score), 2), factors


def generate_yield_projection(
    field_id: str,
    crop: str,
    variety: Optional[str],
    planting_date: date,
    area_ha: float,
    coordinates: Optional[List[Dict[str, float]]] = None,
    fertilizer_history: Optional[str] = None,
    ndvi_history: Optional[List[float]] = None,
    weather_data: Optional[Dict[str, Any]] = None,
    cumulative_rainfall_mm: float = 0.0,
    transplant_date: Optional[date] = None,
    is_transplanted: bool = False
) -> YieldProjection:
    """
    Generate agronomically-grounded yield projection.
    
    This is the main entry point for yield calculations.
    """
    # 1. Get variety data from database
    variety_info = get_variety_info(variety) if variety else None
    
    # Determine base yield potentials
    if variety_info:
        base_yield_low = float(variety_info.get('yield_potential_low', 4.0))
        base_yield_high = float(variety_info.get('yield_potential_high', 8.0))
        days_to_maturity = variety_info.get('days_to_maturity', 140)
    else:
        # Default yields by crop (conservative estimates for Zimbabwe)
        DEFAULT_YIELDS = {
            "maize": (4.0, 10.0),
            "tobacco": (1.5, 3.0),
            "soybean": (2.0, 3.5),
            "wheat": (3.5, 6.0),
            "tomato": (30.0, 60.0),
            "cabbage": (40.0, 80.0),
            "potato": (20.0, 40.0),
            "cotton": (2.0, 4.0),
            "groundnuts": (1.5, 3.0),
            "sunflower": (1.5, 3.0),
            "sorghum": (2.5, 5.0)
        }
        yields = DEFAULT_YIELDS.get(crop.lower(), (3.0, 6.0))
        base_yield_low, base_yield_high = yields
        days_to_maturity = 140
    
    base_yield_mid = (base_yield_low + base_yield_high) / 2
    
    # 2. Calculate growth stage
    growth_stage = calculate_growth_stage(
        planting_date=planting_date,
        variety_name=variety or "Generic",
        crop_type=crop,
        transplant_date=transplant_date,
        is_transplanted=is_transplanted
    )
    
    # 3. Get regional multiplier if coordinates available
    if coordinates and len(coordinates) > 0:
        avg_lat = sum(p.get('lat', -17.82) for p in coordinates) / len(coordinates)
        avg_lon = sum(p.get('lon', 31.05) for p in coordinates) / len(coordinates)
    else:
        avg_lat, avg_lon = -17.82, 31.05  # Default to Harare
    
    region, region_multiplier = get_regional_multiplier(avg_lat, avg_lon, crop)
    
    # 4. Calculate individual adjustment factors
    ndvi_factor, ndvi_explanation = calculate_ndvi_factor(ndvi_history or [])
    water_factor, water_explanation = calculate_water_factor(
        cumulative_rainfall_mm, 
        growth_stage.days_since_planting,
        crop,
        growth_stage.progress_percent
    )
    input_factor, input_explanation = calculate_input_factor(
        fertilizer_history, 
        crop,
        growth_stage.progress_percent
    )
    variety_factor, variety_explanation = calculate_variety_factor(variety_info, weather_data)
    
    # 5. Combine all factors
    combined_factor = (
        region_multiplier *
        ndvi_factor *
        water_factor *
        input_factor *
        variety_factor
    )
    
    # 6. Calculate final projections
    projected_yield = base_yield_mid * combined_factor
    yield_low = base_yield_low * combined_factor * 0.9
    yield_high = base_yield_high * combined_factor * 1.05
    
    # Ensure projections are reasonable
    projected_yield = max(base_yield_low * 0.3, min(base_yield_high * 1.2, projected_yield))
    yield_low = max(0, yield_low)
    yield_high = max(projected_yield, yield_high)
    
    # 7. Calculate confidence score
    confidence_score, confidence_factors = calculate_confidence_score(
        has_variety_data=variety_info is not None,
        has_ndvi=bool(ndvi_history),
        ndvi_count=len(ndvi_history) if ndvi_history else 0,
        has_weather=weather_data is not None,
        has_inputs=bool(fertilizer_history and fertilizer_history.strip()),
        days_since_planting=growth_stage.days_since_planting,
        growth_stage_percent=growth_stage.progress_percent
    )
    
    # 8. Generate yield gap analysis
    potential_yield = base_yield_high * region_multiplier
    gap_percent = ((potential_yield - projected_yield) / potential_yield) * 100 if potential_yield > 0 else 0
    
    if gap_percent < 10:
        yield_gap_analysis = f"Excellent performance! Projected yield is within {gap_percent:.0f}% of variety potential."
    elif gap_percent < 25:
        yield_gap_analysis = f"{gap_percent:.0f}% yield gap detected. Key limiting factors: {ndvi_explanation.split('-')[0] if ndvi_factor < 0.95 else water_explanation.split('-')[0] if water_factor < 0.95 else 'minor stress factors'}."
    else:
        limiting_factors = []
        if ndvi_factor < 0.9:
            limiting_factors.append("crop health")
        if water_factor < 0.9:
            limiting_factors.append("water stress")
        if input_factor < 0.9:
            limiting_factors.append("nutrient limitation")
        yield_gap_analysis = f"{gap_percent:.0f}% yield gap. Primary limiting factors: {', '.join(limiting_factors) if limiting_factors else 'environmental stress'}. Consider consulting Agritex for field assessment."
    
    # 9. Build confidence factors list
    all_factors = [
        f"Variety: {variety or 'Unknown'} ({base_yield_low}-{base_yield_high} t/ha potential)",
        f"Region: Natural Region {region} (×{region_multiplier:.2f})",
        ndvi_explanation,
        water_explanation,
        input_explanation,
        variety_explanation
    ]
    
    return YieldProjection(
        projected_yield=round(projected_yield, 2),
        yield_potential=round(base_yield_high * region_multiplier, 2),
        confidence_bands={
            "low": round(yield_low, 2),
            "mid": round(projected_yield, 2),
            "high": round(yield_high, 2)
        },
        confidence_score=confidence_score,
        confidence_factors=confidence_factors,
        yield_gap_analysis=yield_gap_analysis,
        methodology="KurimaSense Agronomic Model v1.0 - variety-grounded",
        adjustment_factors={
            "region_multiplier": region_multiplier,
            "ndvi_factor": ndvi_factor,
            "water_factor": water_factor,
            "input_factor": input_factor,
            "variety_factor": variety_factor,
            "combined_factor": round(combined_factor, 3)
        },
        disclaimer=YIELD_DISCLAIMER.strip()
    )


def get_field_ndvi_history(field_id: str, days: int = 30) -> List[float]:
    """Fetch NDVI history for a field from daily_logs."""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ndvi FROM daily_logs 
            WHERE field_id = %s AND ndvi IS NOT NULL
            ORDER BY log_date DESC
            LIMIT %s
        """, (field_id, days))
        
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Return in chronological order (oldest first)
        return [float(r['ndvi']) for r in reversed(rows)]
    except Exception as e:
        print(f"NDVI history fetch error: {e}")
        if conn:
            conn.close()
        return []


# Export for use in app.py
__all__ = [
    'YieldProjection',
    'generate_yield_projection',
    'get_field_ndvi_history',
    'YIELD_DISCLAIMER'
]
