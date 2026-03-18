"""
UK Secure Dog Parks Web Scraper
================================
Scrapes multiple sources to build a comprehensive database of secure/enclosed
dog parks across the UK.

Sources:
  - dogwalkingfields.co.uk   (enclosed dog walking fields)
  - sniffspot.co.uk          (private secure dog areas)
  - paddocksforpooches.co.uk (paddock listings)
  - Google Places API        (optional, requires API key)
  - Local council websites   (public parks with secure areas)

Usage:
  python scraper.py                    # scrape all sources
  python scraper.py --source sniffspot # scrape single source
  python scraper.py --output data/parks.json
"""

import requests
import httpx
import asyncio
import json
import time
import re
import sqlite3
import logging
import argparse
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DogParkFinder/1.0; "
        "+https://dogparkfinder.co.uk/bot)"
    )
}


# ─────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────

@dataclass
class DogPark:
    id: str
    name: str
    description: str
    address: str
    town: str
    county: str
    postcode: str
    country: str = "UK"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_secure: bool = True
    is_fully_enclosed: bool = False
    fence_height_m: Optional[float] = None
    size_acres: Optional[float] = None
    price_per_hour: Optional[float] = None
    is_free: bool = False
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    opening_hours: Optional[str] = None
    features: list = None          # e.g. ["parking", "water", "agility", "lighting"]
    dog_size_allowed: list = None  # ["small", "medium", "large"]
    max_dogs: Optional[int] = None
    source: str = ""
    source_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: int = 0
    images: list = None
    last_verified: str = ""
    created_at: str = ""

    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.dog_size_allowed is None:
            self.dog_size_allowed = ["small", "medium", "large"]
        if self.images is None:
            self.images = []
        if not self.last_verified:
            self.last_verified = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


# ─────────────────────────────────────────────
#  Scrapers
# ─────────────────────────────────────────────

class DogWalkingFieldsScraper:
    """
    Scrapes dogwalkingfields.co.uk — the largest UK directory of
    enclosed, hire-by-the-hour dog walking fields.
    """

    BASE_URL = "https://www.dogwalkingfields.co.uk"
    SEARCH_URL = "https://www.dogwalkingfields.co.uk/search"

    # UK counties / regions to iterate over
    REGIONS = [
        "London", "Kent", "Surrey", "Sussex", "Hampshire", "Berkshire",
        "Essex", "Suffolk", "Norfolk", "Cambridgeshire", "Hertfordshire",
        "Bedfordshire", "Oxfordshire", "Buckinghamshire", "Gloucestershire",
        "Wiltshire", "Somerset", "Devon", "Cornwall", "Dorset",
        "Warwickshire", "Worcestershire", "Shropshire", "Staffordshire",
        "Derbyshire", "Nottinghamshire", "Leicestershire", "Northamptonshire",
        "Lincolnshire", "Yorkshire", "Lancashire", "Cheshire", "Merseyside",
        "Greater Manchester", "Tyne and Wear", "Durham", "Cumbria",
        "Wales", "Scotland",
    ]

    def scrape(self) -> list[DogPark]:
        parks = []
        for region in self.REGIONS:
            log.info(f"[DogWalkingFields] Scraping region: {region}")
            try:
                region_parks = self._scrape_region(region)
                parks.extend(region_parks)
                time.sleep(1.5)  # polite delay
            except Exception as e:
                log.warning(f"[DogWalkingFields] Failed for {region}: {e}")
        return parks

    def _scrape_region(self, region: str) -> list[DogPark]:
        resp = requests.get(
            self.SEARCH_URL,
            params={"location": region, "radius": "50"},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return self._parse_listing_page(soup, region)

    def _parse_listing_page(self, soup: BeautifulSoup, region: str) -> list[DogPark]:
        parks = []
        listings = soup.select(".listing-item, .search-result, article.park")
        for item in listings:
            try:
                park = self._parse_listing_item(item, region)
                if park:
                    parks.append(park)
            except Exception as e:
                log.debug(f"[DogWalkingFields] Parse error: {e}")
        return parks

    def _parse_listing_item(self, item, region: str) -> Optional[DogPark]:
        name_el = item.select_one("h2, h3, .listing-title, .park-name")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)

        address_el = item.select_one(".address, .location, .listing-address")
        address = address_el.get_text(strip=True) if address_el else ""

        postcode = _extract_postcode(address)

        price_el = item.select_one(".price, .cost, .listing-price")
        price = _parse_price(price_el.get_text() if price_el else "")

        features = self._extract_features(item)
        size = self._extract_size(item)
        link_el = item.select_one("a[href]")
        url = (self.BASE_URL + link_el["href"]) if link_el else None

        return DogPark(
            id=_make_id(name, postcode),
            name=name,
            description=_extract_description(item),
            address=address,
            town=_guess_town(address),
            county=region,
            postcode=postcode,
            is_fully_enclosed=True,
            price_per_hour=price,
            is_free=price == 0,
            features=features,
            size_acres=size,
            source="dogwalkingfields",
            source_url=url,
        )

    def _extract_features(self, item) -> list:
        text = item.get_text().lower()
        features = []
        if "parking" in text:
            features.append("parking")
        if "water" in text:
            features.append("water")
        if "agility" in text:
            features.append("agility_equipment")
        if "light" in text:
            features.append("lighting")
        if "toilet" in text or "facilities" in text:
            features.append("toilet_facilities")
        if "shelter" in text:
            features.append("shelter")
        return features

    def _extract_size(self, item) -> Optional[float]:
        text = item.get_text()
        match = re.search(r"([\d.]+)\s*acres?", text, re.IGNORECASE)
        return float(match.group(1)) if match else None


class SniffspotScraper:
    """
    Scrapes sniffspot.co.uk — private, secure dog areas for hire.
    """

    BASE_URL = "https://www.sniffspot.co.uk"
    SPOTS_URL = "https://www.sniffspot.co.uk/spots"

    def scrape(self) -> list[DogPark]:
        parks = []
        page = 1
        while True:
            log.info(f"[Sniffspot] Page {page}")
            try:
                resp = requests.get(
                    self.SPOTS_URL,
                    params={"page": page, "country": "gb"},
                    headers=HEADERS,
                    timeout=15,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                new_parks = self._parse_page(soup)
                if not new_parks:
                    break
                parks.extend(new_parks)
                page += 1
                time.sleep(2)
            except Exception as e:
                log.warning(f"[Sniffspot] Failed on page {page}: {e}")
                break
        return parks

    def _parse_page(self, soup: BeautifulSoup) -> list[DogPark]:
        parks = []
        cards = soup.select(".spot-card, .listing-card, [data-testid='spot-card']")
        for card in cards:
            try:
                park = self._parse_card(card)
                if park:
                    parks.append(park)
            except Exception as e:
                log.debug(f"[Sniffspot] Parse card error: {e}")
        return parks

    def _parse_card(self, card) -> Optional[DogPark]:
        name_el = card.select_one("h2, h3, .spot-name, .title")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)

        loc_el = card.select_one(".location, .spot-location, .address")
        address = loc_el.get_text(strip=True) if loc_el else ""

        price_el = card.select_one(".price, .spot-price")
        price = _parse_price(price_el.get_text() if price_el else "")

        rating_el = card.select_one(".rating, .stars, [data-rating]")
        rating = None
        if rating_el:
            rating = _parse_rating(rating_el)

        img_el = card.select_one("img")
        images = [img_el["src"]] if img_el and img_el.get("src") else []

        size_match = re.search(r"([\d.]+)\s*acres?", card.get_text(), re.IGNORECASE)
        size = float(size_match.group(1)) if size_match else None

        postcode = _extract_postcode(address)
        parts = address.split(",")
        town = parts[-2].strip() if len(parts) >= 2 else ""
        county = parts[-1].strip() if parts else ""

        link = card.select_one("a[href]")
        url = (self.BASE_URL + link["href"]) if link else None

        return DogPark(
            id=_make_id(name, postcode),
            name=name,
            description=_extract_description(card),
            address=address,
            town=town,
            county=county,
            postcode=postcode,
            is_fully_enclosed=True,
            price_per_hour=price,
            is_free=price == 0,
            size_acres=size,
            rating=rating,
            images=images,
            source="sniffspot",
            source_url=url,
        )


class PaddocksForPochesScraper:
    """
    Scrapes paddocksforpooches.co.uk — dedicated paddock rental directory.
    """

    BASE_URL = "https://www.paddocksforpooches.co.uk"
    LISTINGS_URL = "https://www.paddocksforpooches.co.uk/listings"

    COUNTIES = [
        "bedfordshire", "berkshire", "bristol", "buckinghamshire",
        "cambridgeshire", "cheshire", "cornwall", "cumbria", "derbyshire",
        "devon", "dorset", "durham", "east-sussex", "essex", "gloucestershire",
        "greater-london", "greater-manchester", "hampshire", "herefordshire",
        "hertfordshire", "kent", "lancashire", "leicestershire", "lincolnshire",
        "merseyside", "norfolk", "north-yorkshire", "northamptonshire",
        "northumberland", "nottinghamshire", "oxfordshire", "shropshire",
        "somerset", "south-yorkshire", "staffordshire", "suffolk", "surrey",
        "tyne-and-wear", "warwickshire", "west-midlands", "west-sussex",
        "west-yorkshire", "wiltshire", "worcestershire",
        "wales", "scotland",
    ]

    def scrape(self) -> list[DogPark]:
        parks = []
        for county in self.COUNTIES:
            log.info(f"[PaddocksForPooches] Scraping: {county}")
            try:
                resp = requests.get(
                    f"{self.LISTINGS_URL}/{county}",
                    headers=HEADERS,
                    timeout=15,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")
                county_parks = self._parse_listings(soup, county)
                parks.extend(county_parks)
                time.sleep(1.5)
            except Exception as e:
                log.warning(f"[PaddocksForPooches] Failed for {county}: {e}")
        return parks

    def _parse_listings(self, soup: BeautifulSoup, county: str) -> list[DogPark]:
        parks = []
        items = soup.select(".paddock, .listing, article")
        for item in items:
            try:
                park = self._parse_item(item, county)
                if park:
                    parks.append(park)
            except Exception as e:
                log.debug(f"[PaddocksForPooches] Parse error: {e}")
        return parks

    def _parse_item(self, item, county: str) -> Optional[DogPark]:
        name_el = item.select_one("h2, h3, .paddock-name")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)

        desc_el = item.select_one("p, .description")
        desc = desc_el.get_text(strip=True) if desc_el else ""

        address_el = item.select_one(".address, .location")
        address = address_el.get_text(strip=True) if address_el else ""

        postcode = _extract_postcode(address or desc)

        features = []
        text = item.get_text().lower()
        for feat, keyword in [
            ("parking", "parking"), ("water", "fresh water"),
            ("agility_equipment", "agility"), ("shelter", "shelter"),
            ("lighting", "flood light"), ("toilet_facilities", "toilet"),
        ]:
            if keyword in text:
                features.append(feat)

        link = item.select_one("a[href]")
        url = None
        if link:
            href = link["href"]
            url = href if href.startswith("http") else self.BASE_URL + href

        return DogPark(
            id=_make_id(name, postcode),
            name=name,
            description=desc,
            address=address,
            town=_guess_town(address),
            county=county.replace("-", " ").title(),
            postcode=postcode,
            is_fully_enclosed=True,
            features=features,
            source="paddocksforpooches",
            source_url=url,
        )


class GooglePlacesScraper:
    """
    Uses Google Places API to find dog parks & secure dog areas.
    Requires GOOGLE_PLACES_API_KEY environment variable.
    """

    PLACES_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

    UK_SEARCH_CENTRES = [
        # (city, lat, lng)
        ("London", 51.5074, -0.1278),
        ("Birmingham", 52.4862, -1.8904),
        ("Leeds", 53.8008, -1.5491),
        ("Glasgow", 55.8642, -4.2518),
        ("Sheffield", 53.3811, -1.4701),
        ("Bradford", 53.7960, -1.7594),
        ("Liverpool", 53.4084, -2.9916),
        ("Edinburgh", 55.9533, -3.1883),
        ("Manchester", 53.4808, -2.2426),
        ("Bristol", 51.4545, -2.5879),
        ("Cardiff", 51.4816, -3.1791),
        ("Belfast", 54.5973, -5.9301),
        ("Leicester", 52.6369, -1.1398),
        ("Nottingham", 52.9548, -1.1581),
        ("Newcastle", 54.9783, -1.6178),
    ]

    PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def scrape(self) -> list[DogPark]:
        parks = []
        queries = [
            "secure dog park",
            "enclosed dog park",
            "fenced dog park",
            "secure dog walking field",
            "private dog paddock",
        ]
        for city, lat, lng in self.UK_SEARCH_CENTRES:
            for query in queries:
                log.info(f"[GooglePlaces] {query} near {city}")
                try:
                    results = self._search(f"{query} near {city}", lat, lng)
                    parks.extend(results)
                    time.sleep(0.5)
                except Exception as e:
                    log.warning(f"[GooglePlaces] Failed: {e}")
        return parks

    def _search(self, query: str, lat: float, lng: float) -> list[DogPark]:
        resp = requests.get(
            self.PLACES_URL,
            params={
                "query": query,
                "location": f"{lat},{lng}",
                "radius": 50000,
                "region": "uk",
                "key": self.api_key,
            },
            timeout=15,
        )
        data = resp.json()
        parks = []
        for result in data.get("results", []):
            try:
                park = self._parse_result(result)
                parks.append(park)
            except Exception as e:
                log.debug(f"[GooglePlaces] Parse error: {e}")
        return parks

    def _get_details(self, place_id: str) -> dict:
        """Fetch full place details including photos, phone, website, opening hours."""
        resp = requests.get(
            self.DETAILS_URL,
            params={
                "place_id": place_id,
                "fields": "name,formatted_phone_number,website,opening_hours,photos,editorial_summary",
                "key": self.api_key,
            },
            timeout=15,
        )
        return resp.json().get("result", {})

    def _get_photo_url(self, photo_reference: str, max_width: int = 800) -> str:
        """Return a proxy-safe photo URL without embedding the API key."""
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photo_reference={photo_reference}&key=REDACTED"

    def _resolve_photo_url(self, photo_reference: str, max_width: int = 800) -> str:
        """Follow the redirect to get the actual CDN image URL (no key in final URL)."""
        try:
            resp = requests.get(
                self.PHOTO_URL,
                params={
                    "maxwidth": max_width,
                    "photo_reference": photo_reference,
                    "key": self.api_key,
                },
                timeout=10,
                allow_redirects=True,
            )
            # The final URL after redirect is a CDN URL with no API key
            return resp.url
        except Exception:
            return None

    def _parse_result(self, r: dict) -> DogPark:
        loc      = r.get("geometry", {}).get("location", {})
        name     = r.get("name", "")
        address  = r.get("formatted_address", "")
        postcode = _extract_postcode(address)
        place_id = r.get("place_id", "")

        # Fetch full details for phone, website, hours, photos
        details  = {}
        images   = []
        phone    = None
        website  = None
        opening  = None
        description = ""

        try:
            details = self._get_details(place_id)
            time.sleep(0.2)  # polite delay

            phone   = details.get("formatted_phone_number")
            website = details.get("website")
            hours   = details.get("opening_hours", {})
            opening = ", ".join(hours.get("weekday_text", [])) or None
            summary = details.get("editorial_summary", {})
            description = summary.get("overview", "")

            # Get up to 3 photo URLs — follow redirect to get clean CDN URL
            photos = details.get("photos", [])[:3]
            for photo in photos:
                ref = photo.get("photo_reference")
                if ref:
                    url = self._resolve_photo_url(ref)
                    if url:
                        images.append(url)

        except Exception as e:
            log.debug(f"[GooglePlaces] Details fetch failed for {name}: {e}")

        return DogPark(
            id=_make_id(name, place_id),
            name=name,
            description=description,
            address=address,
            town=_guess_town(address),
            county=_guess_county(address),
            postcode=postcode,
            latitude=loc.get("lat"),
            longitude=loc.get("lng"),
            rating=r.get("rating"),
            review_count=r.get("user_ratings_total", 0),
            phone=phone,
            website=website,
            opening_hours=opening,
            images=images,
            source="google_places",
            source_url=f"https://maps.google.com/?cid={place_id}",
        )


# ─────────────────────────────────────────────
#  Geocoding
# ─────────────────────────────────────────────

def geocode_postcodes(parks: list[DogPark]) -> list[DogPark]:
    """
    Adds lat/lng to parks that are missing coordinates
    using the free postcodes.io API.
    """
    ungeocoded = [p for p in parks if not p.latitude and p.postcode]
    if not ungeocoded:
        return parks

    log.info(f"Geocoding {len(ungeocoded)} parks via postcodes.io ...")

    # batch lookup (up to 100 at a time)
    for i in range(0, len(ungeocoded), 100):
        batch = ungeocoded[i : i + 100]
        postcodes = [p.postcode for p in batch if p.postcode]
        try:
            resp = requests.post(
                "https://api.postcodes.io/postcodes",
                json={"postcodes": postcodes},
                timeout=20,
            )
            results = resp.json().get("result", [])
            pc_map = {}
            for r in results:
                if r.get("result"):
                    pc_map[r["query"].upper()] = (
                        r["result"]["latitude"],
                        r["result"]["longitude"],
                    )
            for park in batch:
                coords = pc_map.get(park.postcode.upper().replace(" ", "") )
                if coords:
                    park.latitude, park.longitude = coords
        except Exception as e:
            log.warning(f"Geocoding batch failed: {e}")
        time.sleep(0.3)

    return parks


# ─────────────────────────────────────────────
#  Deduplication
# ─────────────────────────────────────────────

def deduplicate(parks: list[DogPark]) -> list[DogPark]:
    """Remove near-duplicate parks by name + postcode."""
    seen = set()
    unique = []
    for park in parks:
        key = (
            re.sub(r"\W+", "", park.name.lower()),
            park.postcode.replace(" ", "").upper()[:5],
        )
        if key not in seen:
            seen.add(key)
            unique.append(park)
    log.info(f"Deduplicated: {len(parks)} → {len(unique)} parks")
    return unique


# ─────────────────────────────────────────────
#  Persistence
# ─────────────────────────────────────────────

def save_to_json(parks: list[DogPark], path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = [asdict(p) for p in parks]
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    log.info(f"Saved {len(parks)} parks → {path}")


def save_to_sqlite(parks: list[DogPark], db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS dog_parks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            address TEXT,
            town TEXT,
            county TEXT,
            postcode TEXT,
            country TEXT,
            latitude REAL,
            longitude REAL,
            is_secure INTEGER,
            is_fully_enclosed INTEGER,
            fence_height_m REAL,
            size_acres REAL,
            price_per_hour REAL,
            is_free INTEGER,
            phone TEXT,
            website TEXT,
            email TEXT,
            opening_hours TEXT,
            features TEXT,
            dog_size_allowed TEXT,
            max_dogs INTEGER,
            source TEXT,
            source_url TEXT,
            rating REAL,
            review_count INTEGER,
            images TEXT,
            last_verified TEXT,
            created_at TEXT
        )
    """)
    conn.commit()

    for p in parks:
        d = asdict(p)
        d["features"] = json.dumps(d["features"])
        d["dog_size_allowed"] = json.dumps(d["dog_size_allowed"])
        d["images"] = json.dumps(d["images"])
        d["is_secure"] = int(d["is_secure"])
        d["is_fully_enclosed"] = int(d["is_fully_enclosed"])
        d["is_free"] = int(d["is_free"])
        cur.execute("""
            INSERT OR REPLACE INTO dog_parks VALUES (
                :id, :name, :description, :address, :town, :county, :postcode,
                :country, :latitude, :longitude, :is_secure, :is_fully_enclosed,
                :fence_height_m, :size_acres, :price_per_hour, :is_free,
                :phone, :website, :email, :opening_hours, :features,
                :dog_size_allowed, :max_dogs, :source, :source_url, :rating,
                :review_count, :images, :last_verified, :created_at
            )
        """, d)
    conn.commit()
    conn.close()
    log.info(f"Saved {len(parks)} parks → {db_path}")


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _make_id(name: str, postcode: str) -> str:
    clean_name = re.sub(r"\W+", "_", name.lower()).strip("_")
    clean_pc = re.sub(r"\W+", "", postcode.lower())
    return f"{clean_name}_{clean_pc}"[:80]


def _extract_postcode(text: str) -> str:
    match = re.search(
        r"\b([A-Z]{1,2}\d{1,2}[A-Z]?\s*\d[A-Z]{2})\b",
        text,
        re.IGNORECASE,
    )
    return match.group(1).upper() if match else ""


def _parse_price(text: str) -> Optional[float]:
    match = re.search(r"£([\d.]+)", text)
    return float(match.group(1)) if match else None


def _parse_rating(el) -> Optional[float]:
    text = el.get_text()
    match = re.search(r"([\d.]+)", text)
    if match:
        val = float(match.group(1))
        return val if val <= 5 else val / 2
    return None


def _extract_description(item) -> str:
    for sel in [".description", ".summary", "p"]:
        el = item.select_one(sel)
        if el:
            return el.get_text(strip=True)[:500]
    return ""


def _guess_town(address: str) -> str:
    parts = [p.strip() for p in address.split(",")]
    # postcode is usually last; town is usually second-to-last
    if len(parts) >= 2:
        candidate = parts[-2]
        if not re.search(r"[A-Z]{1,2}\d", candidate):
            return candidate
    return parts[0] if parts else ""


def _guess_county(address: str) -> str:
    parts = [p.strip() for p in address.split(",")]
    if len(parts) >= 3:
        return parts[-2]
    return ""


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="UK Secure Dog Parks Scraper")
    parser.add_argument("--source", choices=["dwf", "sniffspot", "paddocks", "google", "all"],
                        default="all")
    parser.add_argument("--output-json", default="data/parks.json")
    parser.add_argument("--output-db", default="data/parks.db")
    parser.add_argument("--google-api-key", default=None)
    parser.add_argument("--no-geocode", action="store_true")
    args = parser.parse_args()

    all_parks = []

    if args.source in ("dwf", "all"):
        log.info("=== Dog Walking Fields ===")
        parks = DogWalkingFieldsScraper().scrape()
        log.info(f"  → {len(parks)} parks")
        all_parks.extend(parks)

    if args.source in ("sniffspot", "all"):
        log.info("=== Sniffspot ===")
        parks = SniffspotScraper().scrape()
        log.info(f"  → {len(parks)} parks")
        all_parks.extend(parks)

    if args.source in ("paddocks", "all"):
        log.info("=== Paddocks for Pooches ===")
        parks = PaddocksForPochesScraper().scrape()
        log.info(f"  → {len(parks)} parks")
        all_parks.extend(parks)

    if args.source in ("google", "all") and args.google_api_key:
        log.info("=== Google Places ===")
        parks = GooglePlacesScraper(args.google_api_key).scrape()
        log.info(f"  → {len(parks)} parks")
        all_parks.extend(parks)

    log.info(f"\nTotal raw: {len(all_parks)}")
    all_parks = deduplicate(all_parks)

    if not args.no_geocode:
        all_parks = geocode_postcodes(all_parks)

    save_to_json(all_parks, args.output_json)
    save_to_sqlite(all_parks, args.output_db)
    log.info("Done!")


if __name__ == "__main__":
    main()
