import pandas as pd
from recommender.discogs_client import search_release
import time

# Load your collection CSV
df = pd.read_csv("data/sample_collection.csv")

# Create new columns
df["Discogs_Genre"] = ""
df["Discogs_Style"] = ""
df["Discogs_Label"] = ""
df["Discogs_Year"] = ""

# Loop through and enrich
for idx, row in df.iterrows():
    print(f"🔍 Searching: {row['Artist']} – {row['Title']}")
    result = search_release(row["Title"], row["Artist"])
    if result:
        df.at[idx, "Discogs_Genre"] = ", ".join(result.get("genre", []))
        df.at[idx, "Discogs_Style"] = ", ".join(result.get("style", []))
        df.at[idx, "Discogs_Label"] = ", ".join(result.get("label", []))
        df.at[idx, "Discogs_Year"] = result.get("year", "")
    else:
        print(f"❌ No match for: {row['Artist']} – {row['Title']}")
    time.sleep(1)  # Be kind to the API

# Save the enriched version
df.to_csv("data/enriched_collection.csv", index=False)
print("✅ Enrichment complete. Saved to data/enriched_collection.csv")
