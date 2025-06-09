import pandas as pd
import requests
import os
import time
from dotenv import load_dotenv

# Load token
load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")
HEADERS = {
    "User-Agent": "NextSpinVinylApp/1.0",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}"
}

# Load CSV
df = pd.read_csv("data/enriched_collection.csv")

# Ensure columns exist
for col in ["Master_Want", "Master_Have", "Master_Rating"]:
    if col not in df.columns:
        df[col] = pd.NA

# Get unique master IDs
master_ids = df["Discogs_MasterID"].dropna().unique()

def get_master_metadata(master_id):
    url = f"https://api.discogs.com/masters/{int(master_id)}"
    try:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print(f"⚠️ Error for master {master_id}: {resp.status_code}")
            return None
        data = resp.json()
        return {
            "want": data.get("community", {}).get("want"),
            "have": data.get("community", {}).get("have"),
            "rating": data.get("community", {}).get("rating", {}).get("average")
        }
    except Exception as e:
        print(f"❌ Exception for master {master_id}: {e}")
        return None

# Iterate and update
for mid in master_ids:
    print(f"🔍 Fetching master metadata for ID: {mid}")
    metadata = get_master_metadata(mid)
    if metadata:
        df.loc[df["Discogs_MasterID"] == mid, "Master_Want"] = metadata["want"]
        df.loc[df["Discogs_MasterID"] == mid, "Master_Have"] = metadata["have"]
        df.loc[df["Discogs_MasterID"] == mid, "Master_Rating"] = metadata["rating"]
    time.sleep(1)

# Save
df.to_csv("data/enriched_collection.csv", index=False)
print("✅ Master metadata saved to data/enriched_collection.csv")
