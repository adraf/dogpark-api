"""
UK Secure Dog Parks API
========================
FastAPI backend serving dog park data with full search, filter, and
location-based queries.

Endpoints:
  GET  /parks                  — list all parks (paginated, filterable)
  GET  /parks/{id}             — get single park by ID
  GET  /parks/nearby           — find parks near lat/lng
  GET  /parks/search           — full-text search
  GET  /counties               — list all counties
  GET  /towns                  — list all towns (optionally by county)
  GET  /features               — list all available features
  POST /parks/refresh          — re-run scraper (admin)

Run with:  uvicorn api:app --reload --port 8000
"""

import json
import math
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ─────────────────────────────────────────────
#  Config
# ─────────────────────────────────────────────

DATA_PATH = Path(__file__).parent / "data" / "parks.json"
DB_PATH = Path(__file__).parent / "data" / "parks.db"

app = FastAPI(
    title="UK Secure Dog Parks API",
    description="Find and explore secure, enclosed dog parks across the UK.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_PATH = Path(__file__).parent / "index.html"

@app.get("/", include_in_schema=False)
async def serve_frontend():
    if FRONTEND_PATH.exists():
        return FileResponse(str(FRONTEND_PATH))
    return {"message": "SafePaws UK API — visit /docs for the API reference"}


# ─────────────────────────────────────────────
#  Database
# ─────────────────────────────────────────────

def get_db():
    """Return a SQLite connection, creating tables and seeding if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    if _is_empty(conn):
        _seed_from_json(conn)
    return conn


@contextmanager
def db_conn():
    conn = get_db()
    try:
        yield conn
    finally:
        conn.close()


def _ensure_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS dog_parks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            address TEXT,
            town TEXT,
            county TEXT,
            postcode TEXT,
            country TEXT DEFAULT 'UK',
            latitude REAL,
            longitude REAL,
            is_secure INTEGER DEFAULT 1,
            is_fully_enclosed INTEGER DEFAULT 0,
            fence_height_m REAL,
            size_acres REAL,
            price_per_hour REAL,
            is_free INTEGER DEFAULT 0,
            phone TEXT,
            website TEXT,
            email TEXT,
            opening_hours TEXT,
            features TEXT DEFAULT '[]',
            dog_size_allowed TEXT DEFAULT '["small","medium","large"]',
            max_dogs INTEGER,
            source TEXT,
            source_url TEXT,
            rating REAL,
            review_count INTEGER DEFAULT 0,
            images TEXT DEFAULT '[]',
            last_verified TEXT,
            created_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_county ON dog_parks(county);
        CREATE INDEX IF NOT EXISTS idx_town   ON dog_parks(town);
        CREATE INDEX IF NOT EXISTS idx_postcode ON dog_parks(postcode);
    """)
    conn.commit()


def _is_empty(conn) -> bool:
    cur = conn.execute("SELECT COUNT(*) FROM dog_parks")
    return cur.fetchone()[0] == 0


def _seed_from_json(conn):
    if not DATA_PATH.exists():
        return
    parks = json.loads(DATA_PATH.read_text())
    for p in parks:
        p["features"] = json.dumps(p.get("features", []))
        p["dog_size_allowed"] = json.dumps(p.get("dog_size_allowed", []))
        p["images"] = json.dumps(p.get("images", []))
        p["is_secure"] = int(p.get("is_secure", True))
        p["is_fully_enclosed"] = int(p.get("is_fully_enclosed", False))
        p["is_free"] = int(p.get("is_free", False))
        cols = ", ".join(p.keys())
        placeholders = ", ".join(f":{k}" for k in p.keys())
        conn.execute(
            f"INSERT OR REPLACE INTO dog_parks ({cols}) VALUES ({placeholders})",
            p,
        )
    conn.commit()


def _row_to_dict(row) -> dict:
    d = dict(row)
    for field in ("features", "dog_size_allowed", "images"):
        if isinstance(d.get(field), str):
            try:
                d[field] = json.loads(d[field])
            except Exception:
                d[field] = []
    d["is_secure"] = bool(d.get("is_secure"))
    d["is_fully_enclosed"] = bool(d.get("is_fully_enclosed"))
    d["is_free"] = bool(d.get("is_free"))
    return d


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
    postcode: str
    latitude: Optional[float]
    longitude: Optional[float]
    is_fully_enclosed: bool
    size_acres: Optional[float]
    price_per_hour: Optional[float]
    is_free: bool
    rating: Optional[float]
    review_count: int
    features: list
    distance_km: Optional[float] = None


class DogParkDetail(DogParkSummary):
    description: Optional[str]
    address: str
    country: str
    is_secure: bool
    fence_height_m: Optional[float]
    max_dogs: Optional[int]
    phone: Optional[str]
    website: Optional[str]
    email: Optional[str]
    opening_hours: Optional[str]
    dog_size_allowed: list
    source: Optional[str]
    source_url: Optional[str]
    images: list
    last_verified: Optional[str]
    created_at: Optional[str]


class PaginatedParks(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int
    results: list[DogParkSummary]


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────




@app.get("/parks", response_model=PaginatedParks, tags=["parks"])
def list_parks(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=500),
    county: Optional[str] = None,
    town: Optional[str] = None,
    is_free: Optional[bool] = None,
    is_fully_enclosed: Optional[bool] = None,
    min_size_acres: Optional[float] = None,
    max_price_per_hour: Optional[float] = None,
    feature: Optional[list[str]] = Query(None),
    sort: str = Query("rating", regex="^(rating|price|size|name)$"),
):
    """
    List all parks with optional filters and pagination.
    Multiple `feature` query params are AND-ed together.
    """
    with db_conn() as conn:
        conditions = []
        params: dict = {}

        if county:
            conditions.append("LOWER(county) LIKE :county")
            params["county"] = f"%{county.lower()}%"
        if town:
            conditions.append("LOWER(town) LIKE :town")
            params["town"] = f"%{town.lower()}%"
        if is_free is not None:
            conditions.append("is_free = :is_free")
            params["is_free"] = int(is_free)
        if is_fully_enclosed is not None:
            conditions.append("is_fully_enclosed = :is_fully_enclosed")
            params["is_fully_enclosed"] = int(is_fully_enclosed)
        if min_size_acres is not None:
            conditions.append("size_acres >= :min_size_acres")
            params["min_size_acres"] = min_size_acres
        if max_price_per_hour is not None:
            conditions.append(
                "(price_per_hour <= :max_price OR is_free = 1)"
            )
            params["max_price"] = max_price_per_hour

        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        sort_col = {
            "rating": "rating DESC NULLS LAST",
            "price": "price_per_hour ASC NULLS LAST",
            "size": "size_acres DESC NULLS LAST",
            "name": "name ASC",
        }[sort]

        rows = conn.execute(
            f"SELECT * FROM dog_parks {where} ORDER BY {sort_col}",
            params,
        ).fetchall()

        parks = [_row_to_dict(r) for r in rows]

        # Feature filter (post-query — features stored as JSON)
        if feature:
            def has_features(p):
                return all(f in p.get("features", []) for f in feature)
            parks = [p for p in parks if has_features(p)]

        total = len(parks)
        offset = (page - 1) * per_page
        page_parks = parks[offset : offset + per_page]

        return PaginatedParks(
            total=total,
            page=page,
            per_page=per_page,
            pages=math.ceil(total / per_page) if total else 0,
            results=[DogParkSummary(**p) for p in page_parks],
        )


@app.get("/parks/search", response_model=PaginatedParks, tags=["parks"])
def search_parks(
    q: str = Query(..., min_length=2, description="Search query"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Full-text search across name, description, town, county, and postcode."""
    with db_conn() as conn:
        term = f"%{q.lower()}%"
        rows = conn.execute(
            """
            SELECT * FROM dog_parks
            WHERE LOWER(name)        LIKE :t
               OR LOWER(description) LIKE :t
               OR LOWER(town)        LIKE :t
               OR LOWER(county)      LIKE :t
               OR LOWER(postcode)    LIKE :t
            ORDER BY
              CASE
                WHEN LOWER(name) LIKE :t THEN 0
                WHEN LOWER(town) LIKE :t THEN 1
                ELSE 2
              END,
              rating DESC NULLS LAST
            """,
            {"t": term},
        ).fetchall()

        parks = [_row_to_dict(r) for r in rows]
        total = len(parks)
        offset = (page - 1) * per_page
        page_parks = parks[offset : offset + per_page]

        return PaginatedParks(
            total=total,
            page=page,
            per_page=per_page,
            pages=math.ceil(total / per_page) if total else 0,
            results=[DogParkSummary(**p) for p in page_parks],
        )


@app.get("/parks/nearby", tags=["parks"])
def nearby_parks(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_km: float = Query(25.0, description="Search radius in km"),
    limit: int = Query(20, ge=1, le=100),
    is_fully_enclosed: Optional[bool] = None,
):
    """Find parks within a given radius (km) of a lat/lng point."""
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM dog_parks WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
        ).fetchall()

    parks = [_row_to_dict(r) for r in rows]

    if is_fully_enclosed is not None:
        parks = [p for p in parks if p["is_fully_enclosed"] == is_fully_enclosed]

    # Annotate with distance and filter
    results = []
    for p in parks:
        dist = haversine(lat, lng, p["latitude"], p["longitude"])
        if dist <= radius_km:
            p["distance_km"] = round(dist, 2)
            results.append(p)

    results.sort(key=lambda p: p["distance_km"])
    return [DogParkSummary(**p) for p in results[:limit]]


@app.get("/parks/{park_id}", response_model=DogParkDetail, tags=["parks"])
def get_park(park_id: str):
    """Get full details for a single park."""
    with db_conn() as conn:
        row = conn.execute(
            "SELECT * FROM dog_parks WHERE id = ?", (park_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Park not found")
    return DogParkDetail(**_row_to_dict(row))


@app.get("/counties", tags=["meta"])
def list_counties():
    """Return a sorted list of counties that have parks."""
    with db_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT county, COUNT(*) as count "
            "FROM dog_parks WHERE county != '' "
            "GROUP BY county ORDER BY county"
        ).fetchall()
    return [{"county": r["county"], "count": r["count"]} for r in rows]


@app.get("/towns", tags=["meta"])
def list_towns(county: Optional[str] = None):
    """Return towns with parks, optionally filtered by county."""
    with db_conn() as conn:
        if county:
            rows = conn.execute(
                "SELECT DISTINCT town, COUNT(*) as count "
                "FROM dog_parks WHERE LOWER(county) LIKE ? AND town != '' "
                "GROUP BY town ORDER BY town",
                (f"%{county.lower()}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DISTINCT town, COUNT(*) as count "
                "FROM dog_parks WHERE town != '' "
                "GROUP BY town ORDER BY town"
            ).fetchall()
    return [{"town": r["town"], "count": r["count"]} for r in rows]


@app.get("/features", tags=["meta"])
def list_features():
    """Return all available feature tags with their park counts."""
    with db_conn() as conn:
        rows = conn.execute("SELECT features FROM dog_parks").fetchall()

    feature_counts: dict[str, int] = {}
    for row in rows:
        feats = json.loads(row["features"] or "[]")
        for f in feats:
            feature_counts[f] = feature_counts.get(f, 0) + 1

    return [
        {"feature": k, "count": v}
        for k, v in sorted(feature_counts.items(), key=lambda x: -x[1])
    ]


@app.get("/stats", tags=["meta"])
def stats():
    """Summary statistics for the database."""
    with db_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM dog_parks").fetchone()[0]
        enclosed = conn.execute(
            "SELECT COUNT(*) FROM dog_parks WHERE is_fully_enclosed = 1"
        ).fetchone()[0]
        free = conn.execute(
            "SELECT COUNT(*) FROM dog_parks WHERE is_free = 1"
        ).fetchone()[0]
        avg_rating = conn.execute(
            "SELECT AVG(rating) FROM dog_parks WHERE rating IS NOT NULL"
        ).fetchone()[0]
        avg_price = conn.execute(
            "SELECT AVG(price_per_hour) FROM dog_parks WHERE price_per_hour IS NOT NULL"
        ).fetchone()[0]
        counties = conn.execute(
            "SELECT COUNT(DISTINCT county) FROM dog_parks"
        ).fetchone()[0]

    return {
        "total_parks": total,
        "fully_enclosed": enclosed,
        "free_parks": free,
        "counties_covered": counties,
        "avg_rating": round(avg_rating, 2) if avg_rating else None,
        "avg_price_per_hour": round(avg_price, 2) if avg_price else None,
    }


# ─────────────────────────────────────────────
#  Admin — reload data
# ─────────────────────────────────────────────

@app.post("/admin/reload", tags=["admin"])
def reload_data():
    """Drop and re-seed the database from parks.json."""
    with db_conn() as conn:
        conn.execute("DELETE FROM dog_parks")
        conn.commit()
        _seed_from_json(conn)
        total = conn.execute("SELECT COUNT(*) FROM dog_parks").fetchone()[0]
    return {"reloaded": True, "total_parks": total}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
