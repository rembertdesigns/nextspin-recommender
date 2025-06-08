import pandas as pd
import numpy as np
import faiss
from recommender.embedder import build_genre_embedding, build_year_embedding

class TasteRecommender:
    def __init__(self):
        self.index = None
        self.collection_df = None
        self.ids = []

    def fit(self, df):
        self.collection_df = df.copy()
        genre_matrix, _ = build_genre_embedding(df['Genre'])
        year_vector = build_year_embedding(df['Year'])
        vectors = np.hstack([genre_matrix, year_vector]).astype('float32')

        self.ids = df.index.tolist()
        self.index = faiss.IndexFlatIP(vectors.shape[1])  # cosine similarity
        faiss.normalize_L2(vectors)
        self.index.add(vectors)

    def recommend(self, taste_vector, top_k=5):
        query = taste_vector.astype('float32').reshape(1, -1)
        faiss.normalize_L2(query)
        D, I = self.index.search(query, top_k)
        return self.collection_df.iloc[I[0]].copy(), D[0]  # Returns matching records + scores