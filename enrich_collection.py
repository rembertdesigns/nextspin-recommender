import pandas as pd
import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

# Set Discogs API headers
HEADERS = {
    "User-Agent": "NextSpinVinylApp/1.0",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}"
}

# Load the collection file
df = pd.read_csv("data/enriched_collection.csv")

# Add or ensure required columns exist
required_cols = [
    "Discogs_Release_ID", "Discogs_Title", "Discogs_Year", "Discogs_Thumb",
    "Discogs_Community_Rating", "Discogs_MasterID", "Discogs_Want", "Discogs_Have"
]
for col in required_cols:
    if col not in df.columns:
        df[col] = pd.NA

# Query Discogs API
for idx, row in df.iterrows():
    artist = str(row["Artist"]).strip()
    title = str(row["Title"]).strip()

    if not artist or not title:
        continue

    query = f"{artist} {title}"
    print(f"🔍 Searching: {query}")
    url = f"https://api.discogs.com/database/search?q={query}&type=release&per_page=1&page=1"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"⚠️ Skipping {query}, status: {response.status_code}")
        continue

try:
    result = response.json()["results"][0]
    df.at[idx, "Discogs_Release_ID"] = result.get("id")
    df.at[idx, "Discogs_Title"] = result.get("title")
    df.at[idx, "Discogs_Year"] = pd.to_numeric(result.get("year"), errors="coerce")
    df.at[idx, "Discogs_Thumb"] = result.get("thumb")
    df.at[idx, "Discogs_Community_Rating"] = result.get("community", {}).get("rating", {}).get("average")
    df.at[idx, "Discogs_MasterID"] = result.get("master_id")

    # ✅ FIX: Indent these properly
    want_val = result.get("community", {}).get("want")
    have_val = result.get("community", {}).get("have")
    df.at[idx, "Discogs_Want"] = int(want_val) if want_val is not None else pd.NA
    df.at[idx, "Discogs_Have"] = int(have_val) if have_val is not None else pd.NA

except Exception as e:
    print(f"⚠️ Error processing {query}: {e}")

