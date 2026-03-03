import os
import requests
from dotenv import load_dotenv

def verify_weather():
    """
    Verifies that the Weather API key is valid.
    Uses OpenWeatherMap as the default provider for verification.
    """
    load_dotenv()
    
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key or "your_" in api_key:
        print("❌ FAILED: WEATHER_API_KEY not found or is still a placeholder in .env")
        return False

    # Test coordinates for Harare, Zimbabwe
    lat = -17.8216
    lon = 31.0492
    
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    
    try:
        print(f"🔄 Attempting to fetch weather for Lat:{lat} Lon:{lon}...")
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp_k = data.get("main", {}).get("temp")
            print(f"✅ SUCCESS: Weather Data Received. Temp (K): {temp_k}")
            return True
        else:
            print(f"❌ FAILED: API returned status code {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Error connecting to Weather API: {e}")
        return False

if __name__ == "__main__":
    verify_weather()
