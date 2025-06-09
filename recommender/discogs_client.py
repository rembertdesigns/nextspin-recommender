import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

if not DISCOGS_TOKEN:
    print("❌ ERROR: Discogs token not loaded from .env!")

HEADERS = {
    "User-Agent": "NextSpinVinylApp/1.0",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}"
}

def search_release(title, artist=None):
    query = f"{artist} {title}" if artist else title
    url = "https://api.discogs.com/database/search"
    params = {
        "q": query,
        "type": "release",
        "per_page": 1
    }
    print(f"📡 Requesting Discogs for: {query}")
    response = requests.get(url, headers=HEADERS, params=params)
    print("📦 Status:", response.status_code)
    print("📦 Raw JSON:", response.json())
    time.sleep(1)

    if response.status_code == 200:
        results = response.json().get("results", [])
        return results[0] if results else None
    return None

def get_release_details(release_id):
    url = f"https://api.discogs.com/releases/{release_id}"
    response = requests.get(url, headers=HEADERS)
    time.sleep(1)
    if response.status_code == 200:
        return response.json()
    return None

def get_release_stats(release_id):
    url = f"https://api.discogs.com/releases/{release_id}/stats"
    response = requests.get(url, headers=HEADERS)
    time.sleep(1)
    if response.status_code == 200:
        return response.json()
    return None

def get_master_info(master_id):
    url = f"https://api.discogs.com/masters/{master_id}"
    response = requests.get(url, headers=HEADERS)
    time.sleep(1)
    if response.status_code == 200:
        return response.json()
    return None
