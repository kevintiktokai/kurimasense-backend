
import random
from datetime import datetime

BASE_PRICES = {
    "Maize": {"price": 240, "unit": "/t", "volatility": 0.02},
    "Wheat": {"price": 310, "unit": "/t", "volatility": 0.015},
    "Soybean": {"price": 480, "unit": "/t", "volatility": 0.025},
    "Tobacco": {"price": 3.20, "unit": "/kg", "volatility": 0.03},
    "Cotton": {"price": 1.15, "unit": "/lb", "volatility": 0.02},
    "Rice": {"price": 420, "unit": "/t", "volatility": 0.01},
    "Sorghum": {"price": 190, "unit": "/t", "volatility": 0.02},
}

def get_market_prices():
    """
    Generates market prices with random daily fluctuation.
    We seed the random generator with the current hour to keep it stable for a short period,
    or just random for live demo effect.
    """
    # Use current minute/10 to shift every 10 mins?
    # For demo, just random is fine but maybe stable per refresh?
    # Let's make it random but realistic.
    
    results = []
    
    for crop, data in BASE_PRICES.items():
        base = data["price"]
        vol = data["volatility"]
        
        # Random fluctuation +/- volatility
        change_pct = random.uniform(-vol, vol)
        current = base * (1 + change_pct)
        
        # Trend string
        trend_val = change_pct * 100
        sign = "+" if trend_val >= 0 else ""
        trend = f"{sign}{trend_val:.1f}%"
        
        # Format price
        price_fmt = f"${current:.2f}{data['unit']}"
        
        results.append({
            "crop": crop,
            "price": price_fmt,
            "trend": trend,
            "rawValue": current 
        })
        
    return results
