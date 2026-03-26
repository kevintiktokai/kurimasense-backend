"""
Zimbabwe Crop Varieties Database Seeder
========================================
Populates the crop_varieties table with researched data for Zimbabwe.

Sources:
- Seed Co Zimbabwe Product Catalog
- Kutsaga Research Station (Tobacco)
- Quton Zimbabwe (Cotton)
- Starke Ayres & Sakata (Vegetables)
- ARC Grain Crops Institute

Usage:
    python backend/scripts/seed_zimbabwe_crops.py

Requires DATABASE_URL environment variable to be set.
"""

import os
import sys
import json
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory for imports if needed
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(root_dir, 'backend'))


def get_db_connection():
    """Get database connection using environment variable."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL environment variable not set.")
        print("   Set it in your .env file or export it:")
        print("   export DATABASE_URL='postgresql://...'")
        return None
    return psycopg2.connect(db_url)


ZIMBABWE_VARIETIES = [
    # ============================================================
    # MAIZE (Seed Co) - Zimbabwe's Dominant Crop
    # ============================================================
    {
        "crop_name": "Maize",
        "variety_name": "SC 301",
        "breeder": "Seed Co",
        "days_to_maturity": 100,
        "yield_potential_low": 3.0,
        "yield_potential_high": 7.0,
        "description": "Ultra-early maturing white maize. Ideal for drought-prone regions (IV and V) or late planting. Excellent drought escape mechanism.",
        "characteristics": {
            "drought_tolerance": "high",
            "heat_tolerance": "high",
            "disease_resistance": ["Maize Streak Virus", "Grey Leaf Spot"],
            "region_suitability": ["Natural Region IV", "Natural Region V"],
            "gls_tolerance": "moderate",
            "grain_type": "white dent",
            "recommended_plant_population": 44000,
            "row_spacing_cm": 90,
            "in_row_spacing_cm": 25,
            "planting_depth_cm": "5-7",
            "planting_window": "Mid-November to late December (or January for late plant)",
            "seed_rate_kg_per_ha": 25,
            "soil_requirements": "Well-drained sandy loams to clay loams, pH 5.5-7.0",
            "optimal_rainfall_mm": "450-600",
            "fertilizer_basal": "Compound D: 200-300 kg/ha at planting",
            "fertilizer_top_dress": "AN: 150-200 kg/ha at 4-6 weeks (knee height)",
            "key_pests": ["Fall Armyworm", "Stalk Borer", "Cutworm", "Maize Weevil"],
            "pest_management": "Scout weekly from emergence. Apply Emamectin benzoate or Chlorantraniliprole for Fall Armyworm when 5% of plants show fresh damage. Use Actellic for stored grain weevils.",
            "harvesting_moisture": "12.5% for safe storage",
            "post_harvest": "Shell, dry to 12.5%, treat with Actellic Super or Shumba dust, store in airtight containers or hermetic bags"
        }
    },
    {
        "crop_name": "Maize",
        "variety_name": "SC 403",
        "breeder": "Seed Co",
        "days_to_maturity": 112,
        "yield_potential_low": 4.0,
        "yield_potential_high": 8.5,
        "description": "Early maturing white maize with excellent standability. Good option for regions with shorter rainy seasons.",
        "characteristics": {
            "drought_tolerance": "high",
            "heat_tolerance": "high",
            "disease_resistance": ["Grey Leaf Spot", "Common Rust"],
            "region_suitability": ["Natural Region III", "Natural Region IV"],
            "gls_tolerance": "high",
            "grain_type": "white semi-flint",
            "recommended_plant_population": 44000,
            "row_spacing_cm": 90,
            "in_row_spacing_cm": 25,
            "planting_depth_cm": "5-7",
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": 25,
            "soil_requirements": "Sandy loams to clay loams, pH 5.5-7.0",
            "optimal_rainfall_mm": "500-650",
            "fertilizer_basal": "Compound D: 200-300 kg/ha at planting",
            "fertilizer_top_dress": "AN: 150-200 kg/ha at 4-6 weeks",
            "key_pests": ["Fall Armyworm", "Stalk Borer", "Cutworm"],
            "harvesting_moisture": "12.5%",
            "post_harvest": "Dry to 12.5%, treat with storage protectant, store in cool dry place"
        }
    },
    {
        "crop_name": "Maize",
        "variety_name": "SC 513",
        "breeder": "Seed Co",
        "days_to_maturity": 132,
        "yield_potential_low": 5.0,
        "yield_potential_high": 8.0,
        "description": "Early maturing white maize. Excellent heat and drought tolerance with attractive flinty grain.",
        "characteristics": {
            "drought_tolerance": "high",
            "heat_tolerance": "high",
            "disease_resistance": ["Rust", "Leaf Blight"],
            "region_suitability": ["Natural Region III", "Natural Region IV"],
            "gls_tolerance": "moderate",
            "grain_type": "white flint",
            "recommended_plant_population": 44000,
            "row_spacing_cm": 90,
            "in_row_spacing_cm": 25,
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": 25,
            "soil_requirements": "Well-drained soils, pH 5.5-7.0",
            "optimal_rainfall_mm": "500-650",
            "fertilizer_basal": "Compound D: 250-300 kg/ha at planting",
            "fertilizer_top_dress": "AN: 150-200 kg/ha at 4-6 weeks",
            "key_pests": ["Fall Armyworm", "Stalk Borer", "Cutworm"],
            "harvesting_moisture": "12.5%"
        }
    },
    {
        "crop_name": "Maize",
        "variety_name": "SC 637",
        "breeder": "Seed Co",
        "days_to_maturity": 142,
        "yield_potential_low": 8.0,
        "yield_potential_high": 16.0,
        "description": "Medium maturing white maize. High yielder for high-potential areas and irrigation schemes.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "heat_tolerance": "moderate",
            "disease_resistance": ["Grey Leaf Spot", "Maize Streak Virus"],
            "region_suitability": ["Natural Region I", "Natural Region II", "Irrigation"],
            "gls_tolerance": "high",
            "grain_type": "white dent",
            "recommended_plant_population": 53000,
            "row_spacing_cm": 75,
            "in_row_spacing_cm": 25,
            "planting_window": "Late October to mid-November (early planting recommended)",
            "seed_rate_kg_per_ha": 25,
            "soil_requirements": "Deep, fertile clay loams, pH 5.5-7.0. Requires good moisture retention.",
            "optimal_rainfall_mm": "700-900",
            "fertilizer_basal": "Compound D: 300-400 kg/ha at planting",
            "fertilizer_top_dress": "AN: 200-300 kg/ha split at V6 and V10 stages",
            "key_pests": ["Fall Armyworm", "Stalk Borer", "Ear Rot complex"],
            "irrigation_schedule": "50mm per week during tasselling/silking critical period",
            "harvesting_moisture": "12.5%"
        }
    },
    {
        "crop_name": "Maize",
        "variety_name": "SC 719",
        "breeder": "Seed Co",
        "days_to_maturity": 152,
        "yield_potential_low": 9.0,
        "yield_potential_high": 20.0,
        "description": "Late maturing white maize. Widely adapted and hardy with excellent standability. Popular commercial variety.",
        "characteristics": {
            "drought_tolerance": "high",
            "heat_tolerance": "moderate",
            "disease_resistance": ["Grey Leaf Spot", "Cob Rot", "Ear Rot"],
            "region_suitability": ["Natural Region II", "Irrigation"],
            "gls_tolerance": "high",
            "grain_type": "white dent",
            "recommended_plant_population": 53000,
            "row_spacing_cm": 75,
            "in_row_spacing_cm": 25,
            "planting_window": "Late October to mid-November",
            "seed_rate_kg_per_ha": 25,
            "soil_requirements": "Deep, fertile soils with good water-holding capacity, pH 5.5-7.0",
            "optimal_rainfall_mm": "750-1000",
            "fertilizer_basal": "Compound D: 300-400 kg/ha at planting",
            "fertilizer_top_dress": "AN: 200-300 kg/ha split application",
            "key_pests": ["Fall Armyworm", "Stalk Borer", "Ear Rot complex"],
            "harvesting_moisture": "12.5%",
            "post_harvest": "Dry to 12.5%, treat with storage protectant"
        }
    },
    {
        "crop_name": "Maize",
        "variety_name": "SC 727 (Nzou)",
        "breeder": "Seed Co",
        "days_to_maturity": 158,
        "yield_potential_low": 10.0,
        "yield_potential_high": 21.0,
        "description": "Late maturing white maize. The highest yielding hybrid in Africa for irrigated high-potential areas. Known as 'Nzou' (Elephant). Up to 85% shelling percentage, 18-20 rows, cobs up to 33cm.",
        "characteristics": {
            "drought_tolerance": "high",
            "heat_tolerance": "high",
            "disease_resistance": ["Grey Leaf Spot", "Leaf Blight", "Rust", "Cob Rot", "Northern Corn Leaf Spot", "Maize Streak Virus"],
            "region_suitability": ["Natural Region I", "Natural Region II", "Irrigation"],
            "gls_tolerance": "very high",
            "grain_type": "white dent",
            "recommended_plant_population": 55000,
            "row_spacing_cm": 75,
            "in_row_spacing_cm": 24,
            "planting_window": "Mid-October to early November (needs full season)",
            "seed_rate_kg_per_ha": 25,
            "soil_requirements": "Deep, fertile clay loams with high organic matter, pH 5.5-7.0",
            "optimal_rainfall_mm": "800-1200",
            "fertilizer_basal": "Compound D: 400 kg/ha at planting",
            "fertilizer_top_dress": "AN: 300 kg/ha split at V6 and V10-V12",
            "key_pests": ["Fall Armyworm", "Stalk Borer", "Ear Rot complex"],
            "irrigation_schedule": "60mm per week during tasselling/silking. Total crop water requirement ~600-700mm.",
            "shelling_percentage": "up to 85%",
            "cob_length_cm": "up to 33",
            "plant_height_m": 2.8,
            "cob_placement_m": 1.6,
            "dry_down_rate": "1.8% per week",
            "harvesting_moisture": "12.5%",
            "post_harvest": "Dry to 12.5%, fumigate with Phostoxin for large-scale storage or use hermetic bags for smallholder"
        }
    },

    # --- MAIZE (Pioneer) ---
    {
        "crop_name": "Maize",
        "variety_name": "P2859W",
        "breeder": "Pioneer",
        "days_to_maturity": 128,
        "yield_potential_low": 6.0,
        "yield_potential_high": 9.0,
        "description": "Early maturing white maize. Hard flint grain with excellent poundability for sadza.",
        "characteristics": {
            "drought_tolerance": "high",
            "heat_tolerance": "moderate",
            "disease_resistance": ["Maize Streak Virus"],
            "region_suitability": ["Natural Region III", "Natural Region IV"],
            "grain_type": "white flint",
            "recommended_plant_population": 44000,
            "row_spacing_cm": 90,
            "in_row_spacing_cm": 25,
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": 25,
            "soil_requirements": "Sandy loams to clay loams, pH 5.5-7.0",
            "optimal_rainfall_mm": "500-700",
            "fertilizer_basal": "Compound D: 200-300 kg/ha",
            "fertilizer_top_dress": "AN: 150-200 kg/ha at knee height",
            "key_pests": ["Fall Armyworm", "Stalk Borer", "Cutworm"],
            "harvesting_moisture": "12.5%"
        }
    },
    {
        "crop_name": "Maize",
        "variety_name": "PHB 30G19",
        "breeder": "Pioneer",
        "days_to_maturity": 140,
        "yield_potential_low": 7.0,
        "yield_potential_high": 12.0,
        "description": "Medium maturing hybrid with excellent GLS tolerance. Popular in commercial farming.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "disease_resistance": ["Grey Leaf Spot", "Northern Corn Leaf Blight"],
            "region_suitability": ["Natural Region II", "Natural Region III"],
            "gls_tolerance": "very high",
            "recommended_plant_population": 50000,
            "row_spacing_cm": 75,
            "in_row_spacing_cm": 27,
            "planting_window": "Late October to mid-November",
            "seed_rate_kg_per_ha": 25,
            "soil_requirements": "Medium to high potential soils, pH 5.5-7.0",
            "optimal_rainfall_mm": "650-900",
            "fertilizer_basal": "Compound D: 300-400 kg/ha",
            "fertilizer_top_dress": "AN: 200-250 kg/ha split application",
            "key_pests": ["Fall Armyworm", "Stalk Borer"],
            "harvesting_moisture": "12.5%"
        }
    },

    # ============================================================
    # TOBACCO (Kutsaga Research Station)
    # ============================================================
    {
        "crop_name": "Tobacco",
        "variety_name": "KRK26R",
        "breeder": "Kutsaga",
        "days_to_maturity": 90,
        "yield_potential_low": 2.5,
        "yield_potential_high": 4.5,
        "description": "Popular flue-cured variety. Ripens very fast, produces soft, clean lemon-grade leaves. Suitable for all regions.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "disease_resistance": ["Root-knot Nematode", "Alternaria"],
            "style": "Lemon",
            "growth_habit": "Fast ripening",
            "leaf_size": "Medium-large",
            "curing_time": "5-7 days",
            "seedbed_sowing": "August to September",
            "transplanting_window": "October to November (6-8 weeks after sowing)",
            "row_spacing_cm": 120,
            "in_row_spacing_cm": 50,
            "plant_population_per_ha": 16600,
            "soil_requirements": "Sandy loams with good drainage, pH 5.0-5.8. Avoid heavy clays.",
            "fertilizer_basal": "Compound S: 600-800 kg/ha at ridging",
            "fertilizer_top_dress": "AN: 200-300 kg/ha split at 3 and 6 weeks after transplanting",
            "key_pests": ["Budworm", "Aphids", "Red Spider Mite", "Cutworm", "Nematodes"],
            "key_diseases": ["Root-knot Nematode", "Alternaria", "Angular Leaf Spot", "Bacterial Wilt"],
            "pest_management": "Seedbed: drench with Mocap/Nemacur for nematodes. Field: scout for budworm from topping, spray Chlorpyrifos or Emamectin. Remove suckers promptly.",
            "curing_method": "Flue-curing in barn. Yellow (35-40C, 24-36hrs) -> Leaf drying (45-55C, 24-36hrs) -> Midrib drying (60-70C, 24-48hrs)",
            "grading": "Harvest leaf-by-leaf as they ripen from bottom. Grade by colour (lemon, orange, mahogany), body, and position."
        }
    },
    {
        "crop_name": "Tobacco",
        "variety_name": "KRK75",
        "breeder": "Kutsaga",
        "days_to_maturity": 115,
        "yield_potential_low": 3.0,
        "yield_potential_high": 5.0,
        "description": "Climate-smart variety. Dense root system makes it highly drought tolerant. Orange-mahogany style, premium prices.",
        "characteristics": {
            "drought_tolerance": "very high",
            "disease_resistance": ["Root-knot Nematode", "White Mold", "Frogeye"],
            "style": "Orange/Mahogany",
            "growth_habit": "Slow ripening",
            "leaf_size": "Large",
            "recommended_for": "Dry land farming",
            "seedbed_sowing": "August to September",
            "transplanting_window": "October to November",
            "row_spacing_cm": 120,
            "in_row_spacing_cm": 55,
            "plant_population_per_ha": 15150,
            "soil_requirements": "Sandy loams, pH 5.0-5.8",
            "fertilizer_basal": "Compound S: 600-800 kg/ha",
            "fertilizer_top_dress": "AN: 200-300 kg/ha split",
            "key_pests": ["Budworm", "Aphids", "Red Spider Mite", "Cutworm"],
            "curing_method": "Flue-curing; slow ripening means longer yellowing phase",
            "grading": "Orange/Mahogany grades command premium prices on auction floors"
        }
    },
    {
        "crop_name": "Tobacco",
        "variety_name": "T78",
        "breeder": "Kutsaga",
        "days_to_maturity": 100,
        "yield_potential_low": 3.0,
        "yield_potential_high": 4.8,
        "description": "Climate-smart variety for marginal areas. Broad leaves, medium-lemon style. Good disease package.",
        "characteristics": {
            "drought_tolerance": "high",
            "disease_resistance": ["Angular Leaf Spot", "Mosaic Virus", "Wildfire"],
            "style": "Medium Lemon",
            "growth_habit": "Fast ripening",
            "leaf_size": "Broad",
            "seedbed_sowing": "August to September",
            "transplanting_window": "October to November",
            "row_spacing_cm": 120,
            "in_row_spacing_cm": 50,
            "soil_requirements": "Sandy loams, pH 5.0-5.8",
            "fertilizer_basal": "Compound S: 600-800 kg/ha",
            "fertilizer_top_dress": "AN: 200-300 kg/ha split",
            "key_pests": ["Budworm", "Aphids", "Red Spider Mite"],
            "curing_method": "Flue-curing"
        }
    },
    {
        "crop_name": "Tobacco",
        "variety_name": "KM10",
        "breeder": "Kutsaga",
        "days_to_maturity": 95,
        "yield_potential_low": 2.8,
        "yield_potential_high": 4.2,
        "description": "Early maturing variety with excellent nematode resistance. Ideal for replant or rotation scenarios.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "disease_resistance": ["Root-knot Nematode (High)", "Bacterial Wilt"],
            "style": "Lemon",
            "growth_habit": "Fast",
            "seedbed_sowing": "August to September",
            "transplanting_window": "October to November",
            "row_spacing_cm": 120,
            "in_row_spacing_cm": 50,
            "soil_requirements": "Sandy loams, pH 5.0-5.8. Excellent for nematode-infested fields.",
            "fertilizer_basal": "Compound S: 600-800 kg/ha",
            "fertilizer_top_dress": "AN: 200-300 kg/ha split",
            "key_pests": ["Budworm", "Aphids"],
            "curing_method": "Flue-curing"
        }
    },

    # ============================================================
    # SOYBEANS (Seed Co)
    # ============================================================
    {
        "crop_name": "Soybeans",
        "variety_name": "SC Sentinel",
        "breeder": "Seed Co",
        "days_to_maturity": 125,
        "yield_potential_low": 3.0,
        "yield_potential_high": 5.0,
        "description": "Indeterminate, late-maturing variety. High vegetative growth, excellent for high potential areas and irrigation.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "disease_resistance": ["Rust", "Frog Eye Leaf Spot"],
            "growth_habit": "Indeterminate",
            "pod_shattering": "low",
            "seed_size": "medium",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "5-7",
            "planting_depth_cm": "3-5",
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": "80-100",
            "soil_requirements": "Well-drained loams to clay loams, pH 5.5-6.5. MUST lime acidic soils (pH<5.2) for nodulation.",
            "optimal_rainfall_mm": "600-800",
            "inoculation": "CRITICAL: Inoculate seed with Bradyrhizobium japonicum at planting. Use peat-based or liquid inoculant. Keep out of direct sunlight.",
            "fertilizer_basal": "Compound L: 200-300 kg/ha (low N, high P). Do NOT apply nitrogen fertilizer as it inhibits nodulation.",
            "key_pests": ["Soybean Rust", "Aphids", "Pod Borer", "Red Spider Mite"],
            "key_diseases": ["Soybean Rust (Phakopsora pachyrhizi)", "Frog Eye Leaf Spot", "Red Leaf Blotch", "Sclerotinia"],
            "pest_management": "Scout for rust from flowering. Spray Tebuconazole/Azoxystrobin preventatively at R1-R3 stage. Rotate with non-legume crops.",
            "harvesting": "Combine at 13% moisture. Avoid harvest losses by cutting low (pods set low on stem).",
            "post_harvest": "Dry to 12%, store in clean, dry conditions. Avoid cracking seed."
        }
    },
    {
        "crop_name": "Soybeans",
        "variety_name": "SC Safari",
        "breeder": "Seed Co",
        "days_to_maturity": 115,
        "yield_potential_low": 2.5,
        "yield_potential_high": 4.0,
        "description": "Determinate, medium-late variety. Good standability and resistance to lodging.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "disease_resistance": ["Red Leaf Blotch"],
            "growth_habit": "Determinate",
            "pod_shattering": "moderate",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "5-7",
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": "80-100",
            "soil_requirements": "Well-drained soils, pH 5.5-6.5. Lime if below pH 5.2.",
            "inoculation": "CRITICAL: Inoculate with Bradyrhizobium japonicum",
            "fertilizer_basal": "Compound L: 200-300 kg/ha (low N)",
            "key_pests": ["Soybean Rust", "Aphids", "Pod Borer"],
            "harvesting": "Combine at 13% moisture"
        }
    },
    {
        "crop_name": "Soybeans",
        "variety_name": "SC Squire",
        "breeder": "Seed Co",
        "days_to_maturity": 105,
        "yield_potential_low": 2.0,
        "yield_potential_high": 3.5,
        "description": "Determinate, early-maturing variety. Ideal for late planting or rotation with winter wheat.",
        "characteristics": {
            "drought_tolerance": "high",
            "disease_resistance": ["Rust"],
            "growth_habit": "Determinate",
            "pod_height": "Good",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "5-7",
            "planting_window": "November to January (good for late planting)",
            "seed_rate_kg_per_ha": "80-100",
            "soil_requirements": "Well-drained soils, pH 5.5-6.5",
            "inoculation": "CRITICAL: Inoculate with Bradyrhizobium japonicum",
            "fertilizer_basal": "Compound L: 200-300 kg/ha",
            "key_pests": ["Soybean Rust", "Aphids"],
            "harvesting": "Combine at 13% moisture"
        }
    },
    {
        "crop_name": "Soybeans",
        "variety_name": "Spike",
        "breeder": "Pannar",
        "days_to_maturity": 120,
        "yield_potential_low": 2.8,
        "yield_potential_high": 4.5,
        "description": "High yielding variety with excellent oil content. Popular with crushing plants.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "oil_content": "high",
            "growth_habit": "Semi-determinate",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "5-7",
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": "80-100",
            "soil_requirements": "Fertile, well-drained soils, pH 5.5-6.5",
            "inoculation": "CRITICAL: Inoculate with Bradyrhizobium japonicum",
            "fertilizer_basal": "Compound L: 200-300 kg/ha",
            "key_pests": ["Soybean Rust", "Aphids", "Pod Borer"],
            "harvesting": "Combine at 13% moisture"
        }
    },

    # ============================================================
    # SORGHUM (Seed Co & ICRISAT)
    # ============================================================
    {
        "crop_name": "Sorghum",
        "variety_name": "SC Sila",
        "breeder": "Seed Co",
        "days_to_maturity": 115,
        "yield_potential_low": 4.0,
        "yield_potential_high": 8.0,
        "description": "White sorghum variety, ideal for opaque beer brewing and mealie-meal. The market leader.",
        "characteristics": {
            "drought_tolerance": "very high",
            "bird_resistance": "low",
            "use": ["Brewing", "Food", "Stockfeed"],
            "grain_color": "white",
            "tannin_content": "low",
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "10-15",
            "planting_depth_cm": "3-5",
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": "5-8",
            "soil_requirements": "Tolerates poor, sandy soils. pH 5.5-7.5. Very tolerant of low fertility.",
            "optimal_rainfall_mm": "400-600",
            "fertilizer_basal": "Compound D: 150-200 kg/ha at planting",
            "fertilizer_top_dress": "AN: 100-150 kg/ha at 4-6 weeks",
            "key_pests": ["Quelea birds", "Stalk Borer", "Shoot Fly", "Grain Midge"],
            "key_diseases": ["Grain Mold", "Anthracnose", "Leaf Blight"],
            "pest_management": "Bird scaring is essential for white/low-tannin types from grain filling. Coordinate with neighbours for quelea control.",
            "harvesting": "Cut heads when grain is hard (moisture <14%). Thresh and winnow.",
            "post_harvest": "Dry to 12%, store in airtight containers. Sorghum stores well if dry."
        }
    },
    {
        "crop_name": "Sorghum",
        "variety_name": "SC Smile",
        "breeder": "Seed Co",
        "days_to_maturity": 110,
        "yield_potential_low": 3.0,
        "yield_potential_high": 7.0,
        "description": "Red sorghum variety, highly sought after for traditional brewing (chibuku). High tannin provides bird resistance.",
        "characteristics": {
            "drought_tolerance": "very high",
            "bird_resistance": "high",
            "use": ["Brewing", "Traditional beer"],
            "grain_color": "red",
            "tannin_content": "high",
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "10-15",
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": "5-8",
            "soil_requirements": "Tolerates poor, sandy soils. pH 5.5-7.5",
            "optimal_rainfall_mm": "350-550",
            "fertilizer_basal": "Compound D: 150-200 kg/ha",
            "fertilizer_top_dress": "AN: 100-150 kg/ha at 4-6 weeks",
            "key_pests": ["Stalk Borer", "Shoot Fly", "Grain Midge"],
            "harvesting": "Cut heads when grain is hard, thresh and winnow",
            "post_harvest": "Dry to 12%, store in airtight containers"
        }
    },
    {
        "crop_name": "Sorghum",
        "variety_name": "Macia",
        "breeder": "ICRISAT",
        "days_to_maturity": 100,
        "yield_potential_low": 3.5,
        "yield_potential_high": 6.0,
        "description": "Open-pollinated variety with excellent food quality. Low tannin, good for sadza. Popular in communal areas. Seed can be retained.",
        "characteristics": {
            "drought_tolerance": "very high",
            "bird_resistance": "low",
            "use": ["Food", "Sadza"],
            "grain_color": "white",
            "tannin_content": "very low",
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "10-15",
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": "5-8",
            "soil_requirements": "Very adaptable. Sandy to clay soils, pH 5.5-7.5",
            "optimal_rainfall_mm": "350-500",
            "fertilizer_basal": "Compound D: 100-200 kg/ha",
            "fertilizer_top_dress": "AN: 100 kg/ha at 4-6 weeks",
            "key_pests": ["Quelea birds (MAJOR - white grain)", "Stalk Borer", "Shoot Fly"],
            "pest_management": "Bird scaring essential. Consider planting near homestead for easier bird scaring.",
            "seed_retention": "OPV - farmers can retain seed for 3-4 seasons before genetic degradation"
        }
    },

    # ============================================================
    # WHEAT (Seed Co - Winter Crop, Irrigated)
    # ============================================================
    {
        "crop_name": "Wheat",
        "variety_name": "SC Nduna",
        "breeder": "Seed Co",
        "days_to_maturity": 125,
        "yield_potential_low": 6.0,
        "yield_potential_high": 10.0,
        "description": "Premium white wheat variety with excellent baking quality. Medium maturity. Main commercial variety.",
        "characteristics": {
            "disease_resistance": ["Leaf Rust", "Stem Rust", "Yellow Rust"],
            "growth_habit": "Determinate",
            "season": "Winter (May-September)",
            "protein_content": "12-14%",
            "baking_quality": "excellent",
            "row_spacing_cm": "17-20",
            "planting_depth_cm": "3-5",
            "planting_window": "May to mid-June (winter crop, requires irrigation)",
            "seed_rate_kg_per_ha": "100-120",
            "soil_requirements": "Fertile clay loams to heavy clays, pH 6.0-7.0. Requires residual moisture or irrigation.",
            "irrigation": "ESSENTIAL. Total requirement 450-550mm. Apply 40-50mm every 7-10 days. Critical periods: tillering and grain filling.",
            "fertilizer_basal": "Compound D: 400 kg/ha or MAP: 200 kg/ha at planting",
            "fertilizer_top_dress": "AN: 200 kg/ha at tillering (3-4 weeks) + 100 kg/ha at flag leaf",
            "key_pests": ["Aphids (Russian Wheat Aphid)", "Armyworm"],
            "key_diseases": ["Leaf Rust", "Stem Rust", "Yellow Rust", "Powdery Mildew", "Septoria"],
            "pest_management": "Scout for aphids from tillering. Spray Dimethoate or Imidacloprid if threshold exceeded. Fungicide (Propiconazole) at flag leaf for rust prevention.",
            "harvesting": "Combine at 12-13% moisture. Avoid rain damage at maturity.",
            "post_harvest": "Dry to 12%, store in clean silos. Grade for milling quality."
        }
    },
    {
        "crop_name": "Wheat",
        "variety_name": "SC Select",
        "breeder": "Seed Co",
        "days_to_maturity": 115,
        "yield_potential_low": 5.5,
        "yield_potential_high": 9.0,
        "description": "Early maturing wheat variety. Good for late planting to avoid early rains at harvest.",
        "characteristics": {
            "disease_resistance": ["Powdery Mildew", "Leaf Rust"],
            "season": "Winter",
            "protein_content": "11-13%",
            "row_spacing_cm": "17-20",
            "planting_window": "May to late June",
            "seed_rate_kg_per_ha": "100-120",
            "soil_requirements": "Fertile soils, pH 6.0-7.0",
            "irrigation": "ESSENTIAL. 400-500mm total.",
            "fertilizer_basal": "Compound D: 400 kg/ha at planting",
            "fertilizer_top_dress": "AN: 200 kg/ha at tillering",
            "key_pests": ["Aphids", "Armyworm"],
            "key_diseases": ["Powdery Mildew", "Leaf Rust"],
            "harvesting": "Combine at 12-13% moisture"
        }
    },
    {
        "crop_name": "Wheat",
        "variety_name": "Pan 3120",
        "breeder": "Pannar",
        "days_to_maturity": 120,
        "yield_potential_low": 6.0,
        "yield_potential_high": 9.5,
        "description": "Medium maturity variety with good rust resistance package. Widely adapted.",
        "characteristics": {
            "disease_resistance": ["Leaf Rust", "Stem Rust"],
            "season": "Winter",
            "standability": "excellent",
            "row_spacing_cm": "17-20",
            "planting_window": "May to mid-June",
            "seed_rate_kg_per_ha": "100-120",
            "soil_requirements": "Fertile soils, pH 6.0-7.0",
            "irrigation": "ESSENTIAL. 450-550mm total.",
            "fertilizer_basal": "Compound D: 400 kg/ha at planting",
            "fertilizer_top_dress": "AN: 200-250 kg/ha at tillering",
            "key_pests": ["Aphids", "Armyworm"],
            "harvesting": "Combine at 12-13% moisture"
        }
    },

    # ============================================================
    # COTTON (Quton Zimbabwe)
    # ============================================================
    {
        "crop_name": "Cotton",
        "variety_name": "QM 593",
        "breeder": "Quton",
        "days_to_maturity": 160,
        "yield_potential_low": 1.5,
        "yield_potential_high": 3.5,
        "description": "High yield potential cotton variety with good fibre quality. Widely adapted across cotton-growing regions.",
        "characteristics": {
            "drought_tolerance": "high",
            "disease_resistance": ["Verticillium Wilt", "Jassids", "Bollworms"],
            "fibre_quality": "Excellent",
            "ginning_outturn": "40-42%",
            "staple_length": "28-30mm",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "30-40",
            "planting_depth_cm": "3-5",
            "planting_window": "Mid-October to end November (needs warm soil >18C)",
            "seed_rate_kg_per_ha": "15-20",
            "soil_requirements": "Deep, well-drained loams to clay loams, pH 5.5-7.0. Avoid waterlogged soils.",
            "optimal_rainfall_mm": "600-800",
            "fertilizer_basal": "Compound L: 200-300 kg/ha at planting",
            "fertilizer_top_dress": "AN: 100-150 kg/ha at first square (6-8 weeks)",
            "key_pests": ["American Bollworm (Helicoverpa)", "Red Bollworm", "Jassids", "Aphids", "Stainers", "Whitefly"],
            "key_diseases": ["Verticillium Wilt", "Fusarium Wilt", "Bacterial Blight", "Alternaria Leaf Spot"],
            "pest_management": "Scout twice weekly from squaring. Spray Cypermethrin/Lambda-cyhalothrin for bollworm at threshold (3 larvae per 10 plants). Rotate insecticide classes to avoid resistance.",
            "harvesting": "Pick when bolls fully open. Pick clean, avoid contaminants (polypropylene bags, hair, stones). Sort grades in field.",
            "post_harvest": "Store in clean cotton/hessian bags only. Never use polypropylene bags - contaminants are penalised."
        }
    },
    {
        "crop_name": "Cotton",
        "variety_name": "SZ 9314",
        "breeder": "Quton",
        "days_to_maturity": 150,
        "yield_potential_low": 1.2,
        "yield_potential_high": 3.0,
        "description": "Widely adapted cotton variety, performs well in middleveld and lowveld. Good for smallholder farmers.",
        "characteristics": {
            "drought_tolerance": "very high",
            "disease_resistance": ["Bacterial Blight", "Fusarium Wilt"],
            "ginning_outturn": "38-40%",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "30-40",
            "planting_window": "Mid-October to end November",
            "seed_rate_kg_per_ha": "15-20",
            "soil_requirements": "Adaptable. Sandy loams to clays, pH 5.5-7.0",
            "optimal_rainfall_mm": "500-700",
            "fertilizer_basal": "Compound L: 200-300 kg/ha",
            "fertilizer_top_dress": "AN: 100 kg/ha at squaring",
            "key_pests": ["American Bollworm", "Red Bollworm", "Jassids", "Aphids"],
            "harvesting": "Pick clean when bolls fully open",
            "post_harvest": "Store in cotton/hessian bags only"
        }
    },
    {
        "crop_name": "Cotton",
        "variety_name": "QM 302",
        "breeder": "Quton",
        "days_to_maturity": 145,
        "yield_potential_low": 1.3,
        "yield_potential_high": 2.8,
        "description": "Early maturing variety suitable for short season areas. Compact plant structure.",
        "characteristics": {
            "drought_tolerance": "high",
            "disease_resistance": ["Bacterial Blight"],
            "plant_type": "Compact",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "25-35",
            "planting_window": "October to December (good for late planting)",
            "seed_rate_kg_per_ha": "15-20",
            "soil_requirements": "Well-drained soils, pH 5.5-7.0",
            "optimal_rainfall_mm": "450-650",
            "fertilizer_basal": "Compound L: 200-300 kg/ha",
            "fertilizer_top_dress": "AN: 100 kg/ha at squaring",
            "key_pests": ["American Bollworm", "Jassids", "Aphids"],
            "harvesting": "Pick clean when bolls fully open"
        }
    },

    # ============================================================
    # GROUNDNUTS / PEANUTS
    # ============================================================
    {
        "crop_name": "Groundnuts",
        "variety_name": "Natal Common",
        "breeder": "Generic",
        "days_to_maturity": 110,
        "yield_potential_low": 1.5,
        "yield_potential_high": 2.5,
        "description": "Spanish type, erect bunch. Small kernels. Drought tolerant and widely adapted.",
        "characteristics": {
            "drought_tolerance": "high",
            "pod_type": "bunch",
            "kernel_size": "small",
            "oil_content": "48-50%",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "10-15",
            "planting_depth_cm": "5-7",
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": "60-80 (unshelled) or 40-50 (shelled)",
            "soil_requirements": "Light, well-drained sandy soils, pH 5.5-6.5. Calcium critical for pod filling - apply gypsum at flowering.",
            "optimal_rainfall_mm": "500-700",
            "fertilizer_basal": "Compound D: 150-200 kg/ha. Do NOT apply nitrogen - groundnuts fix their own N.",
            "gypsum_application": "200-300 kg/ha gypsum at flowering for calcium supply to pegging zone",
            "key_pests": ["Aphids (transmit Rosette Virus)", "Termites", "Leaf Miner", "Groundnut Bruchid (storage)"],
            "key_diseases": ["Rosette Virus", "Early Leaf Spot", "Late Leaf Spot", "Rust", "Aflatoxin (Aspergillus)"],
            "pest_management": "Control aphids early to prevent Rosette virus. Use certified seed. Rotate with cereals. Remove volunteers.",
            "harvesting": "Lift when 75% of pods have dark inner shell. Invert and dry on windrows for 3-5 days.",
            "post_harvest": "CRITICAL: Dry to <8% moisture to prevent Aflatoxin. Sort and remove damaged/discoloured kernels. Store in cool, dry place.",
            "aflatoxin_prevention": "Harvest on time. Dry rapidly. Sort out damaged pods. Avoid soil contact during drying. Store at <8% moisture."
        }
    },
    {
        "crop_name": "Groundnuts",
        "variety_name": "Makulu Red",
        "breeder": "Generic",
        "days_to_maturity": 130,
        "yield_potential_low": 2.0,
        "yield_potential_high": 4.0,
        "description": "Red skinned, large kernel (Valencia type). Requires good rainfall. Popular for confectionery market.",
        "characteristics": {
            "drought_tolerance": "low",
            "pod_type": "bunch",
            "kernel_size": "large",
            "market": "Confectionery",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "10-15",
            "planting_window": "November to early December (needs full season)",
            "seed_rate_kg_per_ha": "80-100 (unshelled)",
            "soil_requirements": "Light, well-drained sandy soils, pH 5.5-6.5. Apply gypsum at flowering.",
            "optimal_rainfall_mm": "600-800",
            "fertilizer_basal": "Compound D: 150-200 kg/ha",
            "gypsum_application": "250-300 kg/ha at flowering",
            "key_pests": ["Aphids", "Termites", "Leaf Miner"],
            "key_diseases": ["Rosette Virus", "Early Leaf Spot", "Late Leaf Spot", "Aflatoxin"],
            "harvesting": "Lift when 75% of pods have dark inner shell",
            "aflatoxin_prevention": "Dry rapidly to <8% moisture, sort damaged pods"
        }
    },
    {
        "crop_name": "Groundnuts",
        "variety_name": "Nyanda",
        "breeder": "ARC",
        "days_to_maturity": 120,
        "yield_potential_low": 1.8,
        "yield_potential_high": 3.5,
        "description": "High yielding variety with good disease resistance. Suitable for both oil and confectionery.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "disease_resistance": ["Rosette Virus", "Early Leaf Spot"],
            "kernel_size": "medium-large",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "10-15",
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": "70-90 (unshelled)",
            "soil_requirements": "Light, well-drained sandy soils, pH 5.5-6.5",
            "fertilizer_basal": "Compound D: 150-200 kg/ha",
            "gypsum_application": "200-300 kg/ha at flowering",
            "key_pests": ["Aphids", "Termites"],
            "harvesting": "Lift when 75% of pods have dark inner shell",
            "aflatoxin_prevention": "Dry rapidly, sort damaged pods, store at <8% moisture"
        }
    },

    # ============================================================
    # SUNFLOWER
    # ============================================================
    {
        "crop_name": "Sunflower",
        "variety_name": "PAN 7057",
        "breeder": "Pannar",
        "days_to_maturity": 95,
        "yield_potential_low": 1.5,
        "yield_potential_high": 3.0,
        "description": "Early maturing sunflower hybrid. Good for short season areas or late planting.",
        "characteristics": {
            "drought_tolerance": "high",
            "disease_resistance": ["Rust", "Downy Mildew"],
            "oil_content": "42-45%",
            "plant_height": "medium",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "20-25",
            "planting_depth_cm": "3-5",
            "planting_window": "November to January (flexible - good for late planting)",
            "seed_rate_kg_per_ha": "5-7",
            "plant_population_per_ha": "40000-50000",
            "soil_requirements": "Wide range of soils, pH 5.5-7.5. Deep soils preferred for tap root.",
            "optimal_rainfall_mm": "400-600",
            "fertilizer_basal": "Compound D: 200-250 kg/ha",
            "fertilizer_top_dress": "AN: 100 kg/ha at 4-6 weeks if growth is poor",
            "key_pests": ["Birds (at seed fill)", "Bollworm", "Cutworm"],
            "key_diseases": ["Rust", "Downy Mildew", "Sclerotinia Head Rot"],
            "harvesting": "Harvest when back of head is brown and seeds are hard. Moisture 10-12%.",
            "post_harvest": "Dry to 9%, store in clean, aerated bins. Sunflower seed deteriorates if stored at high moisture."
        }
    },
    {
        "crop_name": "Sunflower",
        "variety_name": "Agsun 8251",
        "breeder": "AgriSeeds",
        "days_to_maturity": 105,
        "yield_potential_low": 2.0,
        "yield_potential_high": 3.5,
        "description": "Medium maturing hybrid with high oil content. Excellent standability.",
        "characteristics": {
            "drought_tolerance": "high",
            "disease_resistance": ["Sclerotinia"],
            "oil_content": "44-47%",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "20-25",
            "planting_window": "November to December",
            "seed_rate_kg_per_ha": "5-7",
            "soil_requirements": "Wide range, pH 5.5-7.5",
            "fertilizer_basal": "Compound D: 200-250 kg/ha",
            "key_pests": ["Birds", "Bollworm"],
            "harvesting": "Harvest when back of head brown, seeds hard at 10-12% moisture"
        }
    },
    {
        "crop_name": "Sunflower",
        "variety_name": "NK Adagio CL",
        "breeder": "Syngenta",
        "days_to_maturity": 100,
        "yield_potential_low": 1.8,
        "yield_potential_high": 3.2,
        "description": "Clearfield hybrid resistant to Clearfield herbicides. Good for weed management.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "herbicide_tolerance": "Clearfield (Imazamox)",
            "oil_content": "43-46%",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "20-25",
            "planting_window": "November to December",
            "seed_rate_kg_per_ha": "5-7",
            "soil_requirements": "Wide range, pH 5.5-7.5",
            "fertilizer_basal": "Compound D: 200-250 kg/ha",
            "weed_management": "Apply Imazamox (Clearfield herbicide) post-emergence for broadleaf and grass weed control",
            "key_pests": ["Birds", "Bollworm"],
            "harvesting": "Harvest at 10-12% moisture"
        }
    },

    # ============================================================
    # SUGAR BEANS
    # ============================================================
    {
        "crop_name": "Sugar Beans",
        "variety_name": "Gloria",
        "breeder": "Pannar",
        "days_to_maturity": 90,
        "yield_potential_low": 1.5,
        "yield_potential_high": 3.0,
        "description": "Large red speckled bean. Market leader for table beans. Good cooking quality.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "disease_resistance": ["Anthracnose", "Common Bean Mosaic"],
            "seed_size": "large",
            "cooking_time": "short",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "7-10",
            "planting_depth_cm": "3-5",
            "planting_window": "January to mid-February (late summer crop) or November with irrigation",
            "seed_rate_kg_per_ha": "80-100",
            "soil_requirements": "Well-drained loams, pH 5.5-6.5. Sensitive to waterlogging and salinity.",
            "optimal_rainfall_mm": "400-500",
            "fertilizer_basal": "Compound D: 200-300 kg/ha. Beans fix N but benefit from starter N.",
            "inoculation": "Inoculate with Rhizobium phaseoli for improved N fixation",
            "key_pests": ["Bean Fly (most destructive)", "Aphids", "Pod Borer", "Bruchids (storage)"],
            "key_diseases": ["Anthracnose", "Angular Leaf Spot", "Rust", "Common Bean Mosaic Virus", "Halo Blight"],
            "pest_management": "Dress seed with Imidacloprid for Bean Fly protection. Critical in first 3 weeks. Spray Dimethoate if heavy infestation.",
            "harvesting": "Pull plants when 90% of pods are dry. Stack and dry for 5-7 days. Thresh.",
            "post_harvest": "Dry to 12%, treat with Actellic for bruchid protection, store in airtight containers."
        }
    },
    {
        "crop_name": "Sugar Beans",
        "variety_name": "Doraline",
        "breeder": "Seed Co",
        "days_to_maturity": 85,
        "yield_potential_low": 1.2,
        "yield_potential_high": 2.5,
        "description": "Red speckled bean with determinate growth. Early maturing and compact.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "growth_habit": "Determinate bush",
            "seed_size": "medium",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "7-10",
            "planting_window": "January to mid-February, or November with irrigation",
            "seed_rate_kg_per_ha": "80-100",
            "soil_requirements": "Well-drained loams, pH 5.5-6.5",
            "fertilizer_basal": "Compound D: 200-300 kg/ha",
            "key_pests": ["Bean Fly", "Aphids", "Pod Borer"],
            "key_diseases": ["Anthracnose", "Angular Leaf Spot", "Rust"],
            "harvesting": "Pull when 90% pods dry"
        }
    },
    {
        "crop_name": "Sugar Beans",
        "variety_name": "PAN 148",
        "breeder": "Pannar",
        "days_to_maturity": 95,
        "yield_potential_low": 1.8,
        "yield_potential_high": 3.2,
        "description": "High yielding red bean variety with excellent disease resistance package.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "disease_resistance": ["Rust", "Anthracnose", "Angular Leaf Spot"],
            "growth_habit": "Determinate",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "7-10",
            "planting_window": "January to mid-February",
            "seed_rate_kg_per_ha": "80-100",
            "soil_requirements": "Well-drained loams, pH 5.5-6.5",
            "fertilizer_basal": "Compound D: 200-300 kg/ha",
            "key_pests": ["Bean Fly", "Aphids"],
            "harvesting": "Pull when 90% pods dry"
        }
    },

    # ============================================================
    # POTATOES
    # ============================================================
    {
        "crop_name": "Potato",
        "variety_name": "BP1",
        "breeder": "Generic",
        "days_to_maturity": 95,
        "yield_potential_low": 30.0,
        "yield_potential_high": 60.0,
        "description": "The standard table potato in Zimbabwe. Good cooking quality (waxier texture). Pink skin.",
        "characteristics": {
            "tuber_shape": "Oval",
            "disease_resistance": ["Late Blight (Moderate)"],
            "skin_color": "pink",
            "flesh_color": "cream",
            "use": ["Boiling", "Roasting"],
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "25-30",
            "planting_depth_cm": "10-15",
            "planting_window": "August-September (spring) or January-February (summer). Two seasons possible under irrigation.",
            "seed_rate_kg_per_ha": "2000-2500 (certified seed tubers)",
            "soil_requirements": "Deep, well-drained sandy loams, pH 5.0-6.0. Acid tolerant. Avoid fresh manure (causes scab).",
            "optimal_rainfall_mm": "500-700 (or equivalent irrigation)",
            "fertilizer_basal": "2:3:4 at 1000-1500 kg/ha or Compound S: 800-1000 kg/ha at planting",
            "fertilizer_top_dress": "LAN/AN: 200-300 kg/ha at earthing up",
            "earthing_up": "Earth up 2-3 times to cover tubers and prevent greening. First at 15-20cm height.",
            "key_pests": ["Potato Tuber Moth", "Aphids", "Red Spider Mite", "Cutworm", "Nematodes"],
            "key_diseases": ["Late Blight (Phytophthora - MAJOR)", "Early Blight", "Bacterial Wilt", "Scab", "Virus Y"],
            "pest_management": "LATE BLIGHT: Spray preventatively with Mancozeb/Ridomil every 7-10 days from 30cm height, especially in wet weather. Do not plant near tomatoes.",
            "harvesting": "Dehaulm 2 weeks before harvest to set skin. Dig carefully to avoid damage.",
            "post_harvest": "Cure in shade for 10-14 days (15-20C). Store in cool (4-8C), dark, ventilated store. Remove rotten tubers promptly."
        }
    },
    {
        "crop_name": "Potato",
        "variety_name": "Mnandi",
        "breeder": "ARC",
        "days_to_maturity": 90,
        "yield_potential_low": 35.0,
        "yield_potential_high": 65.0,
        "description": "High yielding variety with good eating quality. Slightly shorter cycle than BP1.",
        "characteristics": {
            "tuber_shape": "Round-Oval",
            "disease_resistance": ["Scab (Moderate)", "Virus Y"],
            "skin_color": "yellow",
            "flesh_color": "light yellow",
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "25-30",
            "planting_window": "August-September (spring) or January-February (summer)",
            "seed_rate_kg_per_ha": "2000-2500",
            "soil_requirements": "Deep, well-drained sandy loams, pH 5.0-6.0",
            "fertilizer_basal": "2:3:4 at 1000-1500 kg/ha",
            "earthing_up": "Earth up 2-3 times",
            "key_pests": ["Potato Tuber Moth", "Aphids", "Cutworm"],
            "key_diseases": ["Late Blight", "Early Blight", "Scab"],
            "pest_management": "Spray Mancozeb/Ridomil preventatively for Late Blight"
        }
    },
    {
        "crop_name": "Potato",
        "variety_name": "Hermes",
        "breeder": "Generic",
        "days_to_maturity": 100,
        "yield_potential_low": 25.0,
        "yield_potential_high": 50.0,
        "description": "Specialized variety for crisps/processing. High dry matter content.",
        "characteristics": {
            "use": "Crisping/Processing",
            "disease_resistance": ["Virus Y"],
            "dry_matter": "high",
            "skin_color": "white",
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "25-30",
            "planting_window": "August-September or January-February",
            "seed_rate_kg_per_ha": "2000-2500",
            "soil_requirements": "Deep sandy loams, pH 5.0-6.0",
            "fertilizer_basal": "2:3:4 at 1000-1200 kg/ha (lower N for processing - reduces sugar content)",
            "key_diseases": ["Late Blight", "Early Blight"]
        }
    },
    {
        "crop_name": "Potato",
        "variety_name": "Mondial",
        "breeder": "HZPC",
        "days_to_maturity": 110,
        "yield_potential_low": 40.0,
        "yield_potential_high": 70.0,
        "description": "High yielding variety with oval tubers. Popular for chips (French fries).",
        "characteristics": {
            "use": ["Chips/Fries", "Table"],
            "tuber_shape": "Long oval",
            "skin_color": "yellow",
            "flesh_color": "light yellow",
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "30-35",
            "planting_window": "August-September or January-February",
            "seed_rate_kg_per_ha": "2000-2500",
            "soil_requirements": "Deep sandy loams, pH 5.0-6.0",
            "fertilizer_basal": "2:3:4 at 1200-1500 kg/ha",
            "irrigation": "Critical at tuber initiation and bulking. 25-30mm every 3-4 days.",
            "key_diseases": ["Late Blight", "Early Blight"]
        }
    },

    # ============================================================
    # TOMATOES
    # ============================================================
    {
        "crop_name": "Tomato",
        "variety_name": "Rodade",
        "breeder": "Open Pollinated",
        "days_to_maturity": 85,
        "yield_potential_low": 40.0,
        "yield_potential_high": 80.0,
        "description": "Popular open-pollinated variety. Determinant growth, good reliability and fruit set.",
        "characteristics": {
            "growth_habit": "Determinate",
            "disease_resistance": ["Fusarium Wilt", "Verticillium Wilt"],
            "fruit_size": "medium",
            "fruit_firmness": "good",
            "nursery_sowing": "Sow in seedbed/trays 4-6 weeks before transplanting",
            "transplanting_window": "Year-round under irrigation. Main season: August-October (dry season for best quality)",
            "row_spacing_cm": 120,
            "in_row_spacing_cm": "40-50",
            "soil_requirements": "Well-drained, fertile loams, pH 5.5-6.8. Rich in organic matter.",
            "fertilizer_basal": "2:3:4 at 800-1000 kg/ha or Compound S: 600 kg/ha at planting",
            "fertilizer_top_dress": "LAN: 150 kg/ha every 3-4 weeks from flowering. Calcium Nitrate to prevent Blossom End Rot.",
            "key_pests": ["Tuta absoluta (Tomato Leaf Miner - DEVASTATING)", "Bollworm", "Whitefly", "Red Spider Mite", "Nematodes"],
            "key_diseases": ["Late Blight", "Early Blight", "Bacterial Wilt", "Fusarium Wilt", "Tomato Yellow Leaf Curl Virus"],
            "pest_management": "TUTA ABSOLUTA: Use pheromone traps for monitoring. Spray Chlorantraniliprole/Emamectin benzoate. Combine with netting in high-value production. Rotate chemicals.",
            "staking": "Stake or cage plants for better air circulation, easier harvesting, and reduced disease",
            "harvesting": "Pick at breaker stage (pink) for distant markets, or red-ripe for local sales. Handle gently.",
            "post_harvest": "Grade by size and ripeness. Use wooden/plastic crates, not sacks. Keep in shade. Shelf life 5-7 days at ambient temperature."
        }
    },
    {
        "crop_name": "Tomato",
        "variety_name": "Star 9009",
        "breeder": "Starke Ayres",
        "days_to_maturity": 80,
        "yield_potential_low": 80.0,
        "yield_potential_high": 120.0,
        "description": "Standard determinant hybrid tomato. Excellent fruit quality and shelf life.",
        "characteristics": {
            "growth_habit": "Determinate",
            "disease_resistance": ["ToMV", "Verticillium", "Fusarium 1&2", "Nematodes"],
            "fruit_size": "100-120g",
            "shelf_life": "excellent",
            "nursery_sowing": "Sow 4-6 weeks before transplanting",
            "transplanting_window": "Year-round under irrigation",
            "row_spacing_cm": 120,
            "in_row_spacing_cm": "40-50",
            "soil_requirements": "Well-drained fertile loams, pH 5.5-6.8",
            "fertilizer_basal": "2:3:4 at 800-1000 kg/ha",
            "fertilizer_top_dress": "LAN: 150 kg/ha every 3-4 weeks from flowering",
            "key_pests": ["Tuta absoluta", "Bollworm", "Whitefly", "Red Spider Mite"],
            "key_diseases": ["Late Blight", "Early Blight", "Bacterial Wilt"],
            "harvesting": "Pick at breaker or red-ripe stage",
            "post_harvest": "Grade, pack in crates, keep in shade"
        }
    },
    {
        "crop_name": "Tomato",
        "variety_name": "Tengeru 97",
        "breeder": "Open Pollinated",
        "days_to_maturity": 90,
        "yield_potential_low": 30.0,
        "yield_potential_high": 60.0,
        "description": "Indeterminate variety popular with small scale farmers. Long harvest period, needs staking.",
        "characteristics": {
            "growth_habit": "Indeterminate",
            "disease_resistance": ["Nematodes (Moderate)"],
            "fruit_size": "medium",
            "harvest_window": "extended",
            "nursery_sowing": "Sow 4-6 weeks before transplanting",
            "transplanting_window": "Year-round under irrigation",
            "row_spacing_cm": 120,
            "in_row_spacing_cm": "50-60",
            "staking": "ESSENTIAL - indeterminate type. Use 1.5m stakes or string trellis.",
            "pruning": "Remove suckers to maintain 2-3 main stems",
            "soil_requirements": "Well-drained fertile loams, pH 5.5-6.8",
            "fertilizer_basal": "2:3:4 at 800 kg/ha",
            "key_pests": ["Tuta absoluta", "Bollworm", "Whitefly"],
            "harvesting": "Extended harvest over 8-12 weeks"
        }
    },
    {
        "crop_name": "Tomato",
        "variety_name": "Heinz 1370",
        "breeder": "Heinz",
        "days_to_maturity": 95,
        "yield_potential_low": 60.0,
        "yield_potential_high": 100.0,
        "description": "Processing tomato variety. High solids content for paste and sauce production.",
        "characteristics": {
            "growth_habit": "Determinate",
            "use": "Processing",
            "brix": "high",
            "fruit_firmness": "excellent",
            "nursery_sowing": "Sow 4-6 weeks before transplanting",
            "transplanting_window": "March-May (dry season for processing)",
            "row_spacing_cm": 150,
            "in_row_spacing_cm": "30-40",
            "soil_requirements": "Fertile loams, pH 5.5-6.8",
            "fertilizer_basal": "2:3:4 at 800-1000 kg/ha",
            "harvesting": "Machine or hand harvest when fully red. Single destructive harvest.",
            "post_harvest": "Deliver to processing plant within 24 hours of harvest"
        }
    },

    # ============================================================
    # ONIONS
    # ============================================================
    {
        "crop_name": "Onion",
        "variety_name": "Texas Grano",
        "breeder": "Open Pollinated",
        "days_to_maturity": 160,
        "yield_potential_low": 30.0,
        "yield_potential_high": 50.0,
        "description": "Short day onion, mild pungency. The standard white onion for Zimbabwe.",
        "characteristics": {
            "day_length": "Short Day",
            "storage": "Medium (2-3 months)",
            "pungency": "mild",
            "bulb_color": "white",
            "nursery_sowing": "March-April (for June-July transplanting)",
            "transplanting_window": "June to July (winter transplanting for November harvest)",
            "row_spacing_cm": 30,
            "in_row_spacing_cm": "8-10",
            "planting_depth_cm": "2-3 (seedlings set at same depth as nursery)",
            "soil_requirements": "Fertile, well-drained loams to clay loams, pH 6.0-7.0. High organic matter.",
            "irrigation": "Regular, shallow irrigation. Critical during bulb expansion. Stop watering 2 weeks before harvest for curing.",
            "fertilizer_basal": "2:3:4 at 600-800 kg/ha at transplanting",
            "fertilizer_top_dress": "LAN: 100-150 kg/ha at 4 and 8 weeks after transplanting. Stop N after bulbing begins.",
            "key_pests": ["Thrips (MAJOR)", "Onion Fly", "Cutworm"],
            "key_diseases": ["Purple Blotch", "Downy Mildew", "Stemphylium Leaf Blight", "Basal Rot"],
            "pest_management": "Thrips: Spray Abamectin or Spinosad weekly during dry hot weather. Rotate insecticides.",
            "harvesting": "Harvest when 50-75% of tops have fallen over naturally. Pull and windrow to cure for 7-10 days.",
            "post_harvest": "Cure in shade with good ventilation for 2-3 weeks. Remove tops. Grade by size. Store in slatted crates in cool, dry, ventilated area."
        }
    },
    {
        "crop_name": "Onion",
        "variety_name": "Red Creole",
        "breeder": "Open Pollinated",
        "days_to_maturity": 170,
        "yield_potential_low": 25.0,
        "yield_potential_high": 45.0,
        "description": "Red onion with distinct pungency. Excellent storage qualities. Popular in informal markets.",
        "characteristics": {
            "day_length": "Short Day",
            "storage": "Good (4-5 months)",
            "pungency": "strong",
            "bulb_color": "red",
            "nursery_sowing": "March-April",
            "transplanting_window": "June to July",
            "row_spacing_cm": 30,
            "in_row_spacing_cm": "8-10",
            "soil_requirements": "Fertile, well-drained soils, pH 6.0-7.0",
            "fertilizer_basal": "2:3:4 at 600-800 kg/ha",
            "key_pests": ["Thrips", "Onion Fly"],
            "key_diseases": ["Purple Blotch", "Downy Mildew"],
            "harvesting": "Harvest when tops fall over. Cure 7-10 days.",
            "post_harvest": "Excellent storage - 4-5 months in cool, dry conditions"
        }
    },
    {
        "crop_name": "Onion",
        "variety_name": "Star 9077",
        "breeder": "Starke Ayres",
        "days_to_maturity": 150,
        "yield_potential_low": 40.0,
        "yield_potential_high": 60.0,
        "description": "High yielding hybrid onion. Uniform bulb size with good pink blush.",
        "characteristics": {
            "day_length": "Short Day",
            "storage": "Medium",
            "bulb_color": "white with pink",
            "uniformity": "excellent",
            "nursery_sowing": "March-April",
            "transplanting_window": "June to July",
            "row_spacing_cm": 30,
            "in_row_spacing_cm": "8-10",
            "soil_requirements": "Fertile, well-drained soils, pH 6.0-7.0",
            "fertilizer_basal": "2:3:4 at 600-800 kg/ha",
            "key_pests": ["Thrips", "Onion Fly"],
            "harvesting": "Harvest when tops fall over"
        }
    },

    # ============================================================
    # CABBAGE
    # ============================================================
    {
        "crop_name": "Cabbage",
        "variety_name": "Star 3311",
        "breeder": "Starke Ayres",
        "days_to_maturity": 85,
        "yield_potential_low": 60.0,
        "yield_potential_high": 100.0,
        "description": "The market leader. Large heads (4-6kg), uniform, excellent holding ability in the field.",
        "characteristics": {
            "heat_tolerance": "good",
            "disease_resistance": ["Black Rot"],
            "head_weight": "4-6 kg",
            "head_shape": "round",
            "color": "blue-green",
            "nursery_sowing": "Sow in seedbed/trays 4-5 weeks before transplanting",
            "transplanting_window": "Year-round. Best: February-May (cool season) for quality heads.",
            "row_spacing_cm": 60,
            "in_row_spacing_cm": "40-50",
            "soil_requirements": "Fertile, well-drained soils with high organic matter, pH 6.0-7.0",
            "irrigation": "Regular. 25-30mm per week. Consistent moisture prevents head splitting.",
            "fertilizer_basal": "2:3:4 at 800-1000 kg/ha at transplanting",
            "fertilizer_top_dress": "LAN: 150 kg/ha at 3 and 6 weeks after transplanting",
            "key_pests": ["Diamondback Moth (DBM - MAJOR)", "Aphids", "Cutworm", "Bagrada Bug"],
            "key_diseases": ["Black Rot", "Clubroot", "Downy Mildew", "Ring Spot"],
            "pest_management": "DBM: Most damaging pest. Spray Bt (Bacillus thuringiensis) or Spinosad. Rotate insecticide classes - DBM develops resistance quickly. Use trap crops (Indian mustard).",
            "harvesting": "Cut when heads are firm and compact. Leave 2-3 wrapper leaves for protection.",
            "post_harvest": "Keep in shade. Can store 2-4 weeks at 0-4C with 95% humidity. Grade by size and quality."
        }
    },
    {
        "crop_name": "Cabbage",
        "variety_name": "Fabulosa",
        "breeder": "Sakata",
        "days_to_maturity": 80,
        "yield_potential_low": 70.0,
        "yield_potential_high": 110.0,
        "description": "High yielding hybrid with excellent field holding and Black Rot resistance.",
        "characteristics": {
            "disease_resistance": ["Black Rot (High)", "Fusarium Yellows"],
            "head_weight": "3-5 kg",
            "head_shape": "round-flat",
            "nursery_sowing": "4-5 weeks before transplanting",
            "transplanting_window": "Year-round, best February-May",
            "row_spacing_cm": 60,
            "in_row_spacing_cm": "40-50",
            "soil_requirements": "Fertile, well-drained, pH 6.0-7.0",
            "fertilizer_basal": "2:3:4 at 800-1000 kg/ha",
            "key_pests": ["Diamondback Moth", "Aphids", "Cutworm"],
            "harvesting": "Cut when firm, leave wrapper leaves"
        }
    },
    {
        "crop_name": "Cabbage",
        "variety_name": "Grand Slam",
        "breeder": "Sakata",
        "days_to_maturity": 95,
        "yield_potential_low": 80.0,
        "yield_potential_high": 120.0,
        "description": "Late maturing variety with extra-large heads. Popular for institutional markets.",
        "characteristics": {
            "heat_tolerance": "moderate",
            "disease_resistance": ["Black Rot", "Tipburn resistant"],
            "head_weight": "5-8 kg",
            "nursery_sowing": "4-5 weeks before transplanting",
            "transplanting_window": "Year-round, best February-May",
            "row_spacing_cm": 60,
            "in_row_spacing_cm": "50-60",
            "soil_requirements": "Fertile, well-drained, pH 6.0-7.0",
            "fertilizer_basal": "2:3:4 at 1000-1200 kg/ha",
            "key_pests": ["Diamondback Moth", "Aphids"],
            "harvesting": "Cut when firm, leave wrapper leaves"
        }
    },

    # ============================================================
    # SWEET POTATOES - Major Food Security Crop
    # ============================================================
    {
        "crop_name": "Sweet Potato",
        "variety_name": "Brondal",
        "breeder": "DR&SS Zimbabwe",
        "days_to_maturity": 120,
        "yield_potential_low": 15.0,
        "yield_potential_high": 30.0,
        "description": "White-fleshed sweet potato, the most widely grown variety in Zimbabwe. Excellent drought tolerance. Preferred for its starchy, dry texture (good for roasting/boiling). High dry matter content.",
        "characteristics": {
            "flesh_color": "white",
            "skin_color": "cream/pale",
            "drought_tolerance": "very high",
            "texture": "dry, starchy",
            "dry_matter_content": "high (30-35%)",
            "beta_carotene": "low (white-fleshed)",
            "region_suitability": ["Natural Region II", "Natural Region III", "Natural Region IV", "Natural Region V"],
            "planting_method": "Vine cuttings (30-40cm tip cuttings from healthy mother plants)",
            "planting_window": "October to December (with first rains). Can plant January in wetter areas.",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "25-30",
            "planting_depth_cm": "Two-thirds of cutting buried, 2-3 nodes below soil",
            "ridging": "Plant on ridges 30-40cm high for good tuber development and drainage",
            "vine_multiplication": "Establish rapid multiplication plots 2 months before main planting. 1 hectare needs ~33,000 cuttings.",
            "soil_requirements": "Light, well-drained sandy loams, pH 5.5-6.5. Tolerates poor fertility. Avoid waterlogged soils.",
            "optimal_rainfall_mm": "500-750",
            "fertilizer_basal": "Compound D: 200-300 kg/ha. AVOID excess nitrogen - causes excessive vine growth at expense of tubers.",
            "fertilizer_note": "Sweet potato is efficient at extracting nutrients. Responds well to organic matter/compost rather than heavy mineral fertilizer.",
            "key_pests": ["Sweet Potato Weevil (Cylas spp. - MOST DESTRUCTIVE)", "Whitefly", "Aphids", "Millipedes", "Mole Rats"],
            "key_diseases": ["Sweet Potato Virus Disease (SPVD)", "Alternaria Blight", "Scab", "Black Rot (Ceratocystis)"],
            "pest_management": "SWEET POTATO WEEVIL: The #1 threat. Plant early. Earth up regularly to cover exposed tubers. Harvest on time - do not leave tubers in ground. Use clean planting material. Rotate fields. Destroy old crop residues.",
            "disease_management": "SPVD: Use virus-free planting material. Remove and destroy diseased plants. Do not take cuttings from infected plants. Source clean vines from research stations.",
            "weeding": "Weed 2-3 times. First weeding at 3-4 weeks, second at 6-8 weeks. After canopy closure, crop suppresses weeds.",
            "earthing_up": "Earth up at 6-8 weeks to cover tubers and prevent weevil damage and greening",
            "harvesting": "Harvest at 4-5 months when leaves start yellowing. Test dig to check tuber size. Do not delay - weevil damage increases.",
            "post_harvest": "Handle carefully - sweet potato skin is fragile. Cure at 25-30C and 85-90% humidity for 5-7 days to heal wounds. Store in cool (13-15C), well-ventilated place. Shelf life 2-4 weeks at ambient, 2-3 months if cured and stored properly.",
            "nutritional_value": "Good source of carbohydrates, dietary fibre, potassium, and vitamin C. White-fleshed types lower in Vitamin A.",
            "intercropping": "Can be intercropped with maize, beans, or cowpeas. Good rotation crop after cereals."
        }
    },
    {
        "crop_name": "Sweet Potato",
        "variety_name": "Beauregard",
        "breeder": "Louisiana State University/Introduced",
        "days_to_maturity": 110,
        "yield_potential_low": 20.0,
        "yield_potential_high": 40.0,
        "description": "Orange-fleshed sweet potato (OFSP). Very high beta-carotene content - addresses Vitamin A deficiency. Sweet, moist texture. Increasingly promoted by NGOs and government for nutrition programmes.",
        "characteristics": {
            "flesh_color": "deep orange",
            "skin_color": "copper/red",
            "drought_tolerance": "moderate",
            "texture": "moist, sweet",
            "dry_matter_content": "moderate (20-25%)",
            "beta_carotene": "very high (>100 mg/kg fresh weight)",
            "vitamin_a_content": "Provides >100% daily Vitamin A requirement per 125g serving",
            "region_suitability": ["Natural Region I", "Natural Region II", "Natural Region III"],
            "planting_method": "Vine cuttings (30-40cm)",
            "planting_window": "October to December",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "25-30",
            "ridging": "Plant on ridges 30-40cm high",
            "vine_multiplication": "Establish rapid multiplication plots 2 months before planting",
            "soil_requirements": "Well-drained sandy loams, pH 5.5-6.5. Responds to moderate fertility.",
            "optimal_rainfall_mm": "600-900",
            "fertilizer_basal": "Compound D: 200-300 kg/ha. Moderate N only.",
            "key_pests": ["Sweet Potato Weevil (Cylas spp.)", "Whitefly", "Aphids"],
            "key_diseases": ["SPVD", "Alternaria Blight", "Black Rot"],
            "pest_management": "Earth up regularly. Harvest on time. Use clean planting material.",
            "harvesting": "Harvest at 3.5-4 months. Does not store as long as white types due to higher moisture.",
            "post_harvest": "Cure and store carefully. Shorter shelf life than white types (1-2 weeks ambient). Process into chips/flour for longer storage.",
            "nutritional_value": "EXCELLENT source of Vitamin A (beta-carotene), Vitamin C, dietary fibre. Critical for combating Vitamin A deficiency in children.",
            "processing": "Can be dried into chips, milled into flour for fortified porridge, used in baking (bread, buns, cakes), or pureed for baby food."
        }
    },
    {
        "crop_name": "Sweet Potato",
        "variety_name": "Chingovha",
        "breeder": "DR&SS Zimbabwe",
        "days_to_maturity": 130,
        "yield_potential_low": 12.0,
        "yield_potential_high": 25.0,
        "description": "Traditional white-fleshed variety popular in communal areas. Very hardy and drought tolerant. Known for excellent roasting quality and long in-ground storage ability.",
        "characteristics": {
            "flesh_color": "white",
            "skin_color": "reddish-brown",
            "drought_tolerance": "very high",
            "texture": "dry, starchy, mealy",
            "dry_matter_content": "very high (33-38%)",
            "beta_carotene": "low",
            "region_suitability": ["Natural Region III", "Natural Region IV", "Natural Region V"],
            "planting_method": "Vine cuttings (30-40cm)",
            "planting_window": "November to January",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "30",
            "ridging": "Plant on ridges",
            "soil_requirements": "Tolerates very poor soils. Sandy soils preferred.",
            "optimal_rainfall_mm": "400-600",
            "fertilizer_basal": "Compound D: 100-200 kg/ha or manure/compost",
            "key_pests": ["Sweet Potato Weevil", "Mole Rats"],
            "key_diseases": ["SPVD", "Alternaria"],
            "pest_management": "Earth up regularly. Can be left in ground longer than other varieties (piecemeal harvesting).",
            "harvesting": "Piecemeal harvesting possible - dig tubers as needed over 2-3 months. Provides extended food security.",
            "in_ground_storage": "Excellent - tubers can remain in ground for several weeks after maturity without significant quality loss",
            "nutritional_value": "Good source of carbohydrates. Fills the 'hungry season' gap between main harvests."
        }
    },
    {
        "crop_name": "Sweet Potato",
        "variety_name": "Irene",
        "breeder": "CIP/Introduced",
        "days_to_maturity": 105,
        "yield_potential_low": 18.0,
        "yield_potential_high": 35.0,
        "description": "Orange-fleshed sweet potato developed by CIP (International Potato Center). High yielding with good virus tolerance. Promoted for nutrition security.",
        "characteristics": {
            "flesh_color": "orange",
            "skin_color": "light brown",
            "drought_tolerance": "moderate",
            "texture": "moist, moderately sweet",
            "dry_matter_content": "moderate (22-28%)",
            "beta_carotene": "high (60-80 mg/kg fresh weight)",
            "region_suitability": ["Natural Region I", "Natural Region II", "Natural Region III"],
            "planting_method": "Vine cuttings (30-40cm)",
            "planting_window": "October to December",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "25-30",
            "ridging": "Plant on ridges",
            "soil_requirements": "Well-drained sandy loams, pH 5.5-6.5",
            "optimal_rainfall_mm": "550-800",
            "fertilizer_basal": "Compound D: 200-300 kg/ha",
            "key_pests": ["Sweet Potato Weevil", "Whitefly"],
            "key_diseases": ["SPVD (tolerant)", "Alternaria"],
            "harvesting": "Harvest at 3.5-4 months",
            "nutritional_value": "High Vitamin A, good for nutrition programmes"
        }
    },

    # ============================================================
    # FINGER MILLET (Rapoko/Rukweza) - Traditional Small Grain
    # ============================================================
    {
        "crop_name": "Finger Millet",
        "variety_name": "ICIAP-SM 1",
        "breeder": "ICRISAT",
        "days_to_maturity": 100,
        "yield_potential_low": 1.0,
        "yield_potential_high": 2.5,
        "description": "Improved finger millet variety with good blast resistance. Higher yielding than local landraces. Important traditional cereal for porridge (bota), beer, and food security.",
        "characteristics": {
            "drought_tolerance": "very high",
            "heat_tolerance": "high",
            "region_suitability": ["Natural Region III", "Natural Region IV", "Natural Region V"],
            "row_spacing_cm": 30,
            "in_row_spacing_cm": "10-15 (thin to this after emergence)",
            "planting_depth_cm": "1-2 (surface sow and press/roll)",
            "planting_window": "November to mid-December (with first rains)",
            "seed_rate_kg_per_ha": "5-8 (very small seed - mix with sand for even distribution)",
            "soil_requirements": "Wide range, including poor sandy soils. pH 5.0-7.0. Tolerates low fertility.",
            "optimal_rainfall_mm": "350-600",
            "fertilizer_basal": "Compound D: 100-150 kg/ha (or manure: 5-10 t/ha)",
            "fertilizer_top_dress": "AN: 50-100 kg/ha at tillering (3-4 weeks)",
            "key_pests": ["Quelea birds (MAJOR at grain filling)", "Shoot Fly", "Stalk Borer"],
            "key_diseases": ["Blast (Magnaporthe)", "Smut", "Helminthosporium Leaf Blight"],
            "pest_management": "Bird scaring essential from heading to maturity. Plant near homestead.",
            "use": ["Porridge (bota)", "Traditional beer (kachasu/hwahwa)", "Flour/mealie-meal", "Malting"],
            "weeding": "2-3 weedings critical. First at 2-3 weeks, second at 5-6 weeks.",
            "harvesting": "Cut heads when grain is hard and fingers close. Dry heads for 1-2 weeks. Thresh by beating.",
            "post_harvest": "Very good storage (2-5 years if dry). Resistant to storage pests due to small grain size. Thresh, winnow, dry to 12%.",
            "nutritional_value": "Excellent source of calcium (3x more than other cereals), iron, methionine. Gluten-free. Diabetic-friendly (slow-release carbs).",
            "cultural_significance": "Rapoko/rukweza is deeply embedded in Shona culture. Used for traditional ceremonies, ancestral offerings, and social gatherings."
        }
    },
    {
        "crop_name": "Finger Millet",
        "variety_name": "FMV 1 (Local Improved)",
        "breeder": "DR&SS Zimbabwe",
        "days_to_maturity": 110,
        "yield_potential_low": 0.8,
        "yield_potential_high": 2.0,
        "description": "Locally improved finger millet selection. Adapted to Zimbabwe's communal farming systems. Good tillering ability.",
        "characteristics": {
            "drought_tolerance": "very high",
            "heat_tolerance": "high",
            "region_suitability": ["Natural Region III", "Natural Region IV", "Natural Region V"],
            "row_spacing_cm": 30,
            "in_row_spacing_cm": "10-15",
            "planting_window": "November to mid-December",
            "seed_rate_kg_per_ha": "5-8",
            "soil_requirements": "Tolerates very poor soils. Sandy to clay loams.",
            "optimal_rainfall_mm": "350-500",
            "fertilizer_basal": "Compound D: 100-150 kg/ha or manure",
            "key_pests": ["Quelea birds", "Shoot Fly"],
            "key_diseases": ["Blast", "Smut"],
            "use": ["Porridge", "Traditional beer", "Flour"],
            "seed_retention": "OPV - farmers can retain seed",
            "post_harvest": "Stores very well for 2-5 years"
        }
    },

    # ============================================================
    # PEARL MILLET (Mhunga) - Drought Tolerant Small Grain
    # ============================================================
    {
        "crop_name": "Pearl Millet",
        "variety_name": "Okashana 1",
        "breeder": "ICRISAT/SADC",
        "days_to_maturity": 85,
        "yield_potential_low": 1.5,
        "yield_potential_high": 3.0,
        "description": "Early maturing pearl millet variety. Excellent drought escape. The most heat and drought tolerant of all cereals. Ideal for Natural Regions IV and V where maize consistently fails.",
        "characteristics": {
            "drought_tolerance": "extremely high",
            "heat_tolerance": "very high",
            "region_suitability": ["Natural Region IV", "Natural Region V"],
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "15-20",
            "planting_depth_cm": "2-3",
            "planting_window": "November to December (with first effective rains)",
            "seed_rate_kg_per_ha": "3-5",
            "soil_requirements": "Tolerates very poor, sandy, infertile soils. pH 5.0-8.0. Most drought-tolerant cereal.",
            "optimal_rainfall_mm": "250-500",
            "fertilizer_basal": "Compound D: 100-200 kg/ha (or manure: 5-10 t/ha)",
            "fertilizer_top_dress": "AN: 50-100 kg/ha at 3-4 weeks if rains are good",
            "key_pests": ["Quelea birds (MAJOR)", "Stalk Borer", "Head Miner", "Downy Mildew"],
            "key_diseases": ["Downy Mildew", "Smut", "Ergot", "Rust"],
            "pest_management": "Bird scaring essential from heading. Coordinate with community.",
            "use": ["Sadza/porridge (mahewu)", "Traditional beer", "Flour", "Livestock feed"],
            "weeding": "2 weedings critical. Millet is poor competitor in early stages.",
            "harvesting": "Cut heads when grain is hard. Dry for 1-2 weeks. Thresh.",
            "post_harvest": "Good storage if properly dried (<12%). More susceptible to storage pests than finger millet - treat with Actellic.",
            "nutritional_value": "Rich in iron, zinc, protein, and B vitamins. Higher energy content than maize. Gluten-free.",
            "climate_resilience": "Can recover from drought stress better than any other cereal. Produces grain even in seasons when maize fails completely."
        }
    },
    {
        "crop_name": "Pearl Millet",
        "variety_name": "PMV 2",
        "breeder": "DR&SS Zimbabwe",
        "days_to_maturity": 90,
        "yield_potential_low": 1.0,
        "yield_potential_high": 2.5,
        "description": "Locally adapted pearl millet variety. Good tillering ability. OPV - farmers can retain seed.",
        "characteristics": {
            "drought_tolerance": "extremely high",
            "heat_tolerance": "very high",
            "region_suitability": ["Natural Region IV", "Natural Region V"],
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "15-20",
            "planting_window": "November to December",
            "seed_rate_kg_per_ha": "3-5",
            "soil_requirements": "Very adaptable. Sandy soils, pH 5.0-8.0",
            "optimal_rainfall_mm": "250-450",
            "fertilizer_basal": "Compound D: 100-150 kg/ha or manure",
            "key_pests": ["Quelea birds", "Stalk Borer"],
            "key_diseases": ["Downy Mildew", "Smut"],
            "use": ["Sadza", "Porridge", "Traditional beer"],
            "seed_retention": "OPV - farmers can retain seed"
        }
    },

    # ============================================================
    # COWPEAS (Nyemba) - Important Legume for Food Security
    # ============================================================
    {
        "crop_name": "Cowpeas",
        "variety_name": "CBC 1",
        "breeder": "DR&SS Zimbabwe",
        "days_to_maturity": 75,
        "yield_potential_low": 1.0,
        "yield_potential_high": 2.0,
        "description": "Early maturing cowpea variety. Cream coloured grain. Important protein source and nitrogen-fixing crop. Both grain and leaves are eaten.",
        "characteristics": {
            "drought_tolerance": "very high",
            "heat_tolerance": "high",
            "grain_color": "cream",
            "region_suitability": ["Natural Region III", "Natural Region IV", "Natural Region V"],
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "15-20",
            "planting_depth_cm": "3-5",
            "planting_window": "December to January (plant after main crop established for relay/intercrop, or as sole crop)",
            "seed_rate_kg_per_ha": "20-30",
            "soil_requirements": "Wide range. Sandy to clay soils, pH 5.5-7.0. Tolerates poor soils. Fixes nitrogen.",
            "optimal_rainfall_mm": "300-500",
            "fertilizer_basal": "Compound D: 100-150 kg/ha. Low N due to N-fixation capability.",
            "inoculation": "Inoculate with Bradyrhizobium for improved N-fixation on new fields",
            "key_pests": ["Pod Borer (Maruca)", "Aphids", "Bruchids (storage - MAJOR)", "Flower Thrips", "Blister Beetle"],
            "key_diseases": ["Cowpea Mosaic Virus", "Anthracnose", "Septoria Leaf Spot", "Bacterial Blight"],
            "pest_management": "Aphids: spray Dimethoate at seedling stage. Storage bruchids: treat dried grain with Actellic or use triple-bagging (PICS bags).",
            "use": ["Grain (protein source)", "Leaves (vegetable - munyemba)", "Livestock fodder", "Green manure/cover crop"],
            "intercropping": "Excellent intercrop with maize, sorghum, or millet. Fix nitrogen for subsequent cereal crop.",
            "leaf_harvesting": "Young leaves harvested as vegetable (munyemba) from 4-6 weeks. Pick tender tips.",
            "harvesting": "Harvest pods when dry and brown. Multiple pickings as pods mature unevenly.",
            "post_harvest": "Dry pods, thresh, winnow. CRITICAL: Treat with Actellic for bruchids or use hermetic storage (PICS bags).",
            "nutritional_value": "High protein (23-25%), iron, zinc, folate. Leaves are excellent source of Vitamin A, iron, and protein.",
            "rotation_value": "Fixes 40-80 kg N/ha. Excellent preceding crop for cereals."
        }
    },
    {
        "crop_name": "Cowpeas",
        "variety_name": "CBC 2 (Nyemba)",
        "breeder": "DR&SS Zimbabwe",
        "days_to_maturity": 85,
        "yield_potential_low": 0.8,
        "yield_potential_high": 1.8,
        "description": "Local cowpea variety with spreading growth habit. Good for intercropping. Both grain and leaves used for food.",
        "characteristics": {
            "drought_tolerance": "very high",
            "heat_tolerance": "high",
            "grain_color": "brown/mixed",
            "growth_habit": "Spreading/trailing",
            "region_suitability": ["Natural Region III", "Natural Region IV", "Natural Region V"],
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "20-25",
            "planting_window": "December to January",
            "seed_rate_kg_per_ha": "15-25",
            "soil_requirements": "Very adaptable. Tolerates poor soils.",
            "optimal_rainfall_mm": "300-500",
            "fertilizer_basal": "Minimal - Compound D: 100 kg/ha or manure",
            "key_pests": ["Pod Borer", "Aphids", "Bruchids (storage)"],
            "use": ["Grain", "Leaves (vegetable)", "Fodder", "Soil improvement"],
            "intercropping": "Traditionally intercropped with maize, sorghum, or millet",
            "post_harvest": "Treat for bruchids. Use PICS bags for storage."
        }
    },
    {
        "crop_name": "Cowpeas",
        "variety_name": "IT 18",
        "breeder": "IITA",
        "days_to_maturity": 65,
        "yield_potential_low": 1.2,
        "yield_potential_high": 2.5,
        "description": "Extra-early maturing cowpea from IITA. White grain preferred by market. Erect growth habit, good for sole cropping.",
        "characteristics": {
            "drought_tolerance": "high",
            "heat_tolerance": "high",
            "grain_color": "white",
            "growth_habit": "Erect/semi-erect",
            "region_suitability": ["Natural Region III", "Natural Region IV"],
            "row_spacing_cm": 60,
            "in_row_spacing_cm": "15-20",
            "planting_window": "November to January",
            "seed_rate_kg_per_ha": "25-30",
            "soil_requirements": "Well-drained soils, pH 5.5-7.0",
            "fertilizer_basal": "Compound D: 100-150 kg/ha",
            "key_pests": ["Pod Borer", "Aphids", "Flower Thrips", "Bruchids"],
            "use": ["Grain (high market value for white grain)", "Leaves"],
            "harvesting": "Early maturity allows double cropping",
            "post_harvest": "Treat for bruchids or use hermetic storage"
        }
    },

    # ============================================================
    # BAMBARA NUTS (Nyimo) - Indigenous Legume
    # ============================================================
    {
        "crop_name": "Bambara Nuts",
        "variety_name": "Local Red",
        "breeder": "Landrace",
        "days_to_maturity": 130,
        "yield_potential_low": 0.5,
        "yield_potential_high": 1.5,
        "description": "Traditional red-seeded bambara nut landrace. One of Africa's most important indigenous crops. Extremely drought tolerant. Produces underground pods like groundnuts. Rich in protein.",
        "characteristics": {
            "drought_tolerance": "extremely high",
            "heat_tolerance": "very high",
            "seed_color": "red",
            "region_suitability": ["Natural Region III", "Natural Region IV", "Natural Region V"],
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "15-20",
            "planting_depth_cm": "3-5",
            "planting_window": "November to December",
            "seed_rate_kg_per_ha": "50-80",
            "soil_requirements": "Light, well-drained sandy soils. pH 5.0-6.5. Produces poorly in heavy clays.",
            "optimal_rainfall_mm": "300-500",
            "fertilizer_basal": "Minimal or none. Compound D: 50-100 kg/ha if available. Fixes own nitrogen.",
            "key_pests": ["Termites", "Groundnut Bruchid", "Millipedes"],
            "key_diseases": ["Cercospora Leaf Spot", "Root Rot (in waterlogged soils)"],
            "use": ["Boiled fresh (mutakura)", "Dried and ground into flour", "Roasted snack", "Livestock feed"],
            "weeding": "2-3 weedings. First at 3 weeks, second at 6 weeks.",
            "harvesting": "Uproot entire plant when leaves yellow and pods are mature. Dry plants for 1-2 weeks.",
            "post_harvest": "Shell, dry to <10%, store in airtight containers. Very good storage life.",
            "nutritional_value": "High protein (18-24%), good carbohydrates, complete food. Contains lysine (often limiting amino acid in cereal-based diets).",
            "cultural_significance": "Nyimo is a culturally important crop in Zimbabwe. Traditionally women's crop. Used in ceremonies.",
            "climate_resilience": "Produces food even in years when maize and other crops fail. Critical food security crop."
        }
    },
    {
        "crop_name": "Bambara Nuts",
        "variety_name": "Local Cream",
        "breeder": "Landrace",
        "days_to_maturity": 120,
        "yield_potential_low": 0.6,
        "yield_potential_high": 1.8,
        "description": "Cream/white-seeded bambara nut landrace. Slightly earlier than red type. Preferred for flour and commercial sale.",
        "characteristics": {
            "drought_tolerance": "extremely high",
            "seed_color": "cream/white",
            "region_suitability": ["Natural Region III", "Natural Region IV", "Natural Region V"],
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "15-20",
            "planting_window": "November to December",
            "seed_rate_kg_per_ha": "50-80",
            "soil_requirements": "Light, well-drained sandy soils, pH 5.0-6.5",
            "optimal_rainfall_mm": "300-500",
            "fertilizer_basal": "Minimal. Fixes own nitrogen.",
            "key_pests": ["Termites", "Groundnut Bruchid"],
            "use": ["Flour (for porridge fortification)", "Boiled", "Roasted"],
            "harvesting": "Uproot when leaves yellow",
            "nutritional_value": "High protein (18-24%), complete food"
        }
    },

    # ============================================================
    # BUTTERNUT / PUMPKIN - Important Food Security Vegetable
    # ============================================================
    {
        "crop_name": "Butternut",
        "variety_name": "Waltham",
        "breeder": "Open Pollinated",
        "days_to_maturity": 100,
        "yield_potential_low": 15.0,
        "yield_potential_high": 30.0,
        "description": "The standard butternut variety in Zimbabwe. Bell-shaped fruit, deep orange flesh. Very popular at markets. Good source of Vitamin A.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "fruit_weight_kg": "1.5-3.0",
            "flesh_color": "deep orange",
            "region_suitability": ["Natural Region I", "Natural Region II", "Natural Region III", "Natural Region IV"],
            "planting_method": "Direct seed",
            "planting_window": "October to December (warm season crop)",
            "row_spacing_cm": 200,
            "in_row_spacing_cm": "60-80",
            "planting_depth_cm": "3-5",
            "seed_rate_kg_per_ha": "3-4",
            "soil_requirements": "Fertile, well-drained loams to clay loams, pH 5.5-6.8. High organic matter preferred.",
            "optimal_rainfall_mm": "500-800",
            "fertilizer_basal": "Compound D: 300-400 kg/ha or manure: 10-20 t/ha at planting",
            "fertilizer_top_dress": "LAN: 100 kg/ha at first runner stage",
            "key_pests": ["Fruit Fly", "Pumpkin Fly", "Aphids", "Red Spider Mite", "Cutworm"],
            "key_diseases": ["Powdery Mildew", "Downy Mildew", "Anthracnose", "Mosaic Virus"],
            "pest_management": "Fruit Fly: Use protein bait traps. Spray Malathion if severe. Remove fallen fruit.",
            "harvesting": "Harvest when stem dries and fruit skin is hard (cannot be dented with thumbnail). Leave 5cm stem attached.",
            "post_harvest": "Cure in sun for 7-10 days to harden skin. Excellent storage: 3-6 months in cool, dry, ventilated place.",
            "nutritional_value": "Excellent source of beta-carotene (Vitamin A), Vitamin C, potassium, and dietary fibre."
        }
    },
    {
        "crop_name": "Butternut",
        "variety_name": "Star 6001",
        "breeder": "Starke Ayres",
        "days_to_maturity": 90,
        "yield_potential_low": 20.0,
        "yield_potential_high": 40.0,
        "description": "High yielding hybrid butternut with uniform fruit shape and size. Excellent market appeal.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "fruit_weight_kg": "1.5-2.5",
            "flesh_color": "deep orange",
            "region_suitability": ["Natural Region I", "Natural Region II", "Natural Region III"],
            "planting_window": "October to December",
            "row_spacing_cm": 200,
            "in_row_spacing_cm": "60-80",
            "seed_rate_kg_per_ha": "3-4",
            "soil_requirements": "Fertile, well-drained soils, pH 5.5-6.8",
            "fertilizer_basal": "Compound D: 300-400 kg/ha",
            "key_pests": ["Fruit Fly", "Aphids", "Red Spider Mite"],
            "key_diseases": ["Powdery Mildew", "Downy Mildew"],
            "harvesting": "Harvest when stem dries and skin is hard",
            "post_harvest": "Cure and store 3-6 months"
        }
    },

    # ============================================================
    # PAPRIKA / CHILLIES - High-Value Cash Crop
    # ============================================================
    {
        "crop_name": "Paprika",
        "variety_name": "PRI Paprika",
        "breeder": "Paprika International",
        "days_to_maturity": 150,
        "yield_potential_low": 1.5,
        "yield_potential_high": 3.5,
        "description": "Standard paprika variety for Zimbabwe. High colour value (ASTA >180). Major export crop and high-value cash crop for smallholders. Dried pods are ground into paprika spice and oleoresin.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "heat_tolerance": "high",
            "asta_color_value": ">180",
            "region_suitability": ["Natural Region I", "Natural Region II", "Natural Region III"],
            "nursery_sowing": "July-August (sow in seedbeds 6-8 weeks before transplanting)",
            "transplanting_window": "September to November",
            "row_spacing_cm": 90,
            "in_row_spacing_cm": "30-40",
            "soil_requirements": "Well-drained, fertile loams, pH 5.5-6.8. Good organic matter.",
            "irrigation": "Regular. 25-30mm per week. Critical during flowering and fruit set.",
            "fertilizer_basal": "Compound S: 400-600 kg/ha at transplanting",
            "fertilizer_top_dress": "AN: 100-150 kg/ha at 4-week intervals (3-4 applications)",
            "key_pests": ["Aphids", "Fruit Fly", "Cutworm", "Bollworm", "Red Spider Mite"],
            "key_diseases": ["Bacterial Spot", "Cercospora Leaf Spot", "Phytophthora Root Rot", "Mosaic Virus"],
            "pest_management": "Aphids transmit viruses - control early with Imidacloprid/Dimethoate. Remove and destroy virus-infected plants.",
            "harvesting": "Pick when pods are fully red and mature. Multiple harvests over 3-4 months.",
            "drying": "Sun dry on raised platforms/racks for 7-14 days or use mechanical dryer. Pods must be dry enough to snap cleanly. Target moisture <11%.",
            "post_harvest": "Grade by colour and size. Pack in clean bags. Store in cool, dry place away from light (colour fades). Sell to registered buyers.",
            "market_info": "Zimbabwe is a significant paprika exporter. Contracts available through Paprika International and other buyers. ASTA colour value determines price."
        }
    },
    {
        "crop_name": "Paprika",
        "variety_name": "Serrano Hot Chilli",
        "breeder": "Various",
        "days_to_maturity": 120,
        "yield_potential_low": 2.0,
        "yield_potential_high": 5.0,
        "description": "Hot chilli variety for fresh market and drying. Growing demand in Zimbabwe for export and local processing (hot sauce, chilli flakes).",
        "characteristics": {
            "drought_tolerance": "moderate",
            "heat_tolerance": "high",
            "heat_level_shu": "10000-25000 (medium-hot)",
            "region_suitability": ["Natural Region I", "Natural Region II", "Natural Region III"],
            "nursery_sowing": "July-August",
            "transplanting_window": "September to November",
            "row_spacing_cm": 60,
            "in_row_spacing_cm": "30",
            "soil_requirements": "Well-drained, fertile soils, pH 5.5-6.8",
            "irrigation": "Regular. Moderate stress at fruiting can increase pungency.",
            "fertilizer_basal": "Compound S: 400-600 kg/ha",
            "fertilizer_top_dress": "AN: 100 kg/ha every 4 weeks",
            "key_pests": ["Aphids", "Fruit Fly", "Bollworm"],
            "key_diseases": ["Bacterial Spot", "Anthracnose", "Mosaic Virus"],
            "harvesting": "Multiple harvests. Pick red-ripe for drying, green for fresh market.",
            "post_harvest": "Sun dry or smoke dry. Grade and pack."
        }
    },

    # ============================================================
    # PEAS (Garden Peas) - Fresh Market & Export
    # ============================================================
    {
        "crop_name": "Peas",
        "variety_name": "Greenfeast",
        "breeder": "Open Pollinated",
        "days_to_maturity": 70,
        "yield_potential_low": 4.0,
        "yield_potential_high": 8.0,
        "description": "Standard garden pea for fresh market. Produces well-filled pods with sweet, tender peas. Popular for local market and freezing.",
        "characteristics": {
            "drought_tolerance": "low",
            "heat_tolerance": "low",
            "pea_type": "Garden/Shelling",
            "region_suitability": ["Natural Region I", "Natural Region II", "Irrigation"],
            "planting_method": "Direct seed",
            "planting_window": "March to June (cool season crop). Can also plant August-September with irrigation.",
            "row_spacing_cm": 30,
            "in_row_spacing_cm": "5-7",
            "planting_depth_cm": "3-5",
            "seed_rate_kg_per_ha": "80-120",
            "soil_requirements": "Well-drained, fertile loams, pH 6.0-7.0. Cool temperatures essential (15-20C optimal).",
            "optimal_temperature_c": "15-20 (will not set pods above 27C)",
            "irrigation": "Regular. 25mm per week. Peas are shallow-rooted and drought-sensitive.",
            "fertilizer_basal": "Compound D: 200-300 kg/ha. Peas fix nitrogen but benefit from starter fertilizer.",
            "inoculation": "Inoculate with Rhizobium leguminosarum for improved N-fixation",
            "key_pests": ["Pea Aphid", "Pod Borer", "Cutworm", "Thrips"],
            "key_diseases": ["Powdery Mildew", "Downy Mildew", "Fusarium Wilt", "Ascochyta Blight"],
            "pest_management": "Powdery Mildew: spray Sulphur or Triadimefon preventatively in warm/dry weather. Aphids: Dimethoate or natural predators.",
            "staking": "Tall varieties need staking with strings or netting. Dwarf types are self-supporting.",
            "harvesting": "Pick when pods are well-filled but still bright green. Test by pressing - peas should be tender. Pick every 2-3 days.",
            "post_harvest": "Highly perishable. Cool immediately. Shelf life 2-3 days at ambient, 7-10 days at 0-2C. Shell and freeze for longer storage."
        }
    },
    {
        "crop_name": "Peas",
        "variety_name": "Onward",
        "breeder": "Open Pollinated",
        "days_to_maturity": 75,
        "yield_potential_low": 5.0,
        "yield_potential_high": 10.0,
        "description": "Heavy-yielding garden pea, semi-dwarf. Reliable producer with excellent flavour. Good for freezing.",
        "characteristics": {
            "drought_tolerance": "low",
            "pea_type": "Garden/Shelling",
            "growth_habit": "Semi-dwarf (60-75cm)",
            "region_suitability": ["Natural Region I", "Natural Region II", "Irrigation"],
            "planting_window": "March to June (cool season)",
            "row_spacing_cm": 30,
            "in_row_spacing_cm": "5-7",
            "seed_rate_kg_per_ha": "80-120",
            "soil_requirements": "Well-drained loams, pH 6.0-7.0",
            "optimal_temperature_c": "15-20",
            "fertilizer_basal": "Compound D: 200-300 kg/ha",
            "key_pests": ["Pea Aphid", "Pod Borer"],
            "key_diseases": ["Powdery Mildew", "Fusarium Wilt"],
            "harvesting": "Pick every 2-3 days when pods well-filled"
        }
    },

    # ============================================================
    # SNOW PEAS / MANGE TOUT / SUGAR SNAP - Major Export Crop
    # ============================================================
    {
        "crop_name": "Snow Peas",
        "variety_name": "Oregon Sugar Pod",
        "breeder": "Open Pollinated",
        "days_to_maturity": 65,
        "yield_potential_low": 3.0,
        "yield_potential_high": 6.0,
        "description": "Flat-podded mange tout for export. Entire pod eaten before peas develop. One of Zimbabwe's top horticultural exports to EU and UK markets. High-value crop requiring strict quality control.",
        "characteristics": {
            "drought_tolerance": "low",
            "heat_tolerance": "low",
            "pea_type": "Mange Tout/Snow Pea (flat pod, eaten whole)",
            "region_suitability": ["Natural Region I", "Natural Region II", "Irrigation"],
            "planting_method": "Direct seed",
            "planting_window": "March to July (cool season). Stagger plantings every 2-3 weeks for continuous supply.",
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "5-7",
            "planting_depth_cm": "3-5",
            "seed_rate_kg_per_ha": "80-100",
            "soil_requirements": "Well-drained, fertile soils, pH 6.0-7.0. Must be free of heavy metals and pesticide residues for export (GlobalGAP).",
            "optimal_temperature_c": "12-18 (very sensitive to heat)",
            "irrigation": "Drip irrigation essential for export quality. 25mm per week. Consistent moisture prevents pod distortion.",
            "fertilizer_basal": "2:3:4 at 400-600 kg/ha. Foliar calcium for pod quality.",
            "trellising": "ESSENTIAL. Use 1.5-2m poles with netting or string trellis. Pods must hang freely for straight, clean pods.",
            "key_pests": ["Pea Aphid", "Leaf Miner", "Thrips", "American Bollworm"],
            "key_diseases": ["Powdery Mildew", "Downy Mildew", "Ascochyta Blight", "Fusarium Wilt"],
            "pest_management": "EXPORT CROPS: Only use approved pesticides with correct pre-harvest intervals (PHI). Check EU MRL (Maximum Residue Limit) database. Keep spray records. IPM approach essential.",
            "harvesting": "Pick DAILY when pods are flat, translucent, and peas barely visible. Pods must be straight, unblemished, uniform green. Grade strictly.",
            "post_harvest": "COLD CHAIN CRITICAL: Cool to 2-4C within 1 hour of harvest. Pack in approved cartons. Transport in refrigerated trucks. Shelf life 7-10 days at 0-2C.",
            "export_requirements": "GlobalGAP certification required. Traceability from seed to pack. Pesticide residue testing. Phytosanitary certificate.",
            "market_info": "Major buyers: UK supermarkets, EU fresh produce importers. Contracts through Zimbabwean horticultural exporters (e.g., Nhimbe Fresh, Interfresh)."
        }
    },
    {
        "crop_name": "Snow Peas",
        "variety_name": "Sugar Snap",
        "breeder": "Various",
        "days_to_maturity": 68,
        "yield_potential_low": 4.0,
        "yield_potential_high": 8.0,
        "description": "Round-podded sugar snap pea for export. Eaten whole with developed peas inside. Crunchy, sweet. Growing demand in EU markets.",
        "characteristics": {
            "drought_tolerance": "low",
            "pea_type": "Sugar Snap (round pod, eaten whole with peas)",
            "region_suitability": ["Natural Region I", "Natural Region II", "Irrigation"],
            "planting_window": "March to July (cool season)",
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "5-7",
            "seed_rate_kg_per_ha": "80-100",
            "soil_requirements": "Well-drained, fertile soils, pH 6.0-7.0",
            "optimal_temperature_c": "12-18",
            "irrigation": "Drip irrigation essential",
            "trellising": "ESSENTIAL. 1.5-2m support.",
            "key_pests": ["Pea Aphid", "Leaf Miner", "Thrips"],
            "key_diseases": ["Powdery Mildew", "Downy Mildew"],
            "harvesting": "Pick when pods are round, plump, and peas visible but pod still tender and stringless",
            "post_harvest": "Cool immediately to 2-4C. Strict cold chain for export.",
            "export_requirements": "GlobalGAP certification, pesticide residue compliance"
        }
    },

    # ============================================================
    # BLUEBERRIES - High-Value Export Fruit
    # ============================================================
    {
        "crop_name": "Blueberries",
        "variety_name": "Legacy",
        "breeder": "USDA/Introduced",
        "days_to_maturity": 730,
        "yield_potential_low": 5.0,
        "yield_potential_high": 12.0,
        "description": "Southern highbush blueberry variety suited to Zimbabwe's climate. Produces during the Northern Hemisphere off-season (September-December), commanding premium export prices to EU and UK. First commercial harvest in year 2-3.",
        "characteristics": {
            "crop_type": "Perennial fruit (lifespan 15-20+ years)",
            "drought_tolerance": "low",
            "heat_tolerance": "moderate",
            "chill_hours_required": "400-600 (low chill - suited to Zimbabwe)",
            "berry_size": "medium-large",
            "flavour": "Sweet, aromatic",
            "firmness": "good (important for export shelf life)",
            "region_suitability": ["Natural Region I", "Natural Region II (highveld)"],
            "altitude": "Above 1200m preferred for adequate winter chill (Harare, Marondera, Nyanga, Juliasdale)",
            "planting_method": "Transplant tissue-culture or rooted cuttings into prepared beds",
            "planting_window": "September to November (spring planting into permanent beds)",
            "row_spacing_m": "2.5-3.0",
            "in_row_spacing_m": "0.8-1.0",
            "plants_per_ha": "3300-5000",
            "soil_requirements": "ACIDIC soil essential: pH 4.5-5.5. Sandy, well-drained, high organic matter. Most Zimbabwe soils need acidification with elemental sulphur or acidifying fertilizers.",
            "soil_preparation": "Incorporate pine bark, sawdust, or peat moss. Raised beds recommended. Mulch heavily with pine needles or wood chips (10-15cm).",
            "irrigation": "Drip irrigation ESSENTIAL. 25-30mm per week. Blueberries have shallow, fibrous root systems - cannot tolerate drought or waterlogging.",
            "water_quality": "pH <6.5 preferred. Alkaline irrigation water must be acidified.",
            "fertilizer_programme": "Use acidifying fertilizers (Ammonium Sulphate, NOT Calcium-based). Fertigation through drip. NPK 10:5:10 at 150-200 kg/ha/year split into weekly applications.",
            "fertilizer_note": "NEVER use Compound D or lime on blueberries - they raise pH and kill the plant. Use acid-forming fertilizers only.",
            "pruning": "Annual winter pruning essential. Remove old/unproductive wood, thin fruiting laterals. Train open vase shape for light penetration.",
            "key_pests": ["Fruit Fly (Drosophila suzukii)", "Birds", "Aphids", "Mealybug", "Red Spider Mite"],
            "key_diseases": ["Botrytis (Grey Mould)", "Anthracnose", "Phytophthora Root Rot", "Blueberry Rust"],
            "pest_management": "Fruit Fly: netting, traps, Spinosad. Birds: netting essential over fruiting blocks. Botrytis: ensure good airflow, spray preventatively at flowering.",
            "harvesting": "Hand-pick when berries are fully blue with waxy bloom. Pick every 5-7 days during season. Handle GENTLY - berries bruise easily.",
            "harvest_season": "September to December (Zimbabwe's counter-season advantage for Northern Hemisphere markets)",
            "post_harvest": "COLD CHAIN CRITICAL: Pre-cool to 0-2C within 2 hours. Pack in 125g/250g punnets. MAP (Modified Atmosphere Packaging) extends shelf life. Air-freight to EU/UK within 48 hours.",
            "yield_timeline": "Year 1: establishment only. Year 2: light crop (1-2 t/ha). Year 3+: full production (5-12 t/ha).",
            "economics": "Investment: USD 15,000-25,000/ha establishment. Returns: USD 30,000-80,000/ha at full production. Payback in 3-4 years.",
            "export_requirements": "GlobalGAP, GRASP. Pesticide residue compliance (EU MRLs). Cold chain certification. Phytosanitary certificate.",
            "market_info": "Zimbabwe exports blueberries Sep-Dec when Northern Hemisphere supply is low. Premium prices USD 8-15/kg. Major buyers: UK retailers, EU importers, Middle East."
        }
    },
    {
        "crop_name": "Blueberries",
        "variety_name": "Ventura",
        "breeder": "International/Licensed",
        "days_to_maturity": 730,
        "yield_potential_low": 6.0,
        "yield_potential_high": 15.0,
        "description": "High-yielding southern highbush variety with excellent firmness for long-distance export. Low chill requirement makes it well-suited to Zimbabwe's highveld.",
        "characteristics": {
            "crop_type": "Perennial fruit (lifespan 15-20+ years)",
            "chill_hours_required": "300-500 (very low chill)",
            "berry_size": "large",
            "firmness": "excellent (key for air-freight export)",
            "flavour": "Sweet-tart, good",
            "region_suitability": ["Natural Region I", "Natural Region II (highveld)"],
            "altitude": "Above 1200m preferred",
            "row_spacing_m": "2.5-3.0",
            "in_row_spacing_m": "0.8-1.0",
            "soil_requirements": "ACIDIC: pH 4.5-5.5. Sandy, high organic matter. Mulch with pine bark.",
            "irrigation": "Drip irrigation ESSENTIAL. 25-30mm per week.",
            "fertilizer_programme": "Acidifying fertilizers only (Ammonium Sulphate). Fertigation.",
            "pruning": "Annual winter pruning. Open vase shape.",
            "key_pests": ["Fruit Fly", "Birds", "Mealybug"],
            "key_diseases": ["Botrytis", "Anthracnose", "Phytophthora"],
            "harvest_season": "September to December",
            "post_harvest": "Pre-cool to 0-2C immediately. Air-freight within 48 hours.",
            "economics": "Premium export crop. USD 30,000-80,000/ha revenue at full production."
        }
    },
    {
        "crop_name": "Blueberries",
        "variety_name": "Eureka Sunrise",
        "breeder": "Mountain Blue (Australia)/Licensed",
        "days_to_maturity": 730,
        "yield_potential_low": 8.0,
        "yield_potential_high": 18.0,
        "description": "Ultra-low chill variety from Australia's breeding programme. Earliest to produce in Zimbabwe (August-September). Very large berries with outstanding export quality.",
        "characteristics": {
            "crop_type": "Perennial fruit",
            "chill_hours_required": "150-300 (ultra-low - ideal for subtropical zones)",
            "berry_size": "very large (>2g)",
            "firmness": "excellent",
            "region_suitability": ["Natural Region I", "Natural Region II"],
            "soil_requirements": "ACIDIC: pH 4.5-5.5. Raised beds with pine bark/peat media.",
            "irrigation": "Drip irrigation ESSENTIAL",
            "fertilizer_programme": "Acid-forming fertilizers only. Weekly fertigation.",
            "harvest_season": "August to November (earliest season - premium prices)",
            "post_harvest": "Cold chain essential. Air-freight to EU/UK.",
            "economics": "Early-season berries command highest prices (USD 12-18/kg)."
        }
    },

    # ============================================================
    # GREEN BEANS / FINE BEANS - Top Horticultural Export
    # ============================================================
    {
        "crop_name": "Green Beans",
        "variety_name": "Samantha",
        "breeder": "Pop Vriend/Hazera",
        "days_to_maturity": 55,
        "yield_potential_low": 8.0,
        "yield_potential_high": 15.0,
        "description": "Premium fine bean (haricot vert) variety for export. Slim, straight, stringless pods. Zimbabwe's fine beans are a major export to EU supermarkets, earning significant foreign currency.",
        "characteristics": {
            "drought_tolerance": "low",
            "bean_type": "Fine bean (haricot vert) - pod diameter <8mm",
            "pod_color": "dark green",
            "stringless": True,
            "region_suitability": ["Natural Region I", "Natural Region II", "Irrigation"],
            "planting_method": "Direct seed",
            "planting_window": "Year-round with irrigation. Peak export windows: March-October (EU winter/spring demand).",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "5-7",
            "planting_depth_cm": "3-5",
            "seed_rate_kg_per_ha": "60-80",
            "soil_requirements": "Well-drained, fertile loams, pH 5.8-6.5. Must be free of contaminants for export.",
            "optimal_temperature_c": "18-25 (will not set pods above 30C or below 12C)",
            "irrigation": "Drip irrigation essential for export quality. 25mm per week. Consistent moisture prevents curved/distorted pods.",
            "fertilizer_basal": "2:3:4 at 400-600 kg/ha at planting",
            "fertilizer_top_dress": "LAN: 100 kg/ha at flowering. Foliar calcium and boron for pod quality.",
            "key_pests": ["Bean Fly (CRITICAL first 3 weeks)", "Whitefly", "American Bollworm", "Aphids", "Red Spider Mite", "Thrips"],
            "key_diseases": ["Rust", "Angular Leaf Spot", "Anthracnose", "Bacterial Blight", "Sclerotinia (White Mould)"],
            "pest_management": "Bean Fly: Imidacloprid seed dressing ESSENTIAL. Whitefly/Aphids: IPM with yellow sticky traps + Spinosad. EXPORT: Only EU-approved pesticides. Keep spray records. Observe PHIs strictly.",
            "harvesting": "Pick every 2 days when pods are slim (<8mm diameter for fine beans). Pods must be straight, unblemished, uniform length (10-13cm). Grade in field.",
            "post_harvest": "COLD CHAIN: Cool to 4-6C within 1 hour. Sort, grade by length/diameter. Pack in approved cartons (1.5kg/4kg). Barcode traceability.",
            "export_requirements": "GlobalGAP certification mandatory. Sedex/SMETA ethical audit. Pesticide residue testing per shipment. Phytosanitary certificate.",
            "market_info": "Top export crop. Buyers: Tesco, Marks & Spencer, Waitrose via Zimbabwean exporters. Price: USD 2-4/kg FOB."
        }
    },
    {
        "crop_name": "Green Beans",
        "variety_name": "Bronco",
        "breeder": "Syngenta",
        "days_to_maturity": 52,
        "yield_potential_low": 6.0,
        "yield_potential_high": 12.0,
        "description": "Bobby bean / standard green bean for fresh market and processing. Thicker pod than fine beans. Good for local market and canning.",
        "characteristics": {
            "drought_tolerance": "low",
            "bean_type": "Bobby/Standard green bean - pod diameter 8-12mm",
            "pod_color": "medium green",
            "stringless": True,
            "region_suitability": ["Natural Region I", "Natural Region II", "Natural Region III"],
            "planting_window": "Year-round with irrigation. September to April rainfed.",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "7-10",
            "seed_rate_kg_per_ha": "60-80",
            "soil_requirements": "Well-drained loams, pH 5.8-6.5",
            "fertilizer_basal": "Compound D: 300-400 kg/ha",
            "key_pests": ["Bean Fly", "Whitefly", "Bollworm"],
            "key_diseases": ["Rust", "Angular Leaf Spot", "Anthracnose"],
            "harvesting": "Pick every 3-4 days. Thicker pod acceptable for local market."
        }
    },
    {
        "crop_name": "Green Beans",
        "variety_name": "Amy",
        "breeder": "Pop Vriend/Hazera",
        "days_to_maturity": 55,
        "yield_potential_low": 8.0,
        "yield_potential_high": 14.0,
        "description": "Extra-fine bean for premium export. Very slim pods (<6mm), dark green. Commands highest prices in EU market.",
        "characteristics": {
            "drought_tolerance": "low",
            "bean_type": "Extra-fine bean (haricot vert) - pod diameter <6mm",
            "pod_color": "dark green",
            "stringless": True,
            "region_suitability": ["Natural Region I", "Natural Region II", "Irrigation"],
            "planting_window": "Year-round with irrigation",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "4-6",
            "seed_rate_kg_per_ha": "70-90",
            "soil_requirements": "Fertile, well-drained, pH 5.8-6.5",
            "irrigation": "Drip essential. Consistent moisture critical.",
            "fertilizer_basal": "2:3:4 at 500-600 kg/ha",
            "key_pests": ["Bean Fly", "Whitefly", "Bollworm", "Thrips"],
            "harvesting": "Pick DAILY. Pods must be <6mm diameter. Extreme grading required.",
            "post_harvest": "Cold chain within 1 hour. Air-freight to EU.",
            "export_requirements": "GlobalGAP, GRASP. Premium price: USD 4-6/kg FOB."
        }
    },

    # ============================================================
    # TEA - Eastern Highlands Plantation Crop
    # ============================================================
    {
        "crop_name": "Tea",
        "variety_name": "SFS 150",
        "breeder": "Tea Research Foundation (Malawi/Zimbabwe)",
        "days_to_maturity": 1095,
        "yield_potential_low": 2.0,
        "yield_potential_high": 4.5,
        "description": "Clonal tea variety for Zimbabwe's Eastern Highlands. High yielding with good quality made tea. Grown commercially by Tanganda Tea Company and smallholders in Honde Valley, Chipinge, and Nyanga.",
        "characteristics": {
            "crop_type": "Perennial (productive for 50-100+ years)",
            "region_suitability": ["Eastern Highlands (Honde Valley, Chipinge, Nyanga, Chimanimani)"],
            "altitude": "900-2000m (>1200m for best quality)",
            "rainfall_requirement_mm": "1200-2000 per year, well-distributed",
            "planting_method": "Transplant rooted cuttings (vegetative propagation from clonal material)",
            "planting_window": "November to February (rainy season)",
            "row_spacing_m": "1.2-1.5",
            "in_row_spacing_m": "0.6-0.75",
            "plants_per_ha": "9000-13000",
            "soil_requirements": "Deep, well-drained acid soils, pH 4.5-5.5. Red loams ideal. Avoid waterlogging.",
            "fertilizer_programme": "NPK 2:1:1 at 200-400 kg N/ha/year. Split into 4-6 applications. Use Ammonium Sulphate as N source (maintains acidity).",
            "pruning": "Prune every 3-4 years to maintain plucking table at 60-75cm. Light skiffing between pruning cycles.",
            "plucking": "Pluck 'two leaves and a bud' every 7-14 days depending on season. Quality depends on fine plucking.",
            "key_pests": ["Tea Mosquito Bug (Helopeltis)", "Red Spider Mite", "Termites", "Nematodes"],
            "key_diseases": ["Blister Blight", "Root Disease (Armillaria)", "Grey Blight"],
            "processing": "Wither (12-18hrs) -> Roll/CTC -> Oxidise/Ferment (1-2hrs) -> Dry (90-100C) -> Sort/Grade",
            "yield_timeline": "Year 1-3: establishment, no harvest. Year 4+: light plucking. Year 6+: full production.",
            "market_info": "Zimbabwe produces ~24,000 tonnes annually. Tanganda Tea is largest producer. Exports to UK, Pakistan, EU.",
            "economics": "High establishment cost but long productive life. Smallholder outgrower schemes available through Tanganda."
        }
    },
    {
        "crop_name": "Tea",
        "variety_name": "PC 108",
        "breeder": "Tea Research Foundation",
        "days_to_maturity": 1095,
        "yield_potential_low": 1.8,
        "yield_potential_high": 3.5,
        "description": "Quality-focused clonal tea variety. Produces premium-grade tea with distinctive flavour. Lower yielding but higher quality grades.",
        "characteristics": {
            "crop_type": "Perennial",
            "region_suitability": ["Eastern Highlands"],
            "altitude": "1200-2000m (high altitude for quality)",
            "soil_requirements": "Deep, acid soils, pH 4.5-5.5",
            "planting_window": "November to February",
            "row_spacing_m": "1.2-1.5",
            "in_row_spacing_m": "0.6-0.75",
            "fertilizer_programme": "NPK at 200-350 kg N/ha/year",
            "plucking": "Two leaves and a bud. Fine plucking for premium grades.",
            "key_pests": ["Tea Mosquito Bug", "Red Spider Mite"],
            "market_info": "Premium tea grades for speciality markets"
        }
    },

    # ============================================================
    # SESAME - Growing Export Crop
    # ============================================================
    {
        "crop_name": "Sesame",
        "variety_name": "Lindi White",
        "breeder": "ICRISAT/DR&SS",
        "days_to_maturity": 100,
        "yield_potential_low": 0.5,
        "yield_potential_high": 1.2,
        "description": "White-seeded sesame variety for export. Growing demand globally for sesame oil, tahini, and confectionery. Well-suited to Zimbabwe's lowveld and middleveld regions. Low-input crop ideal for smallholders.",
        "characteristics": {
            "drought_tolerance": "very high",
            "heat_tolerance": "very high",
            "seed_color": "white (premium export grade)",
            "region_suitability": ["Natural Region III", "Natural Region IV", "Natural Region V"],
            "planting_method": "Direct seed",
            "planting_window": "December to January (needs warm soil >25C)",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "10-15",
            "planting_depth_cm": "1-2 (very small seed - shallow sowing essential)",
            "seed_rate_kg_per_ha": "3-5 (mix with sand for even distribution)",
            "soil_requirements": "Well-drained sandy loams. pH 5.5-7.0. Avoid waterlogging (fatal to sesame).",
            "optimal_rainfall_mm": "400-600",
            "fertilizer_basal": "Compound D: 100-200 kg/ha. Low-input crop.",
            "key_pests": ["Aphids", "Sesame Webworm", "Gall Midge"],
            "key_diseases": ["Cercospora Leaf Spot", "Bacterial Blight", "Fusarium Wilt", "Charcoal Rot"],
            "pest_management": "Generally low pest pressure. Rotate with cereals. Avoid fields with history of Fusarium.",
            "harvesting": "CRITICAL TIMING: Harvest when lower capsules turn brown but before they shatter (sesame shatters easily). Cut plants, stack upright in shocks to dry. Shake seeds onto canvas/tarpaulin.",
            "post_harvest": "Clean seeds, dry to <6% moisture. Grade by colour (white commands premium). Pack in clean bags.",
            "market_info": "Growing global demand. Zimbabwe exports to Asia, Middle East, EU. White sesame commands USD 1,200-2,000/tonne. Contracts available through aggregators."
        }
    },
    {
        "crop_name": "Sesame",
        "variety_name": "IETC 32",
        "breeder": "ICRISAT",
        "days_to_maturity": 90,
        "yield_potential_low": 0.6,
        "yield_potential_high": 1.5,
        "description": "Early maturing sesame with non-shattering capsules. Easier to harvest mechanically. Good oil content.",
        "characteristics": {
            "drought_tolerance": "very high",
            "heat_tolerance": "very high",
            "seed_color": "white-cream",
            "capsule_type": "Semi non-shattering (easier harvest)",
            "region_suitability": ["Natural Region III", "Natural Region IV"],
            "planting_window": "December to January",
            "row_spacing_cm": 45,
            "in_row_spacing_cm": "10-15",
            "seed_rate_kg_per_ha": "3-5",
            "soil_requirements": "Well-drained sandy soils, pH 5.5-7.0",
            "fertilizer_basal": "Compound D: 100-200 kg/ha",
            "key_pests": ["Aphids", "Webworm"],
            "harvesting": "Semi non-shattering allows later harvest with less loss",
            "oil_content": "48-52%"
        }
    },

    # ============================================================
    # CASSAVA - Food Security in Northern Zimbabwe
    # ============================================================
    {
        "crop_name": "Cassava",
        "variety_name": "Sauti",
        "breeder": "IITA/DR&SS",
        "days_to_maturity": 365,
        "yield_potential_low": 15.0,
        "yield_potential_high": 35.0,
        "description": "Improved cassava variety with low cyanide content (sweet type). Important food security crop in northern Zimbabwe (Muzarabani, Guruve, Mt Darwin, Kariba). Produces starchy roots year-round. Extremely drought tolerant once established.",
        "characteristics": {
            "crop_type": "Root crop (harvested 9-18 months after planting)",
            "drought_tolerance": "extremely high",
            "heat_tolerance": "very high",
            "cyanide_level": "low (sweet type - safe with minimal processing)",
            "region_suitability": ["Natural Region III", "Natural Region IV", "Zambezi Valley"],
            "planting_method": "Stem cuttings (20-30cm mature stems)",
            "planting_window": "October to December (with first rains)",
            "row_spacing_cm": 100,
            "in_row_spacing_cm": "80-100",
            "planting_depth_cm": "Horizontal or angled, 5-10cm deep. Plant on mounds in wet areas.",
            "cuttings_per_ha": "10000",
            "soil_requirements": "Wide range including poor sandy soils. pH 4.5-7.5. Tolerates acid and infertile soils.",
            "optimal_rainfall_mm": "500-1500 (extremely adaptable)",
            "fertilizer_basal": "Minimal. Compound D: 100-200 kg/ha if available. Responds well to manure.",
            "key_pests": ["Cassava Mealy Bug", "Cassava Green Mite", "Whitefly (transmits Mosaic Virus)", "Termites"],
            "key_diseases": ["Cassava Mosaic Disease (CMD - MAJOR)", "Cassava Brown Streak Disease (CBSD)", "Bacterial Blight"],
            "pest_management": "CMD: Use CMD-resistant varieties (Sauti is resistant). Never take cuttings from mosaic-infected plants. Biological control of mealybug (Anagyrus parasitoid).",
            "weeding": "Weed 2-3 times in first 3 months before canopy closure",
            "harvesting": "Piecemeal harvest from 9 months onwards. Can leave in ground for up to 24 months as 'living storage'.",
            "post_harvest": "PERISHABLE: Fresh roots deteriorate within 48-72 hours. Process immediately: peel, soak (for bitter types), dry into chips/flour. Cassava flour stores for months.",
            "processing": "Peel -> Grate -> Soak/ferment (removes cyanide) -> Press -> Dry -> Mill into flour. Or: Peel -> Chip -> Sun-dry -> Mill.",
            "nutritional_value": "High in carbohydrates/energy. Low in protein and vitamins. Must be supplemented with protein-rich foods (beans, groundnuts).",
            "food_security": "Ultimate food security crop: produces calories on marginal land, stores in ground, tolerates drought. Critical for Zambezi Valley communities."
        }
    },
    {
        "crop_name": "Cassava",
        "variety_name": "Nyalanda",
        "breeder": "DR&SS Zimbabwe",
        "days_to_maturity": 365,
        "yield_potential_low": 12.0,
        "yield_potential_high": 30.0,
        "description": "Local improved cassava variety with CMD resistance. Good eating quality. Popular in Mashonaland and Zambezi Valley.",
        "characteristics": {
            "crop_type": "Root crop",
            "drought_tolerance": "extremely high",
            "cyanide_level": "low (sweet type)",
            "disease_resistance": ["Cassava Mosaic Disease (resistant)"],
            "region_suitability": ["Natural Region III", "Natural Region IV", "Zambezi Valley"],
            "planting_method": "Stem cuttings (20-30cm)",
            "planting_window": "October to December",
            "row_spacing_cm": 100,
            "in_row_spacing_cm": "80-100",
            "soil_requirements": "Very adaptable. Sandy to clay soils.",
            "fertilizer_basal": "Minimal or manure",
            "key_pests": ["Cassava Mealy Bug", "Green Mite"],
            "harvesting": "Piecemeal from 9 months. In-ground storage up to 24 months.",
            "processing": "Chip and dry into flour, or boil/roast fresh"
        }
    },

    # ============================================================
    # GARLIC - High-Value Vegetable
    # ============================================================
    {
        "crop_name": "Garlic",
        "variety_name": "Egyptian White",
        "breeder": "Open Pollinated",
        "days_to_maturity": 150,
        "yield_potential_low": 5.0,
        "yield_potential_high": 12.0,
        "description": "Standard white garlic for Zimbabwe market. Strong flavour. High-value crop with good returns for small-scale farmers. Zimbabwe imports significant garlic - local production is a profitable opportunity.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "bulb_type": "Softneck (white skin, stores well)",
            "region_suitability": ["Natural Region I", "Natural Region II", "Natural Region III"],
            "planting_method": "Individual cloves (break bulb, plant each clove)",
            "planting_window": "March to May (cool season - needs cold to bulb properly)",
            "row_spacing_cm": 20,
            "in_row_spacing_cm": "10-12",
            "planting_depth_cm": "3-5 (pointed end up)",
            "seed_rate_kg_per_ha": "800-1200 (cloves)",
            "soil_requirements": "Well-drained, fertile loams, pH 6.0-7.0. High organic matter. Never plant after onion/garlic (disease buildup).",
            "irrigation": "Regular. 20-25mm per week. Stop irrigation 2-3 weeks before harvest for curing.",
            "fertilizer_basal": "2:3:4 at 600-800 kg/ha at planting",
            "fertilizer_top_dress": "LAN: 100 kg/ha at 4 and 8 weeks. Stop N after bulbing begins.",
            "key_pests": ["Thrips", "Nematodes", "Onion Fly"],
            "key_diseases": ["White Rot (MAJOR - soil-borne, persists for 20+ years)", "Rust", "Downy Mildew", "Basal Rot"],
            "pest_management": "White Rot: NEVER plant garlic/onion in infected soil. No cure. Rotate fields. Use clean seed cloves.",
            "harvesting": "Harvest when 50-60% of leaves have dried. Lift carefully with fork.",
            "curing": "Cure for 2-4 weeks in warm, dry, ventilated shade. Tops can be braided for hanging storage.",
            "post_harvest": "Stores 3-6 months in cool, dry, ventilated conditions. Premium prices year-round.",
            "economics": "High value: USD 3-8/kg at retail. Import substitution opportunity. Small area (0.25-1 ha) can generate significant income."
        }
    },
    {
        "crop_name": "Garlic",
        "variety_name": "Purple Stripe",
        "breeder": "Open Pollinated",
        "days_to_maturity": 160,
        "yield_potential_low": 4.0,
        "yield_potential_high": 10.0,
        "description": "Hardneck garlic with purple-striped skin. Stronger flavour than white types. Larger cloves, easier to peel. Needs more cold.",
        "characteristics": {
            "bulb_type": "Hardneck (purple stripes, larger cloves, shorter storage)",
            "region_suitability": ["Natural Region I (highveld)", "Natural Region II"],
            "planting_window": "March to April (needs cold exposure for bulbing)",
            "row_spacing_cm": 20,
            "in_row_spacing_cm": "12-15",
            "seed_rate_kg_per_ha": "1000-1500",
            "soil_requirements": "Well-drained, fertile soils, pH 6.0-7.0",
            "irrigation": "Regular. Stop 2-3 weeks before harvest.",
            "fertilizer_basal": "2:3:4 at 600-800 kg/ha",
            "key_diseases": ["White Rot", "Rust"],
            "harvesting": "When 50-60% leaves dried. Remove scapes (flower stalks) for larger bulbs - scapes are edible.",
            "post_harvest": "Stores 2-4 months (shorter than softneck). Premium gourmet market."
        }
    },

    # ============================================================
    # STRAWBERRIES - Growing Export/Premium Market
    # ============================================================
    {
        "crop_name": "Strawberries",
        "variety_name": "Festival",
        "breeder": "University of Florida/Licensed",
        "days_to_maturity": 90,
        "yield_potential_low": 20.0,
        "yield_potential_high": 40.0,
        "description": "Short-day strawberry variety suited to Zimbabwe's highveld. Large, firm, bright red fruit. Growing industry for domestic premium market and limited export. Grown commercially around Harare, Marondera, and Nyanga.",
        "characteristics": {
            "crop_type": "Perennial grown as annual (replant each season for best quality)",
            "drought_tolerance": "low",
            "berry_size": "large",
            "firmness": "good",
            "day_length_response": "Short-day (flowers when days <12 hours - March-September in Zimbabwe)",
            "region_suitability": ["Natural Region I", "Natural Region II (highveld >1200m)"],
            "planting_method": "Transplant bare-root runners or plug plants",
            "planting_window": "March to April (for winter/spring production May-November)",
            "row_spacing_cm": "30 (on raised beds)",
            "in_row_spacing_cm": "25-30",
            "plants_per_ha": "40000-50000",
            "growing_system": "Raised beds with plastic mulch. Tunnel/greenhouse production for premium quality.",
            "soil_requirements": "Well-drained sandy loams, pH 5.5-6.5. High organic matter. Fumigated or solarised for disease control.",
            "irrigation": "Drip irrigation ESSENTIAL. 15-25mm per week. Avoid wetting fruit (Botrytis risk).",
            "fertilizer_programme": "Fertigation: NPK 12:6:24 weekly. High potassium for fruit quality and flavour.",
            "key_pests": ["Red Spider Mite (MAJOR)", "Aphids", "Thrips", "Slugs", "Birds"],
            "key_diseases": ["Botrytis (Grey Mould - MAJOR)", "Powdery Mildew", "Anthracnose", "Phytophthora Crown Rot"],
            "pest_management": "Red Spider Mite: biological control (Phytoseiulus predatory mite) or Abamectin. Botrytis: ventilation, avoid overhead irrigation, preventative fungicides (Switch/Teldor).",
            "harvesting": "Pick every 2-3 days when 3/4 red. Handle very gently. Pick into punnets directly.",
            "post_harvest": "HIGHLY PERISHABLE. Cool to 2-4C within 1 hour. Shelf life 3-5 days. Pack in 250g/500g punnets.",
            "economics": "Premium domestic prices: USD 5-10/kg. Growing demand from hotels, restaurants, supermarkets."
        }
    },
    {
        "crop_name": "Strawberries",
        "variety_name": "Chandler",
        "breeder": "UC Davis/Introduced",
        "days_to_maturity": 85,
        "yield_potential_low": 18.0,
        "yield_potential_high": 35.0,
        "description": "Well-known short-day variety with excellent flavour. Large fruit, good for fresh market. Widely available runners.",
        "characteristics": {
            "crop_type": "Perennial grown as annual",
            "berry_size": "large",
            "flavour": "excellent",
            "day_length_response": "Short-day",
            "region_suitability": ["Natural Region I", "Natural Region II"],
            "planting_window": "March to April",
            "row_spacing_cm": "30 (raised beds)",
            "in_row_spacing_cm": "25-30",
            "soil_requirements": "Well-drained sandy loams, pH 5.5-6.5",
            "irrigation": "Drip essential",
            "key_pests": ["Red Spider Mite", "Aphids", "Botrytis"],
            "harvesting": "Pick every 2-3 days when 3/4 red"
        }
    },

    # ============================================================
    # GREEN PEPPER / SWEET PEPPER
    # ============================================================
    {
        "crop_name": "Green Pepper",
        "variety_name": "California Wonder",
        "breeder": "Open Pollinated",
        "days_to_maturity": 75,
        "yield_potential_low": 20.0,
        "yield_potential_high": 40.0,
        "description": "Standard blocky green pepper. Can be left to ripen to red for premium price. Widely grown in Zimbabwe for fresh market.",
        "characteristics": {
            "drought_tolerance": "moderate",
            "fruit_shape": "blocky, 4-lobed",
            "fruit_color": "green (ripens to red)",
            "region_suitability": ["Natural Region I", "Natural Region II", "Natural Region III"],
            "nursery_sowing": "July-August in seedbeds/trays",
            "transplanting_window": "September to November (6-8 weeks after sowing)",
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "40-50",
            "soil_requirements": "Well-drained, fertile loams, pH 5.5-6.8. Rich in organic matter.",
            "irrigation": "Regular. 25-30mm per week. Drip preferred.",
            "fertilizer_basal": "Compound S: 400-600 kg/ha at transplanting",
            "fertilizer_top_dress": "LAN: 100-150 kg/ha every 3-4 weeks from flowering. Calcium Nitrate to prevent Blossom End Rot.",
            "key_pests": ["Aphids", "Fruit Fly", "Bollworm", "Red Spider Mite", "Cutworm"],
            "key_diseases": ["Bacterial Spot", "Phytophthora Blight", "Mosaic Virus", "Blossom End Rot (calcium deficiency)"],
            "pest_management": "Aphids: Imidacloprid at transplanting. Remove virus-infected plants. Mulch to maintain even soil moisture (prevents BER).",
            "staking": "Stake plants for support when fruit-laden. Prevents branches breaking.",
            "harvesting": "Pick green at full size, or leave to ripen red (commands premium). Multiple harvests over 3-4 months.",
            "post_harvest": "Grade by size and colour. Pack in crates. Shelf life 1-2 weeks at 7-10C."
        }
    },
    {
        "crop_name": "Green Pepper",
        "variety_name": "Star 9011",
        "breeder": "Starke Ayres",
        "days_to_maturity": 70,
        "yield_potential_low": 30.0,
        "yield_potential_high": 50.0,
        "description": "High-yielding hybrid sweet pepper. Blocky fruit with thick walls. Excellent for fresh market and export.",
        "characteristics": {
            "fruit_shape": "blocky, thick-walled",
            "fruit_color": "green (ripens to red/yellow depending on type)",
            "disease_resistance": ["Tobacco Mosaic Virus", "Bacterial Spot (moderate)"],
            "region_suitability": ["Natural Region I", "Natural Region II"],
            "nursery_sowing": "July-August",
            "transplanting_window": "September to November",
            "row_spacing_cm": 75,
            "in_row_spacing_cm": "40-50",
            "soil_requirements": "Fertile, well-drained, pH 5.5-6.8",
            "irrigation": "Drip preferred. 25-30mm per week.",
            "fertilizer_basal": "Compound S: 500-700 kg/ha",
            "key_pests": ["Aphids", "Fruit Fly", "Bollworm"],
            "harvesting": "Multiple harvests. Pick green or coloured."
        }
    },
]


def seed_varieties():
    """Seed the database with Zimbabwe crop varieties."""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        
        # Ensure table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS crop_varieties (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                crop_name TEXT NOT NULL,
                variety_name TEXT NOT NULL,
                breeder TEXT,
                days_to_maturity INTEGER,
                yield_potential_low DECIMAL(10,2),
                yield_potential_high DECIMAL(10,2),
                description TEXT,
                characteristics JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(crop_name, variety_name)
            )
        """)

        print(f"🌱 Seeding {len(ZIMBABWE_VARIETIES)} crop varieties...")
        
        inserted = 0
        updated = 0
        
        for v in ZIMBABWE_VARIETIES:
            cursor.execute("""
                INSERT INTO crop_varieties 
                (crop_name, variety_name, breeder, days_to_maturity, yield_potential_low, yield_potential_high, description, characteristics)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (crop_name, variety_name) 
                DO UPDATE SET 
                    days_to_maturity = EXCLUDED.days_to_maturity,
                    yield_potential_low = EXCLUDED.yield_potential_low,
                    yield_potential_high = EXCLUDED.yield_potential_high,
                    description = EXCLUDED.description,
                    characteristics = EXCLUDED.characteristics
                RETURNING (xmax = 0) AS inserted;
            """, (
                v['crop_name'], 
                v['variety_name'], 
                v['breeder'], 
                v['days_to_maturity'], 
                v['yield_potential_low'], 
                v['yield_potential_high'], 
                v['description'], 
                json.dumps(v['characteristics'])
            ))
            
            result = cursor.fetchone()
            if result and result[0]:
                inserted += 1
            else:
                updated += 1
                
        conn.commit()
        print(f"✅ Successfully seeded crop varieties.")
        print(f"   📊 {inserted} new varieties inserted")
        print(f"   🔄 {updated} existing varieties updated")
        
        # Print summary by crop
        cursor.execute("""
            SELECT crop_name, COUNT(*) as count 
            FROM crop_varieties 
            GROUP BY crop_name 
            ORDER BY count DESC
        """)
        print("\n📋 Varieties by Crop:")
        for row in cursor.fetchall():
            print(f"   • {row[0]}: {row[1]} varieties")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to seed varieties: {e}")
        if conn: 
            conn.close()
        return False


if __name__ == "__main__":
    seed_varieties()
