import pandas as pd
import time
from recommender.discogs_client import (
    search_release,
    get_release_details,
    get_release_stats,
    get_master_info
)

# Load your collection CSV
df = pd.read_csv("data/sample_collection.csv")

# Add enrichment columns
df["Discogs_Genre"] = ""
df["Discogs_Style"] = ""
df["Discogs_Label"] = ""
df["Discogs_Year"] = ""
df["Discogs_CommunityRating"] = ""
df["Discogs_CommunityVotes"] = ""
df["Discogs_Have"] = ""
df["Discogs_Want"] = ""
df["Discogs_Tracklist"] = ""
df["Discogs_MasterGenres"] = ""
df["Discogs_MasterStyles"] = ""

# Loop through and enrich
for idx, row in df.iterrows():
    print(f"🔍 Searching: {row['Artist']} – {row['Title']}")
    result = search_release(row["Title"], row["Artist"])

    if result:
        df.at[idx, "Discogs_Genre"] = ", ".join(result.get("genre", []))
        df.at[idx, "Discogs_Style"] = ", ".join(result.get("style", []))
        df.at[idx, "Discogs_Label"] = ", ".join(result.get("label", []))
        df.at[idx, "Discogs_Year"] = result.get("year", "")

        release_id = result.get("id")
        master_id = result.get("master_id")

        # Get full release details
        details = get_release_details(release_id)
        if details:
            tracklist = [t["title"] for t in details.get("tracklist", [])]
            df.at[idx, "Discogs_Tracklist"] = " | ".join(tracklist)
            df.at[idx, "Discogs_CommunityRating"] = details.get("community", {}).get("rating", {}).get("average", "")
            df.at[idx, "Discogs_CommunityVotes"] = details.get("community", {}).get("rating", {}).get("count", "")

        # Get community stats
        stats = get_release_stats(release_id)
        if stats:
            df.at[idx, "Discogs_Have"] = stats.get("have", "")
            df.at[idx, "Discogs_Want"] = stats.get("want", "")

        # Get master info
        if master_id:
            master_info = get_master_info(master_id)
            if master_info:
                df.at[idx, "Discogs_MasterGenres"] = ", ".join(master_info.get("genres", []))
                df.at[idx, "Discogs_MasterStyles"] = ", ".join(master_info.get("styles", []))
    else:
        print(f"❌ No match for: {row['Artist']} – {row['Title']}")

    time.sleep(1)  # Respect rate limit

# Save the enriched version
df.to_csv("data/enriched_collection.csv", index=False)
print("✅ Enrichment complete. Saved to data/enriched_collection.csv")

