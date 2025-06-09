import pandas as pd
import requests
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

HEADERS = {
    "User-Agent": "NextSpinVinylApp/1.0",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}"
}

df = pd.read_csv("data/enriched_collection.csv")

# Add columns if missing
for col in ["Discogs_Release_ID", "Discogs_MasterID", "Discogs_Want", "Discogs_Have"]:
    if col not in df.columns:
        df[col] = pd.NA

for idx, row in df.iterrows():
    artist = row.get("Artist")
    title = row.get("Title")
    if pd.isna(artist) or pd.isna(title):
        continue

    query = f"{artist} {title}"
    print(f"🔍 Searching: {query}")
    try:
        r = requests.get(
            f"https://api.discogs.com/database/search",
            headers=HEADERS,
            params={"q": query, "type": "release", "per_page": 1, "page": 1}
        )
        if r.status_code != 200:
            print(f"❌ {query}: {r.status_code}")
            continue
        result = r.json()["results"][0]

        df.at[idx, "Discogs_Release_ID"] = result.get("id", pd.NA)
        df.at[idx, "Discogs_MasterID"] = result.get("master_id", pd.NA)
        df.at[idx, "Discogs_Want"] = result.get("community", {}).get("want", pd.NA)
        df.at[idx, "Discogs_Have"] = result.get("community", {}).get("have", pd.NA)

    except Exception as e:
        print(f"⚠️ {query} failed: {e}")

df.to_csv("data/enriched_collection.csv", index=False)
print("✅ Enrichment complete with Discogs_MasterID, Want, and Have counts.")

