"""
KurimaSense Yield Projection Tool
=================================
Generates yield projections using the agronomic model + AI enhancement.

This tool combines:
1. Data-driven agronomic model (variety database, NDVI, weather)
2. AI-enhanced insights and recommendations

The agronomic model provides the numbers, the AI provides context and advice.
"""

import json
import os
import sys
from datetime import datetime, date
from dotenv import load_dotenv
from openai import OpenAI

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yield_model import (
    generate_yield_projection, 
    get_field_ndvi_history,
    YIELD_DISCLAIMER
)
from proactive_intelligence import calculate_growth_stage, get_variety_info


def _error(message):
    return {"status": "error", "error_message": message}


def _load_payload():
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    return json.loads(raw)


def run(field_data, language="en", rls_user_id=None, rls_tenant_ids=None):
    """Run yield projection. Returns the result dict directly.

    ``rls_user_id``/``rls_tenant_ids``: caller identity for the NDVI-history
    read's RLS GUCs (FORCE-ready); optional for CLI/stdin invocation."""
    load_dotenv()
    try:
        # Extract field parameters
        crop = field_data.get("crop", "Maize")
        variety = field_data.get("variety")
        planting_date_str = field_data.get("planting_date")
        fertilizer_history = field_data.get("fertilizer_history", "None")
        area_ha = float(field_data.get("area", 1.0))
        region = field_data.get("region", "Zimbabwe")
        field_id = field_data.get("field_id")
        transplant_date_str = field_data.get("transplant_date")
        is_transplanted = field_data.get("is_transplanted", False)

        # Parse dates
        planting_date = date.today()
        if planting_date_str:
            try:
                planting_date = datetime.strptime(planting_date_str, "%Y-%m-%d").date()
            except:
                pass

        transplant_date = None
        if transplant_date_str:
            try:
                transplant_date = datetime.strptime(transplant_date_str, "%Y-%m-%d").date()
            except:
                pass

        # Get NDVI history if field_id available
        ndvi_history = []
        if field_id:
            ndvi_history = get_field_ndvi_history(
                field_id, user_id=rls_user_id, tenant_ids=rls_tenant_ids)

        # === STEP 1: Use Agronomic Model for data-driven projection ===
        projection = generate_yield_projection(
            field_id=field_id or "unknown",
            crop=crop,
            variety=variety,
            planting_date=planting_date,
            area_ha=area_ha,
            fertilizer_history=fertilizer_history,
            ndvi_history=ndvi_history,
            transplant_date=transplant_date,
            is_transplanted=is_transplanted
        )

        # Get growth stage info
        growth_stage = calculate_growth_stage(
            planting_date=planting_date,
            variety_name=variety or "Generic",
            crop_type=crop,
            transplant_date=transplant_date,
            is_transplanted=is_transplanted
        )

        # Get variety info for context
        variety_info = get_variety_info(variety) if variety else None

        # === STEP 2: Use AI to generate contextual recommendations ===
        ai_insights = {
            "next_actions": growth_stage.key_activities[:3] if growth_stage.key_activities else [
                "Scout for pests and diseases",
                "Monitor soil moisture",
                "Check weather forecast"
            ],
            "pest_alert": f"Current stage risk: {growth_stage.risks[0]}" if growth_stage.risks else "No specific alerts for this stage",
            "full_plan": []
        }

        # Connect to PhD AI Agronomist Brain
        try:
            from ai_brain import get_brain
            brain = get_brain()

            context = {
                "crop_type": crop,
                "variety_name": variety,
                "stage_name": growth_stage.stage_name,
                "days_since_planting": growth_stage.days_since_planting,
                "days_to_maturity": variety_info.get("days_to_maturity") if variety_info else 140,
                "planting_date": str(planting_date),
                "fertilizer_history": fertilizer_history,
                "projected_yield": projection.projected_yield,
                "variety_info": variety_info
            }

            import asyncio
            phd_plan = asyncio.run(brain.generate_ai_crop_plan(context))

            if phd_plan:
                ai_insights["next_actions"] = phd_plan.get("next_actions", ai_insights["next_actions"])
                ai_insights["pest_alert"] = phd_plan.get("pest_alert", ai_insights["pest_alert"])
                ai_insights["full_plan"] = phd_plan.get("full_plan", [])
                print(f"✅ AI enhancement completed via PhD Brain (full_plan size: {len(ai_insights['full_plan'])})", file=sys.stderr)

        except Exception as ai_error:
            print(f"AI enhancement skipped or failed: {ai_error}", file=sys.stderr)

        # === STEP 3: Combine model + AI results ===
        result = {
            "current_stage": f"{growth_stage.stage_name} - {growth_stage.description[:100]}",
            "days_to_harvest": growth_stage.days_to_harvest,
            "days_since_planting": growth_stage.days_since_planting,
            "progress_percent": growth_stage.progress_percent,

            # Agronomic model results (data-driven)
            "projected_yield": projection.projected_yield,
            "yield_potential": projection.yield_potential,
            "confidence_bands": projection.confidence_bands,
            "confidence_score": projection.confidence_score,
            "confidence_factors": projection.confidence_factors,
            "yield_gap_analysis": projection.yield_gap_analysis,
            "methodology": projection.methodology,

            # AI-enhanced recommendations
            "next_actions": ai_insights["next_actions"],
            "pest_alert": ai_insights["pest_alert"],
            "full_plan": ai_insights["full_plan"],

            # Variety context
            "variety_info": {
                "name": variety_info.get("variety_name") if variety_info else variety,
                "breeder": variety_info.get("breeder") if variety_info else None,
                "days_to_maturity": variety_info.get("days_to_maturity") if variety_info else None
            } if variety_info or variety else None,

            # Legal disclaimer
            "disclaimer": projection.disclaimer
        }

        return {"status": "ok", "data": result}

    except Exception as exc:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return _error(str(exc))


def main():
    load_dotenv()
    payload = _load_payload()
    field_data = payload.get("field_data", {})
    language = payload.get("language", "en")
    result = run(field_data, language)
    sys.stdout.write(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
