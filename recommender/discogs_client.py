import os
import requests

# Optionally set this via .env or use hardcoded if preferred
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN", "YOUR_DISCOGS_TOKEN_HERE")

HEADERS = {
    "User-Agent": "NextSpinVinylApp/1.0",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}"
}

def get_release_stats(release_id):
    try:
        url = f"https://api.discogs.com/releases/{int(release_id)}"
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            print(f"❌ Failed to fetch release ID {release_id}: {res.status_code}")
            return None
        return res.json()
    except Exception as e:
        print(f"⚠️ Exception during fetch for release ID {release_id}: {e}")
        return None
