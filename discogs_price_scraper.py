import pandas as pd
import time
from recommender.discogs_client import get_release_stats

df = pd.read_csv("data/enriched_collection.csv")

# Ensure these columns exist
cols_to_check = [
    "Discogs_Lowest_Price", "Discogs_Num_For_Sale", "Discogs_Rating_Avg_Refreshed",
    "Discogs_Want", "Discogs_Have"
]
for col in cols_to_check:
    if col not in df.columns:
        df[col] = pd.NA
    df[col] = pd.to_numeric(df[col], errors="coerce")

for idx, row in df.iterrows():
    release_id = row.get("Discogs_Release_ID")
    if pd.isna(release_id):
        continue

    print(f"🔍 Fetching price info for release ID: {release_id}")
    stats = get_release_stats(release_id)
    if not stats:
        continue

    try:
        df.at[idx, "Discogs_Lowest_Price"] = stats.get("lowest_price", pd.NA)
        df.at[idx, "Discogs_Num_For_Sale"] = stats.get("num_for_sale", pd.NA)
        df.at[idx, "Discogs_Rating_Avg_Refreshed"] = (
            stats.get("rating", {}).get("average", pd.NA)
        )

        # ✅ Want/Have from Release endpoint (RELIABLE)
        want = stats.get("community", {}).get("want")
        have = stats.get("community", {}).get("have")

        df.at[idx, "Discogs_Want"] = int(want) if want is not None else pd.NA
        df.at[idx, "Discogs_Have"] = int(have) if have is not None else pd.NA

    except Exception as e:
        print(f"⚠️ Error updating row {idx}: {e}")

    time.sleep(1)

df.to_csv("data/enriched_collection.csv", index=False)
print("✅ Enriched CSV saved with price, want, and have info.")