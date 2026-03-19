"""
UK Secure Dog Parks API
========================
FastAPI backend using MongoDB Atlas.

Run with:  uvicorn api:app --reload --port 8000
Env vars:  MONGO_URI  — MongoDB Atlas connection string
"""

import json
import math
import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection

# ─────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────

DATA_PATH = Path(__file__).parent / "data" / "parks.json"
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = "dogparks"
COL_NAME  = "parks"

app = FastAPI(
    title="UK Secure Dog Parks API",
    description="Find and explore secure, enclosed dog parks across the UK.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
#  DB connection (lazy singleton)
# ─────────────────────────────────────────────

_client: Optional[MongoClient] = None

def get_col() -> Collection:
    global _client
    try:
        if _client is None:
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        col = _client[DB_NAME][COL_NAME]
        # Seed if empty — wrapped separately so connection errors don't crash startup
        try:
            if col.count_documents({}) == 0:
                _seed(col)
        except Exception as e:
            print(f"Seed check failed: {e}")
        return col
    except Exception as e:
        _client = None
        raise HTTPException(status_code=503, detail=f"Database connection failed: {e}")


def _seed(col: Collection):
    if not DATA_PATH.exists():
        return
    parks = json.loads(DATA_PATH.read_text())
    for p in parks:
        # Use our id field as _id so upserts are idempotent
        p["_id"] = p["id"]
    col.delete_many({})
    col.insert_many(parks)
    # Create useful indexes
    col.create_index([("county", ASCENDING)])
    col.create_index([("town", ASCENDING)])
    col.create_index([("rating", DESCENDING)])
    col.create_index([("name", ASCENDING)])
    print(f"Seeded {len(parks)} parks into MongoDB")


def _clean(doc: dict) -> dict:
    """Remove MongoDB _id and normalise types."""
    doc.pop("_id", None)
    doc["is_secure"]        = bool(doc.get("is_secure", True))
    doc["is_fully_enclosed"]= bool(doc.get("is_fully_enclosed", False))
    doc["is_free"]          = bool(doc.get("is_free", False))
    doc["features"]         = doc.get("features") or []
    doc["dog_size_allowed"] = doc.get("dog_size_allowed") or []
    doc["images"]           = doc.get("images") or []
    doc["review_count"]     = doc.get("review_count") or 0
    return doc


# ─────────────────────────────────────────────
#  Haversine distance (km)
# ─────────────────────────────────────────────

def haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─────────────────────────────────────────────
#  Response models
# ─────────────────────────────────────────────

class DogParkSummary(BaseModel):
    id: str
    name: str
    town: str
    county: str
    postcode: Optional[str] = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_fully_enclosed: bool = False
    size_acres: Optional[float] = None
    price_per_hour: Optional[float] = None
    is_free: bool = False
    rating: Optional[float] = None
    review_count: int = 0
    features: list = []
    images: list = []
    distance_km: Optional[float] = None


class DogParkDetail(DogParkSummary):
    description: Optional[str] = None
    address: Optional[str] = ""
    country: Optional[str] = "UK"
    is_secure: bool = True
    fence_height_m: Optional[float] = None
    max_dogs: Optional[int] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    opening_hours: Optional[str] = None
    dog_size_allowed: list = []
    source: Optional[str] = None
    source_url: Optional[str] = None
    images: list = []
    last_verified: Optional[str] = None
    created_at: Optional[str] = None


class PaginatedParks(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    results: list[DogParkSummary]


# ─────────────────────────────────────────────
#  Root
# ─────────────────────────────────────────────


@app.get("/", include_in_schema=False)
def root():
    return {"message": "SafePaws UK API — visit /docs for the API reference"}


# ─────────────────────────────────────────────
#  Parks
# ─────────────────────────────────────────────

@app.get("/parks", response_model=PaginatedParks, tags=["parks"])
def list_parks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=2000),
    county: Optional[str] = None,
    town: Optional[str] = None,
    is_free: Optional[bool] = None,
    is_fully_enclosed: Optional[bool] = None,
    min_size_acres: Optional[float] = None,
    max_price_per_hour: Optional[float] = None,
    feature: Optional[list[str]] = Query(None),
    sort: str = Query("rating", pattern="^(rating|price|size|name)$"),
    q_search: Optional[str] = None,
):
    col = get_col()
    query: dict = {}

    if q_search:
        regex = {"$regex": q_search, "$options": "i"}
        query["$or"] = [
            {"name": regex}, {"description": regex},
            {"town": regex}, {"county": regex}, {"postcode": regex},
        ]
    if county:
        query["county"] = {"$regex": county, "$options": "i"}
    if town:
        query["town"] = {"$regex": town, "$options": "i"}
    if is_free is not None:
        query["is_free"] = is_free
    if is_fully_enclosed is not None:
        query["is_fully_enclosed"] = is_fully_enclosed
    if min_size_acres is not None:
        query["size_acres"] = {"$gte": min_size_acres}
    if max_price_per_hour is not None:
        query["$or"] = [
            {"is_free": True},
            {"price_per_hour": {"$lte": max_price_per_hour}},
        ]
    if feature:
        query["features"] = {"$all": feature}

    sort_field = {
        "rating": [("rating", DESCENDING)],
        "price":  [("price_per_hour", ASCENDING)],
        "size":   [("size_acres", DESCENDING)],
        "name":   [("name", ASCENDING)],
    }[sort]

    total  = col.count_documents(query)
    offset = (page - 1) * per_page
    docs   = list(col.find(query).sort(sort_field).skip(offset).limit(per_page))
    parks  = [DogParkSummary(**_clean(d)) for d in docs]

    return PaginatedParks(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        results=parks,
    )


@app.get("/parks/search", response_model=PaginatedParks, tags=["parks"])
def search_parks(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    col   = get_col()
    regex = {"$regex": q, "$options": "i"}
    query = {"$or": [
        {"name": regex}, {"description": regex},
        {"town": regex}, {"county": regex}, {"postcode": regex},
    ]}
    total  = col.count_documents(query)
    offset = (page - 1) * per_page
    docs   = list(col.find(query).skip(offset).limit(per_page))
    parks  = [DogParkSummary(**_clean(d)) for d in docs]
    return PaginatedParks(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        results=parks,
    )


@app.get("/parks/nearby", tags=["parks"])
def nearby_parks(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(25.0),
    limit: int = Query(20, ge=1, le=100),
    is_fully_enclosed: Optional[bool] = None,
):
    col   = get_col()
    query: dict = {"latitude": {"$ne": None}, "longitude": {"$ne": None}}
    if is_fully_enclosed is not None:
        query["is_fully_enclosed"] = is_fully_enclosed

    docs = list(col.find(query))
    results = []
    for d in docs:
        p = _clean(d)
        if p.get("latitude") and p.get("longitude"):
            dist = haversine(lat, lng, p["latitude"], p["longitude"])
            if dist <= radius_km:
                p["distance_km"] = round(dist, 2)
                results.append(p)

    results.sort(key=lambda x: x["distance_km"])
    return [DogParkSummary(**p) for p in results[:limit]]


@app.get("/parks/{park_id}", response_model=DogParkDetail, tags=["parks"])
def get_park(park_id: str):
    col = get_col()
    doc = col.find_one({"id": park_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Park not found")
    return DogParkDetail(**_clean(doc))


# ─────────────────────────────────────────────
#  Meta
# ─────────────────────────────────────────────

@app.get("/counties", tags=["meta"])
def list_counties():
    col = get_col()
    pipeline = [
        {"$match": {"county": {"$ne": ""}}},
        {"$group": {"_id": "$county", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    return [{"county": r["_id"], "count": r["count"]} for r in col.aggregate(pipeline)]


@app.get("/towns", tags=["meta"])
def list_towns(county: Optional[str] = None):
    col   = get_col()
    match: dict = {"town": {"$ne": ""}}
    if county:
        match["county"] = {"$regex": county, "$options": "i"}
    pipeline = [
        {"$match": match},
        {"$group": {"_id": "$town", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    return [{"town": r["_id"], "count": r["count"]} for r in col.aggregate(pipeline)]


@app.get("/features", tags=["meta"])
def list_features():
    col  = get_col()
    docs = col.find({}, {"features": 1})
    counts: dict[str, int] = {}
    for d in docs:
        for f in (d.get("features") or []):
            counts[f] = counts.get(f, 0) + 1
    return [{"feature": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])]


@app.get("/stats", tags=["meta"])
def stats():
    col   = get_col()
    total = col.count_documents({})
    pipeline = [{"$group": {
        "_id": None,
        "enclosed": {"$sum": {"$cond": ["$is_fully_enclosed", 1, 0]}},
        "free":     {"$sum": {"$cond": ["$is_free", 1, 0]}},
        "avg_rating": {"$avg": "$rating"},
        "avg_price":  {"$avg": "$price_per_hour"},
        "counties": {"$addToSet": "$county"},
    }}]
    r = list(col.aggregate(pipeline))
    agg = r[0] if r else {}
    return {
        "total_parks":        total,
        "fully_enclosed":     agg.get("enclosed", 0),
        "free_parks":         agg.get("free", 0),
        "counties_covered":   len(agg.get("counties", [])),
        "avg_rating":         round(agg["avg_rating"], 2) if agg.get("avg_rating") else None,
        "avg_price_per_hour": round(agg["avg_price"],  2) if agg.get("avg_price")  else None,
    }


# ─────────────────────────────────────────────
#  Admin
# ─────────────────────────────────────────────

@app.post("/admin/reload", tags=["admin"])
def reload_data():
    """Re-seed the database from parks.json."""
    col = get_col()
    _seed(col)
    return {"reloaded": True, "total_parks": col.count_documents({})}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
