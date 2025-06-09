import pandas as pd
import numpy as np
import faiss
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler

# Load data
df = pd.read_csv("data/enriched_collection.csv")

# Combine text fields for embedding
df["combo_text"] = (
    df["Discogs_Genre"].fillna("") + " " +
    df["Discogs_Style"].fillna("") + " " +
    df["Discogs_Label"].fillna("")
)

# TF-IDF on combo_text
vectorizer = TfidfVectorizer()
X_text = vectorizer.fit_transform(df["combo_text"])

# Normalize year column (numeric)
year_vals = df["Discogs_Year"].fillna(0).astype(float).values.reshape(-1, 1)
scaler = StandardScaler()
X_year = scaler.fit_transform(year_vals)

# Combine into a final matrix
X_full = np.hstack([X_text.toarray(), X_year])

# Build Faiss index
index = faiss.IndexFlatL2(X_full.shape[1])
index.add(np.array(X_full).astype(np.float32))

def recommend_similar(idx, top_k=5):
    query_vector = np.array([X_full[idx]]).astype(np.float32)
    distances, indices = index.search(query_vector, top_k + 1)
    recs = df.iloc[indices[0][1:]][["Artist", "Title", "Discogs_Genre", "Discogs_Year"]]
    return recs

# Example usage
if __name__ == "__main__":
    print("🎯 Recommendations based on first item in your collection:\n")
    print(recommend_similar(0))
