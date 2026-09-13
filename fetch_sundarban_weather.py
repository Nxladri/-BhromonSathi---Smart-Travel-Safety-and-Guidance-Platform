"""
Fetch historical weather data for key Sundarban zones from Open-Meteo.
No API key required. Free for non-commercial use.

Output CSV columns ready for WeatherRecords table:
LocationID, LocationName, Date, Rainfall, WindSpeed, TempMax, TempMin
"""

import requests
import csv
import time

# Start with only the most important tourist / entry zones
# Verify these coordinates on Google Maps before final use
ZONES = {
    # Core forest-entry / watchtower stops (where tourists actually disembark)
    1:  {"name": "Sajnekhali",        "lat": 22.1239497, "lon": 88.8277877},
    2:  {"name": "Sudhanyakhali",     "lat": 22.1012082, "lon": 88.8018338},
    3:  {"name": "Dobanki",           "lat": 21.9901, "lon": 88.7557},
    4:  {"name": "Netidhopani",       "lat": 21.9208, "lon": 88.7443},
    5:  {"name": "Jharkhali",         "lat": 22.0305947, "lon": 88.7012651},

    # Stay / transit / gateway points
    6:  {"name": "Gosaba",            "lat": 22.1652274, "lon": 88.8078983},
    7:  {"name": "Pakhiralay",        "lat": 22.1418561, "lon": 88.8335028},
    8:  {"name": "Dayapur",           "lat": 22.1300368, "lon": 88.8479035},
    9:  {"name": "Gadkhali",          "lat": 22.156247, "lon": 88.7638294},

    # Notable creek/river route (relevant for boat/tide risk scoring)
    10: {"name": "Panchamukhani",     "lat": 21.9500, "lon": 88.7400},
}


BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
START_DATE = "2015-01-01"
END_DATE = "2024-12-31"
DAILY_VARS = "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max"

def fetch_zone_weather(location_id, name, lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "daily": DAILY_VARS,
        "timezone": "Asia/Kolkata",
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  Failed to fetch {name}: {e}")
        return []

    rows = []
    daily = data.get("daily", {})
    dates = daily.get("time", [])

    for i, date in enumerate(dates):
        rows.append({
            "LocationID": location_id,
            "LocationName": name,
            "Date": date,
            "Rainfall": daily["precipitation_sum"][i],
            "WindSpeed": daily["wind_speed_10m_max"][i],
            "TempMax": daily["temperature_2m_max"][i],
            "TempMin": daily["temperature_2m_min"][i],
        })

    return rows

def main():
    all_rows = []

    for loc_id, info in ZONES.items():
        print(f"Fetching weather for {info['name']}...")
        rows = fetch_zone_weather(loc_id, info["name"], info["lat"], info["lon"])
        all_rows.extend(rows)
        print(f"  → {len(rows)} daily records")
        
        time.sleep(8)  # small delay to be polite to the API

    if not all_rows:
        print("No data collected. Check your internet or coordinates.")
        return

    out_path = "sundarban_weather_history1.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nSaved {len(all_rows)} total records to {out_path}")
    print("Next: Inspect the CSV, then load into SQL Server WeatherRecords table.")

if __name__ == "__main__":
    main()