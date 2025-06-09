import pandas as pd

# Load collection
df = pd.read_csv("data/enriched_collection.csv")

# Ensure numeric types
for col in ["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# --- Keep rows with at least 2 of the 3 fields ---
valid = df[["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have"]].copy()
valid["non_na_count"] = valid.notna().sum(axis=1)
qualified = df[valid["non_na_count"] >= 2].copy()

if qualified.empty:
    print("⚠️ No records have at least 2 of: price, want, or have.")
    fallback_df = df.sort_values(by="Discogs_Want", ascending=False).head(5)
    print("\n🔁 Fallback: Top 5 Most Wanted Records:\n")
    print(fallback_df[["Artist", "Title", "Discogs_Want", "Discogs_MasterID", "Discogs_Year"]])
else:
    # Compute ValueScore with null protection
    qualified["ValueScore"] = (
        qualified["Discogs_Want"].fillna(1) / (qualified["Discogs_Have"].fillna(1) + 1)
    ) * (1 / (qualified["Discogs_Lowest_Price"].fillna(30) + 1))

    top_crate = qualified.sort_values(by="ValueScore", ascending=False).head(5)

    total_cost = top_crate["Discogs_Lowest_Price"].sum(skipna=True)
    avg_price = top_crate["Discogs_Lowest_Price"].mean(skipna=True)

    print("\n🧠 Next 5 Records to Consider (Fallback Value-Aware Scoring):\n")
    print(top_crate[[
        "Artist", "Title", "Discogs_Label", "Discogs_Lowest_Price",
        "Discogs_Want", "Discogs_Have", "ValueScore"
    ]])
    print(f"\n💰 Total Estimated Cost (where price available): ${total_cost:.2f}")
    print(f"📊 Average Price per Record: ${avg_price:.2f}")




