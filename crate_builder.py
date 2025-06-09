import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

# Load enriched collection
df = pd.read_csv("data/enriched_collection.csv")

# Prepare user collection vectors
collection_df = df[df["Discogs_Year"].notna()].copy()
owned_text = (
    collection_df["Discogs_Genre"].fillna("") + " " +
    collection_df["Discogs_Style"].fillna("") + " " +
    collection_df["Discogs_Label"].fillna("")
)

# Prepare catalog text
catalog_df = df.copy()
catalog_text = (
    catalog_df["Discogs_Genre"].fillna("") + " " +
    catalog_df["Discogs_Style"].fillna("") + " " +
    catalog_df["Discogs_Label"].fillna("")
)

# Fit TF-IDF
vectorizer = TfidfVectorizer()
X_catalog = vectorizer.fit_transform(catalog_text)
X_user = vectorizer.transform(owned_text)
user_vector = X_user.mean(axis=0)

# Collection fit (cosine similarity)
similarities = cosine_similarity(user_vector, X_catalog).flatten()
catalog_df["collection_fit"] = similarities

# Rarity score
catalog_df["Discogs_Have"] = pd.to_numeric(catalog_df["Discogs_Have"], errors="coerce").fillna(1)
catalog_df["Discogs_Want"] = pd.to_numeric(catalog_df["Discogs_Want"], errors="coerce").fillna(0)
catalog_df["rarity_score_raw"] = catalog_df["Discogs_Want"] / catalog_df["Discogs_Have"]

# Normalize rarity to simulate value
scaler = MinMaxScaler()
catalog_df["value_score"] = scaler.fit_transform(catalog_df[["rarity_score_raw"]])
catalog_df["rarity_score"] = catalog_df["rarity_score_raw"]  # still keeping raw version

# Final crate score with weights
catalog_df["crate_score"] = (
    0.5 * catalog_df["collection_fit"] +
    0.25 * catalog_df["rarity_score"] +
    0.25 * catalog_df["value_score"]
)

# Top 5 crate picks
crate = (
    catalog_df
    .sort_values("crate_score", ascending=False)
    .drop_duplicates(subset=["Artist", "Title"])
    .head(5)
)

# Show results
print("🧳 Your Next 5 Records Crate Suggestion:\n")
print(crate[["Artist", "Title", "Discogs_Genre", "Discogs_Year", "crate_score", "value_score"]])

