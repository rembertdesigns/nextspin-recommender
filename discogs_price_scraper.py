import pandas as pd
import time
import os
from dotenv import load_dotenv
from recommender.discogs_client import get_release_stats, get_master_info

# Load environment variables
load_dotenv()
DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

# Load data
df = pd.read_csv("data/enriched_collection.csv")

# Ensure columns exist and are float-compatible
for col in ["Discogs_Lowest_Price", "Discogs_Num_For_Sale", "Discogs_Rating_Avg_Refreshed", "Discogs_Want", "Discogs_Have"]:
    if col not in df.columns:
        df[col] = pd.NA
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Loop through rows
for idx, row in df.iterrows():
    release_id = row.get("Discogs_Release_ID")
    if pd.isna(release_id) or release_id == "":
        continue

    print(f"🔍 Fetching price info for release ID: {release_id}")
    stats = get_release_stats(release_id)

    if not stats:
        print(f"⚠️ No release stats found. Trying master ID fallback...")
        master_id = row.get("Discogs_MasterID") or row.get("Discogs_Master_ID")
        if pd.isna(master_id):
            print("❌ No master ID available.")
            continue

        # Use master info to extract want/have from community
        master_info = get_master_info(master_id)
        if not master_info:
            print(f"❌ No master stats found for master ID {master_id}")
            continue

        community = master_info.get("community", {})
        df.at[idx, "Discogs_Want"] = community.get("want", pd.NA)
        df.at[idx, "Discogs_Have"] = community.get("have", pd.NA)
        continue  # Master has no price, so skip price update

    try:
        lowest_price = stats.get("lowest_price")
        num_for_sale = stats.get("num_for_sale")
        avg_rating = stats.get("rating", {}).get("average")
        want = stats.get("community", {}).get("want")
        have = stats.get("community", {}).get("have")

        df.at[idx, "Discogs_Lowest_Price"] = float(lowest_price) if lowest_price is not None else pd.NA
        df.at[idx, "Discogs_Num_For_Sale"] = int(num_for_sale) if num_for_sale is not None else pd.NA
        df.at[idx, "Discogs_Rating_Avg_Refreshed"] = float(avg_rating) if avg_rating is not None else pd.NA
        df.at[idx, "Discogs_Want"] = int(want) if want is not None else pd.NA
        df.at[idx, "Discogs_Have"] = int(have) if have is not None else pd.NA

    except Exception as e:
        print(f"⚠️ Row {idx} failed: {e}")

    time.sleep(1)

# Save enriched file
df.to_csv("data/enriched_collection.csv", index=False)
print("✅ Enriched CSV saved with price, want, and have info.")