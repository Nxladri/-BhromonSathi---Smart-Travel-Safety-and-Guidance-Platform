from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_db_connection
import pyodbc
import requests
import math
import difflib
from typing import List


app = FastAPI(title = "Smart Travel Guidance API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#=================== Zone Matching ====================

KNOWN_ZONES = {
    "Sajnekhali":    (22.1239497, 88.8277877),
    "Sudhanyakhali": (22.1012082, 88.8018338),
    "Dobanki":       (21.9901, 88.7557),
    "Netidhopani":   (21.9208, 88.7443),
    "Jharkhali":     (22.0305947, 88.7012651),
    "Gosaba":        (22.1652274, 88.8078983),
    "Pakhiralay":    (22.1418561, 88.8335028),
    "Dayapur":       (22.1300368, 88.8479035),
    "Gadkhali":      (22.156247, 88.7638294),
    "Panchamukhani": (21.9500, 88.7400),
}

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    return R * c
 
 
def geocode_place(place_name):
    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": place_name, "count": 1, "language": "en"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            return (result["latitude"], result["longitude"])
    except requests.RequestException:
        pass
    return None
 
 
def resolve_zone(user_input: str):
    zone_names = list(KNOWN_ZONES.keys())
 
    for name in zone_names:
        if name.lower() == user_input.strip().lower():
            return {"match_type": "exact", "zone": name, "message": None}
 
    close_matches = difflib.get_close_matches(user_input, zone_names, n=1, cutoff=0.6)
    if close_matches:
        corrected = close_matches[0]
        return {
            "match_type": "corrected",
            "zone": corrected,
            "message": f"Did you mean '{corrected}'? Showing results for '{corrected}'.",
        }
 
    coords = geocode_place(user_input)
    if coords is None:
        return {
            "match_type": "not_found",
            "zone": None,
            "message": f"'{user_input}' could not be located. Please check the spelling "
                       f"or choose from: {', '.join(zone_names)}.",
        }
 
    user_lat, user_lon = coords
    distances = {
        name: haversine_distance(user_lat, user_lon, lat, lon)
        for name, (lat, lon) in KNOWN_ZONES.items()
    }
    nearest_zone = min(distances, key=distances.get)
    nearest_km = round(distances[nearest_zone], 1)
 
    return {
        "match_type": "nearest_suggestion",
        "zone": nearest_zone,
        "message": f"'{user_input}' is not currently covered by Safe Trail. "
                   f"The nearest supported zone is '{nearest_zone}' "
                   f"(~{nearest_km} km away). Showing results for '{nearest_zone}'.",
    }
 

#==================== Response Models ====================

class PrecautionItem(BaseModel):
    precaution_id : int
    scope_type : str
    phase : str
    category : str
    description : str

class RiskResponse(BaseModel):
    zone: str
    month: str
    avg_rainfall : float
    avg_wind_speed : float
    rainfall_risk : str
    wind_risk : str
    combined_risk : str





@app.get("/")
def read_root():
    return {"message": "App backend is running with SQL connection"}



#==================== Risk Assessment Endpoint ====================


@app.get("/risk-assessment")
def get_risk_assessment(zone: str, month: str):
    resolution = resolve_zone(zone)
    if resolution["match_type"] == "not_found":
        raise HTTPException(status_code=404, detail=resolution["message"])
    zone = resolution["zone"]



    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT LocationName, Months, AvgRainfall, AvgWindSpeed, RainfallRisk, WindRisk, YearsOfData
            FROM ZoneRiskByMonth
            WHERE LocationName = ? AND Months = ?"""


        cursor.execute(query, (zone, month))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"Risk assessment not found for the specified '{zone}' and '{month}'.")
        rain_risk = row.RainfallRisk
        wind_risk = row.WindRisk

        # Determine combined risk based on rainfall and wind risk
        risk_priority = {"Low": 1, "Medium": 2, "High": 3}
        combined_risk = max(rain_risk, wind_risk, key=lambda x: risk_priority.get(x, 0))

        response = {
            "zone": row.LocationName,
            "month": row.Months,
            "avg_rainfall": row.AvgRainfall,
            "avg_wind_speed": row.AvgWindSpeed,
            "rainfall_risk": rain_risk,
            "wind_risk": wind_risk,
            "combined_risk": combined_risk,
            "years_of_data": row.YearsOfData
        }

        if resolution['message']:
            response["notice"] = resolution['message']
            response["match_type"] = resolution['match_type']
        return response
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ============== Precautions Endpoint ==============

@app.get("/precautions", response_model=List[PrecautionItem])
def get_precautions(zone: str):
    resolution = resolve_zone(zone)
    if resolution["zone"] is None:
        raise HTTPException(status_code=404, detail=resolution["message"])
    resolved_zone = resolution["zone"]
 
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT PrecautionID, ScopeType, Phase, Category, Description
            FROM safety_precautions
            WHERE ScopeType = 'General' OR LocationName = ?
            ORDER BY
                CASE Phase
                    WHEN 'BeforeTrip' THEN 1
                    WHEN 'DuringTrip' THEN 2
                    WHEN 'Emergency' THEN 3
                END,
                ScopeType DESC
        """
        cursor.execute(query, resolved_zone)
        rows = cursor.fetchall()
        conn.close()
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
 
    if not rows:
        raise HTTPException(status_code=404, detail=f"No precautions found for '{resolved_zone}'.")
 
    return [
        {
            "precaution_id": row.PrecautionID,
            "scope_type": row.ScopeType,
            "phase": row.Phase,
            "category": row.Category,
            "description": row.Description,
        }
        for row in rows
    ]


#==================== Emergency Endpoints ====================
@app.get("/emergency-centers")
def get_emergency_centers():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            SELECT CenterID, CenterName, CenterType, NearestLocationName
            FROM EmergencyCenters
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
    except pyodbc.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if not rows:
        raise HTTPException(status_code=404, detail="No emergency centers found.")

    return [
        {
            "center_id": row.CenterID,
            "center_name": row.CenterName,
            "center_type": row.CenterType,
            "nearest_location_name": row.NearestLocationName,
        }
        for row in rows
    ]


# ====================== Hazard Briefing Endpoint(RAG text based on the user query) ======================
from typing import Optional
from rag_pipeline import get_hazard_briefing


class ChatMessage(BaseModel):
    role: str
    content: str


class HazardChatRequest(BaseModel):
    zone: str
    query: str
    history: Optional[List[ChatMessage]] = []


class HazardChatResponse(BaseModel):
    zone: str
    answer: str
    history: List[ChatMessage]


@app.post("/hazards", response_model=HazardChatResponse)
def get_hazards(request: HazardChatRequest):
    resolution = resolve_zone(request.zone)
    if resolution["zone"] is None:
        raise HTTPException(status_code=404, detail=resolution["message"])
    resolved_zone = resolution["zone"]

    history_as_dicts = [{"role": h.role, "content": h.content} for h in request.history]

    try:
        answer, updated_history = get_hazard_briefing(
            resolved_zone, request.query, history=history_as_dicts
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {str(e)}")

    return {
        "zone": resolved_zone,
        "answer": answer,
        "history": updated_history,
    }