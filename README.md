# 🐾 UK Secure Dog Parks API

A FastAPI backend + web scraper that builds a comprehensive database of **secure, enclosed dog parks** across the UK, ready to power a full dog park finder application.

---

## Project Structure

```
dogpark-api/
├── api.py               ← FastAPI backend (run this)
├── requirements.txt
├── scraper/
│   └── scraper.py       ← Web scraper (run to populate data)
└── data/
    ├── parks.json        ← Scraped / seed data
    └── parks.db          ← SQLite database (auto-generated)
```

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Run the scraper to gather fresh data
```bash
# Scrape all sources
python scraper/scraper.py

# Scrape a specific source
python scraper/scraper.py --source sniffspot
python scraper/scraper.py --source dwf       # dogwalkingfields.co.uk
python scraper/scraper.py --source paddocks  # paddocksforpooches.co.uk

# With Google Places API (optional, for much better coverage)
python scraper/scraper.py --google-api-key YOUR_KEY_HERE

# Skip geocoding (faster, no coordinates)
python scraper/scraper.py --no-geocode
```

> The scraper automatically:
> - Deduplicates parks across sources
> - Geocodes postcodes via postcodes.io (free)
> - Saves to both `data/parks.json` and `data/parks.db`

### 3. Start the API server
```bash
uvicorn api:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive API documentation.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/parks` | List parks (paginated, filterable) |
| GET | `/parks/{id}` | Get a single park by ID |
| GET | `/parks/search?q=...` | Full-text search |
| GET | `/parks/nearby?lat=...&lng=...` | Parks within radius |
| GET | `/counties` | All counties with park counts |
| GET | `/towns` | All towns with park counts |
| GET | `/features` | All feature tags with counts |
| GET | `/stats` | Database statistics |
| POST | `/admin/reload` | Re-seed DB from parks.json |

### Filter Parameters (GET /parks)

| Param | Type | Description |
|-------|------|-------------|
| `county` | string | Filter by county (partial match) |
| `town` | string | Filter by town (partial match) |
| `is_free` | bool | Show only free parks |
| `is_fully_enclosed` | bool | Show only fully enclosed parks |
| `min_size_acres` | float | Minimum field size |
| `max_price_per_hour` | float | Maximum price per hour |
| `feature` | string (multi) | Required features (AND logic) |
| `sort` | string | Sort by: rating, price, size, name |
| `page` | int | Page number |
| `per_page` | int | Results per page (max 100) |

### Example Queries

```bash
# All enclosed parks in Yorkshire, sorted by rating
GET /parks?county=yorkshire&is_fully_enclosed=true&sort=rating

# Parks near London with water and parking
GET /parks?feature=water&feature=parking&county=london

# Parks nearby (within 20km of Manchester city centre)
GET /parks/nearby?lat=53.4808&lng=-2.2426&radius_km=20

# Search for "paddock" parks
GET /parks/search?q=paddock

# Parks under £10/hour
GET /parks?max_price_per_hour=10&sort=price
```

---

## Scraping Sources

| Source | Description | Notes |
|--------|-------------|-------|
| **dogwalkingfields.co.uk** | UK's largest enclosed field directory | Hire-by-hour fields |
| **sniffspot.co.uk** | Private secure dog areas | Good for urban areas |
| **paddocksforpooches.co.uk** | Dedicated paddock directory | Rural coverage |
| **Google Places API** | Maps-based search | Requires API key, best coverage |

---

## Adding New Data

You can add parks manually by appending to `data/parks.json` and calling:
```bash
curl -X POST http://localhost:8000/admin/reload
```

---

## Frontend Integration

This API is designed to power a frontend with:
- 📍 **Map view** — use `/parks/nearby` for location-based rendering
- 📋 **List view** — use `/parks` with filters and pagination
- 🔍 **Search** — use `/parks/search`
- 📌 **Favourites** — store park IDs client-side (localStorage / user DB)
- 🗺️ **Area browser** — use `/counties` → `/towns` → `/parks?town=...`

---

## Data Model

Each park contains:
- Identity: `id`, `name`, `description`
- Location: `address`, `town`, `county`, `postcode`, `latitude`, `longitude`
- Security: `is_secure`, `is_fully_enclosed`, `fence_height_m`
- Details: `size_acres`, `price_per_hour`, `is_free`, `max_dogs`
- Contact: `phone`, `website`, `email`, `opening_hours`
- Features: `features[]` (e.g. `parking`, `water`, `agility_equipment`, `lighting`)
- Quality: `rating`, `review_count`, `images[]`
- Meta: `source`, `source_url`, `last_verified`, `created_at`
