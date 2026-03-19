# 🐾 SafePaws UK - Secure Dog Parks Finder

A full-stack web app for finding secure, enclosed dog parks across the UK. Built with **FastAPI** and **MongoDB Atlas** on the backend and **Vue 3** on the frontend, deployed on **Vercel**.

Live site: [dogpark-api.vercel.app](https://dogpark-api.vercel.app)

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3, Vite, Pinia, Vue Router, PrimeVue, Leaflet |
| Backend | FastAPI (Python) |
| Database | MongoDB Atlas (free tier) |
| Hosting | Vercel |
| Icons | icons8 |
| Maps | OpenStreetMap via Leaflet |
| Data | Google Places API |

---

## Project Structure

```
dogpark-api/
├── api.py                  <- FastAPI backend
├── requirements.txt
├── vercel.json             <- Vercel deployment config
├── fix_parks.py            <- Data cleaning script
├── fix_counties.py         <- County normalisation script
├── scraper/
│   └── scraper.py          <- Google Places scraper
├── data/
│   └── parks.json          <- Park data (source of truth)
└── frontend/
    ├── src/
    │   ├── components/     <- AppIcon, FeatureIcon, ParkCard, ParkMap, Sidebar, TopBar
    │   ├── views/          <- ExploreView, FavouritesView, ParkView
    │   ├── stores/         <- Pinia store (parks.js)
    │   ├── composables/    <- useFeatures.js
    │   └── router/         <- Vue Router
    └── dist/               <- Built frontend (committed for Vercel)
```

---

## Local Development

### Prerequisites
- Python 3.9+
- Node.js 18+
- MongoDB Atlas account (free tier)

### 1. Clone and install backend dependencies
```bash
git clone https://github.com/adraf/dogpark-api.git
cd dogpark-api
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up environment
Create a `.env` file in the project root:
```
MONGO_URI=your-mongodb-connection-string-here
```

### 3. Start the API
```bash
uvicorn api:app --reload --port 8000
```

### 4. Install and run the frontend
```bash
cd frontend
npm install
npm run dev
```

The frontend runs at **http://localhost:5173** and the API at **http://localhost:8000**.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/parks` | List parks (paginated, filterable) |
| GET | `/parks/{id}` | Single park detail |
| GET | `/parks/nearby` | Parks within radius of lat/lng |
| GET | `/counties` | All counties with park counts |
| GET | `/towns` | All towns with park counts |
| GET | `/features` | All feature tags with counts |
| GET | `/stats` | Database statistics |
| POST | `/admin/reload` | Re-seed MongoDB from parks.json |

### Filter Parameters (GET /parks)

| Param | Type | Description |
|-------|------|-------------|
| `q_search` | string | Full-text search (name, town, county, address) |
| `county` | string | Filter by county |
| `feature` | string (multi) | Required features, AND logic |
| `sort` | string | `rating` or `name` |
| `page` | int | Page number |
| `per_page` | int | Results per page (max 2000) |

---

## Scraping Data

Data is sourced from the **Google Places API**. To run a fresh scrape:

```bash
python scraper/scraper.py --source google --google-api-key YOUR_KEY
```

After scraping, run the cleaning scripts:
```bash
python fix_parks.py      # filter non-parks, infer features
python fix_counties.py   # normalise county names via postcodes.io
```

Then commit `data/parks.json` and reload MongoDB:
```bash
git add data/parks.json
git commit -m "Fresh park data"
git push
curl -X POST https://dogpark-api.vercel.app/admin/reload
```

Note: keep your Google API key out of the codebase and make sure `.env` is in `.gitignore`.

---

## Deployment (Vercel)

The app is deployed as a single Vercel project:
- The Python API is served as a serverless function
- The built Vue frontend (`frontend/dist/`) is served as static files
- Routes are configured in `vercel.json`

To redeploy, push to `main` and Vercel will auto-deploy.

Required environment variable in Vercel:
```
MONGO_URI = your-mongodb-connection-string-here
```

---

## Features

- Map view with Leaflet, custom markers and gold highlighting for favourited parks
- Paginated list view with photos, ratings and feature icons
- Full-text search across name, town, county and address
- Filters by feature (parking, water, agility, etc.) and county with search
- Favourites persisted in localStorage with a dedicated tab
- Fully responsive with burger menu and sidebar drawer on mobile
- Real photos from Google Places using clean CDN URLs with no API key embedded

---

## Credits

- Icons by [icons8](https://icons8.com)
- Maps (c) [OpenStreetMap](https://openstreetmap.org/copyright) contributors
- Built by [Adam Rafferty Web Design](https://www.adamraffertywebdesign.com)
