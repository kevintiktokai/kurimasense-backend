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
            "recommended_plant_population": 44000
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
            "grain_type": "white semi-flint"
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
            "grain_type": "white flint"
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
            "recommended_plant_population": 53000
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
            "grain_type": "white dent"
        }
    },
    {
        "crop_name": "Maize",
        "variety_name": "SC 727 (Nzou)",
        "breeder": "Seed Co",
        "days_to_maturity": 158,
        "yield_potential_low": 10.0,
        "yield_potential_high": 21.0,
        "description": "Late maturing white maize. The highest yielding hybrid in Africa for irrigated high-potential areas. Known as 'Nzou' (Elephant).",
        "characteristics": {
            "drought_tolerance": "high",
            "heat_tolerance": "high",
            "disease_resistance": ["Grey Leaf Spot", "Leaf Blight", "Rust", "Cob Rot"],
            "region_suitability": ["Natural Region I", "Natural Region II", "Irrigation"],
            "gls_tolerance": "very high",
            "grain_type": "white dent",
            "recommended_plant_population": 55000
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
            "grain_type": "white flint"
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
            "gls_tolerance": "very high"
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
            "curing_time": "5-7 days"
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
            "recommended_for": "Dry land farming"
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
            "leaf_size": "Broad"
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
            "growth_habit": "Fast"
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
            "seed_size": "medium"
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
            "pod_shattering": "moderate"
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
            "pod_height": "Good"
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
            "growth_habit": "Semi-determinate"
        }
    },

    # ============================================================
    # SORGHUM (Seed Co & SeedCo/ICRISAT)
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
            "tannin_content": "low"
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
            "tannin_content": "high"
        }
    },
    {
        "crop_name": "Sorghum",
        "variety_name": "Macia",
        "breeder": "ICRISAT",
        "days_to_maturity": 100,
        "yield_potential_low": 3.5,
        "yield_potential_high": 6.0,
        "description": "Open-pollinated variety with excellent food quality. Low tannin, good for sadza. Popular in communal areas.",
        "characteristics": {
            "drought_tolerance": "very high",
            "bird_resistance": "low",
            "use": ["Food", "Sadza"],
            "grain_color": "white",
            "tannin_content": "very low"
        }
    },

    # ============================================================
    # WHEAT (Seed Co - Winter Crop)
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
            "baking_quality": "excellent"
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
            "protein_content": "11-13%"
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
            "standability": "excellent"
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
            "staple_length": "28-30mm"
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
            "ginning_outturn": "38-40%"
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
            "plant_type": "Compact"
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
            "oil_content": "48-50%"
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
            "market": "Confectionery"
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
            "kernel_size": "medium-large"
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
            "plant_height": "medium"
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
            "oil_content": "44-47%"
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
            "oil_content": "43-46%"
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
            "cooking_time": "short"
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
            "seed_size": "medium"
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
            "growth_habit": "Determinate"
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
            "use": ["Boiling", "Roasting"]
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
            "flesh_color": "light yellow"
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
            "skin_color": "white"
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
            "flesh_color": "light yellow"
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
            "fruit_firmness": "good"
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
            "shelf_life": "excellent"
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
            "harvest_window": "extended"
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
            "fruit_firmness": "excellent"
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
            "bulb_color": "white"
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
            "bulb_color": "red"
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
            "uniformity": "excellent"
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
            "color": "blue-green"
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
            "head_shape": "round-flat"
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
            "head_weight": "5-8 kg"
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
