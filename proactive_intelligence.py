"""
KurimaSense Proactive Intelligence Service
==========================================
Generates variety-aware alerts based on growth stage, weather, and crop characteristics.

Features:
- Growth stage calculation from planting date + variety maturity
- Disease risk alerts using variety resistance + current weather
- Harvest countdown notifications
- Variety-specific agronomic recommendations
"""

from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from database import get_db_connection
from ai_brain import get_brain
from crop_profiles import (
    get_crop_profile, get_diseases_for_conditions, get_pests_for_stage,
    get_current_stage_for_crop as ck_get_stage,
)


class GrowthStage(Enum):
    """Crop growth stages for cereals (maize-based)."""
    GERMINATION = "Germination"
    VE = "VE - Emergence"
    V1_V3 = "V1-V3 - Early Vegetative"
    V4_V6 = "V4-V6 - Mid Vegetative"
    V7_V10 = "V7-V10 - Late Vegetative"
    VT = "VT - Tasseling"
    R1 = "R1 - Silking"
    R2 = "R2 - Blister"
    R3 = "R3 - Milk"
    R4 = "R4 - Dough"
    R5 = "R5 - Dent"
    R6 = "R6 - Physiological Maturity"
    HARVEST_READY = "Harvest Ready"


class TobaccoStage(Enum):
    """Tobacco growth stages."""
    TRANSPLANT = "Transplanted"
    ESTABLISHMENT = "Establishment (0-3 weeks)"
    RAPID_GROWTH = "Rapid Growth (3-8 weeks)"
    TOPPING = "Topping Stage"
    RIPENING = "Ripening"
    HARVEST = "Harvest Ready"


class VegetableStage(Enum):
    """Generic vegetable growth stages."""
    SEEDLING = "Seedling/Transplant"
    VEGETATIVE = "Vegetative Growth"
    HEADING = "Head Formation"  # For cabbage
    BULBING = "Bulb Formation"  # For onion
    FLOWERING = "Flowering"     # For tomato
    FRUITING = "Fruiting"
    MATURITY = "Maturity"
    HARVEST_READY = "Harvest Ready"


@dataclass
class GrowthStageInfo:
    """Information about current growth stage."""
    stage_name: str
    stage_code: str
    days_in_stage: int
    days_since_planting: int
    days_to_harvest: int
    progress_percent: float
    description: str
    key_activities: List[str]
    risks: List[str]


@dataclass
class ProactiveAlert:
    """A proactive alert for the farmer."""
    id: str
    alert_type: str  # 'disease_risk', 'pest_risk', 'harvest', 'weather', 'nutrient', 'growth_stage'
    severity: str    # 'info', 'warning', 'critical'
    title: str
    message: str
    variety_name: Optional[str]
    field_name: Optional[str]
    action_required: bool
    recommended_actions: List[str]
    triggered_by: Dict[str, Any]  # What triggered this alert
    created_at: str


def get_variety_info(variety_name: str) -> Optional[Dict[str, Any]]:
    """Fetch variety information from the database."""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT crop_name, variety_name, breeder, days_to_maturity, 
                   yield_potential_low, yield_potential_high, characteristics
            FROM crop_varieties 
            WHERE variety_name ILIKE %s
            LIMIT 1
        """, (f"%{variety_name}%",))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return {
                "crop_name": row['crop_name'],
                "variety_name": row['variety_name'],
                "breeder": row['breeder'],
                "days_to_maturity": row['days_to_maturity'],
                "yield_potential_low": float(row['yield_potential_low'] or 0),
                "yield_potential_high": float(row['yield_potential_high'] or 0),
                "characteristics": row['characteristics'] or {}
            }
        return None
        
    except Exception as e:
        print(f"Variety lookup error: {e}")
        if conn: conn.close()
        return None


def calculate_growth_stage(
    planting_date: date,
    variety_name: str,
    crop_type: str = "Maize",
    transplant_date: Optional[date] = None,
    is_transplanted: bool = False
) -> GrowthStageInfo:
    """
    Calculate the current growth stage based on planting date and variety.
    
    Uses variety-specific days_to_maturity for accurate staging.
    
    For transplanted crops (Tomato, Cabbage, Onion, Potato), uses transplant_date
    instead of planting_date to track "Days from Transplant" not "Days from Seed".
    The nursery period (4-6 weeks) is not counted towards field growth stages.
    
    Args:
        planting_date: Date seeds were sown (or transplants if not a transplanted crop)
        variety_name: Name of the variety for maturity lookup
        crop_type: Type of crop
        transplant_date: Date seedlings were transplanted to field (for vegetables)
        is_transplanted: Whether this is a transplanted crop
    """
    today = date.today()
    
    # Determine if this is a transplanted crop
    TRANSPLANTED_CROPS = ['tomato', 'cabbage', 'onion', 'potato', 'pepper', 'eggplant', 'lettuce']
    use_transplant_date = is_transplanted or crop_type.lower() in TRANSPLANTED_CROPS
    
    # For transplanted crops, use transplant_date for growth stage calculations
    effective_start_date = planting_date
    if use_transplant_date and transplant_date:
        effective_start_date = transplant_date
        print(f"🌱 Using transplant_date ({transplant_date}) for {crop_type} growth stage (Days from Transplant)")
    
    days_since_start = (today - effective_start_date).days
    
    # Get variety info for accurate maturity
    variety_info = get_variety_info(variety_name)
    days_to_maturity = 140  # Default
    
    if variety_info:
        days_to_maturity = variety_info.get('days_to_maturity', 140)
        # For transplanted crops, maturity is typically measured from transplant
        # The variety's days_to_maturity already reflects this
    
    days_to_harvest = max(0, days_to_maturity - days_since_start)
    progress_percent = min(100, (days_since_start / days_to_maturity) * 100)
    
    # Determine growth stage based on crop type
    if crop_type.lower() in ['maize', 'corn']:
        return _calculate_maize_stage(days_since_start, days_to_maturity, days_to_harvest, progress_percent)
    elif crop_type.lower() == 'tobacco':
        return _calculate_tobacco_stage(days_since_start, days_to_maturity, days_to_harvest, progress_percent)
    elif crop_type.lower() in ['tomato', 'cabbage', 'onion', 'potato']:
        return _calculate_vegetable_stage(days_since_start, days_to_maturity, days_to_harvest, progress_percent, crop_type)
    elif crop_type.lower() in ['soybeans', 'soybean']:
        return _calculate_soybean_stage(days_since_start, days_to_maturity, days_to_harvest, progress_percent)
    else:
        # Generic stage calculation
        return _calculate_generic_stage(days_since_start, days_to_maturity, days_to_harvest, progress_percent, crop_type)


def _calculate_maize_stage(days: int, maturity: int, days_to_harvest: int, progress: float) -> GrowthStageInfo:
    """Calculate maize growth stage using GDD-approximated day ranges."""
    
    # Stage breakpoints (percentage of total maturity)
    if days < 7:
        stage = GrowthStage.GERMINATION
        desc = "Seeds germinating underground. Radicle and coleoptile emerging."
        activities = ["Ensure adequate soil moisture", "Monitor for seed rot"]
        risks = ["Seed rot if waterlogged", "Poor emergence if soil crusted"]
    elif days < 14:
        stage = GrowthStage.VE
        desc = "Coleoptile has emerged through soil surface."
        activities = ["Scout for cutworms", "Check plant population"]
        risks = ["Cutworm damage", "Bird damage to seedlings"]
    elif days < 28:
        stage = GrowthStage.V1_V3
        desc = "1-3 leaves with visible collars. Critical stage for Nitrogen Use Efficiency (NUE) foundation. Root system establishing."
        activities = ["Apply post-emergence herbicide if needed", "Scout for Fall Armyworm"]
        risks = ["Fall Armyworm in whorl (check for window-pane damage)", "Weed competition"]
    elif days < 42:
        stage = GrowthStage.V4_V6
        desc = "4-6 leaves. Growing point above soil. High Nitrogen demand. Soil pH affects P-availability significantly now."
        activities = ["Side-dress nitrogen (AN)", "Scout for stalk borers", "Monitor for Grey Leaf Spot"]
        risks = ["GLS initiation in humid conditions", "N-deficiency (yellowing V-shape on lower leaves)", "Stalk borer"]
    elif days < 56:
        stage = GrowthStage.V7_V10
        desc = "7-10 leaves. Ear shoot and tassel developing rapidly."
        activities = ["Final nitrogen application", "Scout for GLS and rust"]
        risks = ["Grey Leaf Spot spreading", "Common rust", "Drought stress critical"]
    elif days < 70:
        stage = GrowthStage.VT
        desc = "Tasseling - last branch of tassel visible. Critical water demand."
        activities = ["Ensure irrigation if dry", "Scout for silk clipping insects"]
        risks = ["Drought stress = yield loss", "Silk clipping by beetles"]
    elif days < 77:
        stage = GrowthStage.R1
        desc = "Silking - silks visible. Pollination occurring."
        activities = ["Maintain irrigation", "Do NOT spray fungicides during pollination"]
        risks = ["Poor pollination if drought", "Silk damage reduces kernel set"]
    elif days < 90:
        stage = GrowthStage.R2
        desc = "Blister stage - kernels like blisters with clear fluid."
        activities = ["Maintain moisture", "Scout for ear rots"]
        risks = ["Kernel abortion if stressed", "Ear rot initiation"]
    elif days < 100:
        stage = GrowthStage.R3
        desc = "Milk stage - kernels yellow outside, milky inside."
        activities = ["Scout for ear rots", "Plan harvest logistics"]
        risks = ["Diplodia ear rot", "Aflatoxin risk in drought"]
    elif days < 115:
        stage = GrowthStage.R4
        desc = "Dough stage - kernels have pasty consistency."
        activities = ["Monitor grain moisture", "Scout for stalk rots"]
        risks = ["Stalk rot increasing", "Lodging risk"]
    elif days < 130:
        stage = GrowthStage.R5
        desc = "Dent stage - kernels denting at top. Black layer forming."
        activities = ["Prepare harvesting equipment", "Check grain moisture"]
        risks = ["Lodging", "Ear drop", "Bird/rodent damage"]
    elif days < maturity:
        stage = GrowthStage.R6
        desc = "Physiological maturity - black layer formed. Max dry weight."
        activities = ["Allow field drying to 12-14% moisture", "Begin harvest when ready"]
        risks = ["Field losses if delayed", "Weather damage"]
    else:
        stage = GrowthStage.HARVEST_READY
        desc = "Crop is ready for harvest!"
        activities = ["Harvest immediately", "Monitor grain moisture (target 12.5%)"]
        risks = ["Field losses increasing daily", "Quality deterioration"]
    
    return GrowthStageInfo(
        stage_name=stage.value,
        stage_code=stage.name,
        days_in_stage=days % 14,  # Approximate
        days_since_planting=days,
        days_to_harvest=days_to_harvest,
        progress_percent=round(progress, 1),
        description=desc,
        key_activities=activities,
        risks=risks
    )


def _calculate_tobacco_stage(days: int, maturity: int, days_to_harvest: int, progress: float) -> GrowthStageInfo:
    """Calculate tobacco growth stage."""
    
    if days < 21:
        stage = TobaccoStage.ESTABLISHMENT
        desc = "Plants establishing root system after transplant."
        activities = ["Water regularly", "Scout for cutworms", "Replace dead plants"]
        risks = ["Transplant shock", "Cutworm damage", "Damping off"]
    elif days < 56:
        stage = TobaccoStage.RAPID_GROWTH
        desc = "Rapid vegetative growth. Leaves expanding."
        activities = ["Apply nitrogen (AN)", "Scout for aphids and budworm", "Monitor for frog-eye leaf spot"]
        risks = ["Aphid infestation", "Budworm damage", "Frog-eye leaf spot"]
    elif days < 70:
        stage = TobaccoStage.TOPPING
        desc = "Flower bud visible. Time for topping."
        activities = ["Top plants (remove flower)", "Apply sucker control", "Final fertilizer"]
        risks = ["Delayed topping reduces yield", "Sucker regrowth"]
    elif days < maturity - 14:
        stage = TobaccoStage.RIPENING
        desc = "Leaves ripening from bottom up. Color changing."
        activities = ["Prime lower leaves as they ripen", "Prepare curing barns"]
        risks = ["Over-ripening", "Weather damage to ripe leaves"]
    else:
        stage = TobaccoStage.HARVEST
        desc = "Ready for final harvest. All leaves should be ripe."
        activities = ["Complete harvest", "Begin curing immediately"]
        risks = ["Quality loss if delayed", "Barn capacity"]
    
    return GrowthStageInfo(
        stage_name=stage.value,
        stage_code=stage.name,
        days_in_stage=days % 21,
        days_since_planting=days,
        days_to_harvest=days_to_harvest,
        progress_percent=round(progress, 1),
        description=desc,
        key_activities=activities,
        risks=risks
    )


def _calculate_vegetable_stage(days: int, maturity: int, days_to_harvest: int, progress: float, crop: str) -> GrowthStageInfo:
    """Calculate vegetable growth stages."""
    
    crop_lower = crop.lower()
    
    # Different vegetables have different stage progressions
    if crop_lower == 'cabbage':
        if days < 21:
            stage_name = "Establishment"
            desc = "Transplants establishing. Roots developing."
            activities = ["Water regularly", "Scout for cutworms", "Apply starter fertilizer"]
            risks = ["Transplant shock", "Cutworm damage"]
        elif days < 45:
            stage_name = "Frame Development"
            desc = "Outer leaves (frame) growing rapidly."
            activities = ["Apply nitrogen side-dress", "Scout for diamondback moth"]
            risks = ["Diamondback moth", "Black rot if wet"]
        elif days < 70:
            stage_name = "Head Formation"
            desc = "Head beginning to form and fill."
            activities = ["Maintain consistent moisture", "Scout for head rot"]
            risks = ["Head splitting if uneven watering", "Tipburn"]
        else:
            stage_name = "Maturity"
            desc = "Heads firm and ready for harvest."
            activities = ["Harvest when heads are firm (4-6 kg)", "Don't delay - heads will split"]
            risks = ["Head splitting", "Bolting if hot"]
            
    elif crop_lower == 'tomato':
        if days < 14:
            stage_name = "Establishment"
            desc = "Transplants establishing after planting."
            activities = ["Stake/cage plants", "Water regularly"]
            risks = ["Transplant shock", "Cutworm damage"]
        elif days < 35:
            stage_name = "Vegetative"
            desc = "Vines growing rapidly."
            activities = ["Train vines", "Remove suckers (determinate)", "Apply calcium"]
            risks = ["Blossom end rot", "Early blight"]
        elif days < 55:
            stage_name = "Flowering"
            desc = "Flowers appearing and setting fruit."
            activities = ["Ensure pollination", "Maintain even watering"]
            risks = ["Poor fruit set if too hot", "Blossom drop"]
        elif days < maturity - 10:
            stage_name = "Fruit Development"
            desc = "Fruits sizing and maturing."
            activities = ["Scout for fruit worms", "Maintain calcium", "Reduce nitrogen"]
            risks = ["Fruit worms", "Cracking", "Blossom end rot"]
        else:
            stage_name = "Harvest"
            desc = "Fruits ready for harvest."
            activities = ["Harvest at breaker stage for shipping", "Harvest red-ripe for local market"]
            risks = ["Over-ripening", "Bird damage"]
    else:
        # Generic vegetable
        pct = (days / maturity) * 100
        if pct < 25:
            stage_name = "Establishment"
            desc = "Early growth and establishment."
            activities = ["Ensure adequate water", "Scout for pests"]
            risks = ["Establishment failure"]
        elif pct < 50:
            stage_name = "Vegetative Growth"
            desc = "Active vegetative growth."
            activities = ["Fertilize", "Weed control"]
            risks = ["Nutrient deficiency", "Weed competition"]
        elif pct < 75:
            stage_name = "Reproductive"
            desc = "Reproductive growth phase."
            activities = ["Maintain conditions", "Scout for diseases"]
            risks = ["Disease pressure"]
        else:
            stage_name = "Maturity"
            desc = "Approaching harvest."
            activities = ["Prepare for harvest"]
            risks = ["Over-maturity"]
    
    return GrowthStageInfo(
        stage_name=stage_name,
        stage_code=stage_name.upper().replace(" ", "_"),
        days_in_stage=days % 14,
        days_since_planting=days,
        days_to_harvest=days_to_harvest,
        progress_percent=round(progress, 1),
        description=desc,
        key_activities=activities,
        risks=risks
    )


def _calculate_soybean_stage(days: int, maturity: int, days_to_harvest: int, progress: float) -> GrowthStageInfo:
    """Calculate soybean growth stages."""
    
    if days < 10:
        stage_name = "VE - Emergence"
        desc = "Cotyledons above soil surface."
        activities = ["Check plant stand", "Scout for seedling diseases"]
        risks = ["Poor emergence", "Seedling diseases"]
    elif days < 30:
        stage_name = "V1-V3 - Early Vegetative"
        desc = "First trifoliate leaves developing."
        activities = ["Post-emergence herbicide", "Scout for defoliators"]
        risks = ["Weed competition", "Defoliating insects"]
    elif days < 50:
        stage_name = "V4-V6 - Mid Vegetative"
        desc = "Rapid vegetative growth. Nodes developing."
        activities = ["Scout for soybean rust", "Monitor soil moisture"]
        risks = ["Soybean rust", "Drought stress"]
    elif days < 65:
        stage_name = "R1-R2 - Flowering"
        desc = "Flowering beginning. Critical period."
        activities = ["Apply fungicide if rust present", "Irrigate if dry"]
        risks = ["Flower abortion if stressed", "Rust spreading"]
    elif days < 85:
        stage_name = "R3-R4 - Pod Development"
        desc = "Pods forming and developing."
        activities = ["Scout for pod-sucking bugs", "Final fungicide if needed"]
        risks = ["Pod-sucking bugs", "Pod diseases"]
    elif days < maturity - 14:
        stage_name = "R5-R6 - Seed Fill"
        desc = "Seeds filling in pods."
        activities = ["Maintain moisture", "Scout for pod diseases"]
        risks = ["Seed size reduction if stressed", "Pod shattering"]
    else:
        stage_name = "R7-R8 - Maturity"
        desc = "Pods mature, leaves yellowing/dropping."
        activities = ["Prepare for harvest", "Monitor moisture (13%)", "Apply desiccant if needed"]
        risks = ["Pod shattering", "Harvest losses"]
    
    return GrowthStageInfo(
        stage_name=stage_name,
        stage_code=stage_name.split(" - ")[0],
        days_in_stage=days % 15,
        days_since_planting=days,
        days_to_harvest=days_to_harvest,
        progress_percent=round(progress, 1),
        description=desc,
        key_activities=activities,
        risks=risks
    )


def _calculate_generic_stage(days: int, maturity: int, days_to_harvest: int, progress: float, crop: str) -> GrowthStageInfo:
    """Generic growth stage calculation for other crops."""
    
    pct = progress
    
    if pct < 15:
        stage_name = "Germination/Emergence"
        desc = f"{crop} emerging from soil."
        activities = ["Monitor emergence", "Ensure adequate moisture"]
        risks = ["Poor emergence"]
    elif pct < 35:
        stage_name = "Early Vegetative"
        desc = "Early growth and establishment."
        activities = ["Apply early fertilizer", "Weed control"]
        risks = ["Weed competition", "Nutrient deficiency"]
    elif pct < 55:
        stage_name = "Active Growth"
        desc = "Rapid vegetative growth."
        activities = ["Side-dress fertilizer", "Scout for pests/diseases"]
        risks = ["Pest pressure", "Disease"]
    elif pct < 75:
        stage_name = "Reproductive"
        desc = "Flowering/fruiting phase."
        activities = ["Maintain optimal conditions", "Protect from stress"]
        risks = ["Stress reduces yield"]
    elif pct < 95:
        stage_name = "Maturation"
        desc = "Crop maturing, preparing for harvest."
        activities = ["Reduce irrigation", "Prepare harvest equipment"]
        risks = ["Over-maturity", "Weather damage"]
    else:
        stage_name = "Harvest Ready"
        desc = "Ready for harvest!"
        activities = ["Harvest promptly"]
        risks = ["Yield losses if delayed"]
    
    return GrowthStageInfo(
        stage_name=stage_name,
        stage_code=stage_name.upper().replace(" ", "_").replace("/", "_"),
        days_in_stage=days % 14,
        days_since_planting=days,
        days_to_harvest=days_to_harvest,
        progress_percent=round(progress, 1),
        description=desc,
        key_activities=activities,
        risks=risks
    )


def assess_disease_risk(
    variety_info: Dict[str, Any],
    weather_data: Dict[str, Any],
    growth_stage: GrowthStageInfo
) -> List[ProactiveAlert]:
    """
    Assess disease risk based on variety resistance + current weather.
    
    High humidity + warm temps = fungal disease risk
    Variety resistance profile determines severity
    """
    alerts = []
    now = datetime.now().isoformat()
    
    if not variety_info or not weather_data:
        return alerts
    
    chars = variety_info.get('characteristics', {})
    disease_resistance = chars.get('disease_resistance', [])
    gls_tolerance = chars.get('gls_tolerance', 'moderate')
    drought_tolerance = chars.get('drought_tolerance', 'moderate')
    
    humidity = weather_data.get('humidity', 50)
    temperature = weather_data.get('temperature', 25)
    precipitation = weather_data.get('precipitation', 0)
    
    variety_name = variety_info.get('variety_name', 'Unknown')
    crop = variety_info.get('crop_name', 'Crop')
    
    # Grey Leaf Spot risk (Maize) - High humidity + warm nights
    if crop.lower() == 'maize' and humidity > 80 and temperature > 20:
        # Check variety tolerance
        if gls_tolerance in ['low', 'moderate']:
            severity = 'critical' if gls_tolerance == 'low' else 'warning'
            alerts.append(ProactiveAlert(
                id=f"gls-risk-{now}",
                alert_type="disease_risk",
                severity=severity,
                title="⚠️ Grey Leaf Spot Risk - HIGH",
                message=f"Current conditions (humidity {humidity}%, temp {temperature}°C) favor Grey Leaf Spot. "
                        f"{variety_name} has {gls_tolerance} GLS tolerance - scout immediately!",
                variety_name=variety_name,
                field_name=None,
                action_required=True,
                recommended_actions=[
                    "Scout field for GLS lesions (rectangular, grey-tan)",
                    "Apply fungicide if >50% leaves affected at V8-VT",
                    "Consider Amistar/Nativo at 0.4-0.5 L/ha",
                    "Re-scout in 5-7 days"
                ],
                triggered_by={"humidity": humidity, "temperature": temperature, "gls_tolerance": gls_tolerance},
                created_at=now
            ))
        elif gls_tolerance == 'very high':
            alerts.append(ProactiveAlert(
                id=f"gls-info-{now}",
                alert_type="disease_risk",
                severity="info",
                title="ℹ️ GLS Conditions Present - Low Risk",
                message=f"GLS-favorable weather detected, but {variety_name} has very high tolerance. Monitor but don't panic.",
                variety_name=variety_name,
                field_name=None,
                action_required=False,
                recommended_actions=["Routine scouting", "No fungicide needed unless severe outbreak"],
                triggered_by={"humidity": humidity, "gls_tolerance": gls_tolerance},
                created_at=now
            ))
    
    # Rust risk (various crops)
    if humidity > 75 and 15 < temperature < 25:
        rust_resistant = any('rust' in str(r).lower() for r in disease_resistance)
        if not rust_resistant:
            alerts.append(ProactiveAlert(
                id=f"rust-risk-{now}",
                alert_type="disease_risk",
                severity="warning",
                title="🟠 Rust Risk Elevated",
                message=f"Cool, humid conditions favor rust development. {variety_name} does not have documented rust resistance.",
                variety_name=variety_name,
                field_name=None,
                action_required=True,
                recommended_actions=[
                    "Scout for rust pustules (orange-brown) on lower leaves",
                    "Apply fungicide preventatively if rust history",
                    "Improve air circulation if possible"
                ],
                triggered_by={"humidity": humidity, "temperature": temperature},
                created_at=now
            ))
    
    # Drought stress warning
    if precipitation == 0 and humidity < 40 and drought_tolerance in ['low', 'moderate']:
        alerts.append(ProactiveAlert(
            id=f"drought-stress-{now}",
            alert_type="weather",
            severity="warning" if drought_tolerance == 'low' else "info",
            title="🌵 Drought Stress Risk",
            message=f"Dry conditions detected. {variety_name} has {drought_tolerance} drought tolerance. "
                    f"Consider irrigation if soil moisture is low.",
            variety_name=variety_name,
            field_name=None,
            action_required=drought_tolerance == 'low',
            recommended_actions=[
                "Check soil moisture at 15cm depth",
                "Irrigate 25-30mm if soil dry",
                "Apply mulch to conserve moisture",
                "Avoid fertilizer application until moisture improves"
            ],
            triggered_by={"precipitation": precipitation, "humidity": humidity, "drought_tolerance": drought_tolerance},
            created_at=now
        ))
    
    # --- ENHANCED: Use crop_knowledge engine for additional disease/pest risks ---
    try:
        stage_code = growth_stage.stage_code if growth_stage else ""
        ck_diseases = get_diseases_for_conditions(crop, temperature, humidity, stage_code)
        ck_pests = get_pests_for_stage(crop, stage_code)

        # Add any high-risk diseases not already covered by the hardcoded checks above
        existing_titles = {a.title.lower() for a in alerts}
        for d in ck_diseases:
            if d["risk_level"] in ("high", "moderate"):
                title_check = d["disease"].lower()
                if not any(title_check in t for t in existing_titles):
                    alerts.append(ProactiveAlert(
                        id=f"ck-disease-{d['disease'].replace(' ', '-').lower()}-{now}",
                        alert_type="disease_risk",
                        severity="warning" if d["risk_level"] == "moderate" else "critical",
                        title=f"{'🔴' if d['risk_level'] == 'high' else '🟡'} {d['disease']} Risk — {d['risk_level'].upper()}",
                        message=f"{d['disease']} ({d['pathogen']}): {'; '.join(d['reasons'])}. "
                                f"Look for: {d['scouting_tip']}",
                        variety_name=variety_name,
                        field_name=None,
                        action_required=d["risk_level"] == "high",
                        recommended_actions=[
                            str(a) if isinstance(a, str) else a.get("name", str(a))
                            for a in d.get("recommended_actions", [])
                        ],
                        triggered_by={"risk_score": d["risk_score"], "source": "crop_knowledge_engine"},
                        created_at=now,
                    ))

        # Add stage-specific pest alerts
        for p in ck_pests[:2]:
            alerts.append(ProactiveAlert(
                id=f"ck-pest-{p['pest'].replace(' ', '-').lower()}-{now}",
                alert_type="pest_risk",
                severity="info",
                title=f"🐛 {p['pest']} — Scout Now",
                message=f"At growth stage {stage_code}, {p['pest']} ({p['scientific_name']}) is a key pest. "
                        f"Look for: {', '.join(p['damage_to_look_for'])}. "
                        f"Economic threshold: {p['economic_threshold']}.",
                variety_name=variety_name,
                field_name=None,
                action_required=False,
                recommended_actions=[
                    f"Scouting: {p['scouting_protocol'][:150]}",
                    f"Top control: {p['top_control']}",
                ],
                triggered_by={"stage": stage_code, "source": "crop_knowledge_engine"},
                created_at=now,
            ))
    except Exception as e:
        print(f"Crop knowledge engine disease/pest enhancement failed: {e}")

    return alerts


def generate_harvest_alert(
    growth_stage: GrowthStageInfo,
    variety_info: Dict[str, Any],
    field_name: Optional[str] = None
) -> Optional[ProactiveAlert]:
    """Generate harvest countdown alerts."""
    
    if not variety_info:
        return None
    
    days_to_harvest = growth_stage.days_to_harvest
    variety_name = variety_info.get('variety_name', 'Unknown')
    crop = variety_info.get('crop_name', 'Crop')
    now = datetime.now().isoformat()
    
    if days_to_harvest <= 0:
        return ProactiveAlert(
            id=f"harvest-ready-{now}",
            alert_type="harvest",
            severity="critical",
            title=f"🌾 {crop} Ready for Harvest!",
            message=f"{variety_name} has reached maturity ({variety_info.get('days_to_maturity')} days). "
                    f"Harvest immediately to avoid field losses.",
            variety_name=variety_name,
            field_name=field_name,
            action_required=True,
            recommended_actions=[
                f"Harvest {crop.lower()} at optimal moisture",
                "Check equipment is ready",
                "Arrange transport/storage",
                "Monitor weather for harvest window"
            ],
            triggered_by={"days_to_harvest": days_to_harvest, "progress": growth_stage.progress_percent},
            created_at=now
        )
    
    elif days_to_harvest <= 7:
        return ProactiveAlert(
            id=f"harvest-soon-{now}",
            alert_type="harvest",
            severity="warning",
            title=f"📅 Harvest in {days_to_harvest} days",
            message=f"{variety_name} will be ready for harvest in approximately {days_to_harvest} days. "
                    f"Start preparing now!",
            variety_name=variety_name,
            field_name=field_name,
            action_required=True,
            recommended_actions=[
                "Service harvesting equipment",
                "Arrange labor/contractors",
                "Prepare drying/storage facilities",
                "Check long-term weather forecast"
            ],
            triggered_by={"days_to_harvest": days_to_harvest},
            created_at=now
        )
    
    elif days_to_harvest <= 14:
        return ProactiveAlert(
            id=f"harvest-2weeks-{now}",
            alert_type="harvest",
            severity="info",
            title=f"📆 ~{days_to_harvest} days to harvest",
            message=f"{variety_name} is {growth_stage.progress_percent:.0f}% through its growth cycle. "
                    f"Expected harvest in {days_to_harvest} days.",
            variety_name=variety_name,
            field_name=field_name,
            action_required=False,
            recommended_actions=[
                "Begin harvest planning",
                "Scout for late-season diseases",
                "Monitor grain/fruit maturity"
            ],
            triggered_by={"days_to_harvest": days_to_harvest},
            created_at=now
        )
    
    return None


def generate_growth_stage_alert(
    growth_stage: GrowthStageInfo,
    variety_info: Dict[str, Any],
    field_name: Optional[str] = None
) -> ProactiveAlert:
    """Generate an informational alert about current growth stage."""
    
    variety_name = variety_info.get('variety_name', 'Unknown') if variety_info else 'Unknown'
    crop = variety_info.get('crop_name', 'Crop') if variety_info else 'Crop'
    now = datetime.now().isoformat()
    
    return ProactiveAlert(
        id=f"growth-stage-{now}",
        alert_type="growth_stage",
        severity="info",
        title=f"🌱 {crop} at {growth_stage.stage_name}",
        message=f"{variety_name} is {growth_stage.days_since_planting} days old, at {growth_stage.stage_name} stage. "
                f"{growth_stage.description}",
        variety_name=variety_name,
        field_name=field_name,
        action_required=len(growth_stage.key_activities) > 0,
        recommended_actions=growth_stage.key_activities,
        triggered_by={
            "stage": growth_stage.stage_code,
            "days_since_planting": growth_stage.days_since_planting,
            "progress_percent": growth_stage.progress_percent
        },
        created_at=now
    )


async def generate_proactive_alerts(
    field_id: str,
    field_name: str,
    crop_type: str,
    variety_name: str,
    planting_date: date,
    weather_data: Optional[Dict[str, Any]] = None,
    transplant_date: Optional[date] = None,
    is_transplanted: bool = False
) -> Dict[str, Any]:
    """
    Generate all proactive alerts for a field.
    
    Args:
        field_id: UUID of the field
        field_name: Display name of the field
        crop_type: Type of crop (Maize, Tomato, etc.)
        variety_name: Name of the variety
        planting_date: Date seeds were sown
        weather_data: Current weather conditions for disease risk
        transplant_date: Date seedlings were transplanted (for vegetables)
        is_transplanted: Whether this is a transplanted crop
    
    Returns:
        Dict with growth_stage info and list of alerts
    """
    # Get variety info
    variety_info = get_variety_info(variety_name)
    
    # Calculate growth stage (uses transplant_date for transplanted crops)
    growth_stage = calculate_growth_stage(
        planting_date, 
        variety_name, 
        crop_type,
        transplant_date=transplant_date,
        is_transplanted=is_transplanted
    )
    
    alerts = []
    
    # Growth stage alert (always)
    stage_alert = generate_growth_stage_alert(growth_stage, variety_info, field_name)
    alerts.append(stage_alert)
    
    # Harvest alert
    harvest_alert = generate_harvest_alert(growth_stage, variety_info, field_name)
    if harvest_alert:
        alerts.append(harvest_alert)
    
    # Disease risk alerts (if weather data available)
    if weather_data and variety_info:
        disease_alerts = assess_disease_risk(variety_info, weather_data, growth_stage)
        alerts.extend(disease_alerts)
    
    # Add risks from growth stage as alerts
    for risk in growth_stage.risks:
        alerts.append(ProactiveAlert(
            id=f"risk-{hash(risk)}-{datetime.now().isoformat()}",
            alert_type="growth_stage",
            severity="info",
            title=f"⚡ Stage Risk: {risk.split()[0]}...",
            message=risk,
            variety_name=variety_name,
            field_name=field_name,
            action_required=False,
            recommended_actions=[],
            triggered_by={"stage": growth_stage.stage_code},
            created_at=datetime.now().isoformat()
        ))
    
    # Determine tracking mode
    TRANSPLANTED_CROPS = ['tomato', 'cabbage', 'onion', 'potato', 'pepper', 'eggplant', 'lettuce']
    use_transplant = is_transplanted or crop_type.lower() in TRANSPLANTED_CROPS
    tracking_from = "transplant_date" if (use_transplant and transplant_date) else "planting_date"
    effective_date = transplant_date if (use_transplant and transplant_date) else planting_date
    
    # Build AI context
    ai_context = {
        "field_id": field_id,
        "field_name": field_name,
        "crop_type": crop_type,
        "variety_name": variety_name,
        "variety_info": variety_info,
        "stage_name": growth_stage.stage_name,
        "days_since_planting": growth_stage.days_since_planting,
        "progress_percent": growth_stage.progress_percent,
        "weather": weather_data or {},
        "soil_condition": {} # Placeholder for future soil data integration
    }
    
    # Generate AI priorities and risks
    brain = get_brain()
    ai_results = await brain.generate_ai_priorities_and_risks(ai_context)
    
    # Merge AI risks into alerts (optional, or keep separate)
    for risk in ai_results.get('risks', []):
        alerts.append(ProactiveAlert(
            id=f"ai-risk-{datetime.now().isoformat()}",
            alert_type=risk.get('type', 'pest_risk'),
            severity="warning" if risk.get('risk', 0) > 50 else "info",
            title=f"🧠 AI Alert: {risk.get('name')}",
            message=f"{risk.get('justification', risk.get('name'))} (Risk: {risk.get('risk')}%)",
            variety_name=variety_name,
            field_name=field_name,
            action_required=risk.get('risk', 0) > 70,
            recommended_actions=[], # Detailed in ai_priorities
            triggered_by=risk,
            created_at=datetime.now().isoformat()
        ))

    return {
        "field_id": field_id,
        "field_name": field_name,
        "crop_type": crop_type,
        "is_transplanted": use_transplant,
        "tracking_from": tracking_from,
        "effective_start_date": effective_date.isoformat() if effective_date else None,
        "variety": {
            "name": variety_name,
            "breeder": variety_info.get('breeder') if variety_info else None,
            "days_to_maturity": variety_info.get('days_to_maturity') if variety_info else None
        },
        "growth_stage": {
            "name": growth_stage.stage_name,
            "code": growth_stage.stage_code,
            "days_since_planting": growth_stage.days_since_planting,
            "days_to_harvest": growth_stage.days_to_harvest,
            "progress_percent": growth_stage.progress_percent,
            "description": growth_stage.description,
            "key_activities": growth_stage.key_activities
        },
        "ai_priorities": ai_results.get('actions', []),
        "alerts": [
            {
                "id": a.id,
                "type": a.alert_type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "action_required": a.action_required,
                "recommended_actions": a.recommended_actions,
                "created_at": a.created_at
            }
            for a in alerts
        ],
        "generated_at": datetime.now().isoformat()
    }
