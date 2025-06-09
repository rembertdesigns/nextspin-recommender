import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load enriched collection
df = pd.read_csv("data/enriched_collection.csv")

# Create user collection vector
collection_df = df[df["Discogs_Year"].notna()].copy()
owned_text = (
    collection_df["Discogs_Genre"].fillna("") + " " +
    collection_df["Discogs_Style"].fillna("") + " " +
    collection_df["Discogs_Label"].fillna("")
)

# Create catalog of potential additions (simulate by just reusing all records for now)
catalog_df = df.copy()
catalog_text = (
    catalog_df["Discogs_Genre"].fillna("") + " " +
    catalog_df["Discogs_Style"].fillna("") + " " +
    catalog_df["Discogs_Label"].fillna("")
)

# Fit TF-IDF on full catalog
vectorizer = TfidfVectorizer()
X_catalog = vectorizer.fit_transform(catalog_text)
X_user = vectorizer.transform(owned_text)

# Compute mean vector for user's taste
user_vector = X_user.mean(axis=0)

# Compute collection fit (cosine similarity to user's vector)
similarities = cosine_similarity(user_vector, X_catalog).flatten()
catalog_df["collection_fit"] = similarities

# Compute rarity score from want/have
catalog_df["Discogs_Have"] = pd.to_numeric(catalog_df["Discogs_Have"], errors="coerce").fillna(1)
catalog_df["Discogs_Want"] = pd.to_numeric(catalog_df["Discogs_Want"], errors="coerce").fillna(0)
catalog_df["rarity_score"] = catalog_df["Discogs_Want"] / catalog_df["Discogs_Have"]

# Final score: weighted average
catalog_df["crate_score"] = (
    0.7 * catalog_df["collection_fit"] +
    0.3 * catalog_df["rarity_score"]
)

# Sort and take top 5 unique records not in user's collection
crate = catalog_df.sort_values("crate_score", ascending=False).drop_duplicates(subset=["Artist", "Title"]).head(5)

# Display crate
print("🧳 Your Next 5 Records Crate Suggestion:\n")
print(crate[["Artist", "Title", "Discogs_Genre", "Discogs_Year", "crate_score"]])
