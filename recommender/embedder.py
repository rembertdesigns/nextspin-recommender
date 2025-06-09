import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load environment variables from .env
load_dotenv()

# Authenticate Spotify API using client credentials
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-library-read user-read-email"
))


def load_collection(csv_path):
    df = pd.read_csv(csv_path)
    df['Genre'] = df['Genre'].fillna('Unknown')
    df['Year'] = df['Year'].fillna(0).astype(int)
    return df

def build_genre_embedding(genres):
    """Turns genre column into multi-hot vectors."""
    mlb = MultiLabelBinarizer()
    genre_lists = [g.split(',') for g in genres]
    genre_matrix = mlb.fit_transform(genre_lists)
    return genre_matrix, mlb.classes_

def build_year_embedding(years):
    """Normalizes years to 0–1 scale."""
    min_year = years.min()
    max_year = years.max()
    return ((years - min_year) / (max_year - min_year)).values.reshape(-1, 1)

def build_taste_profile(df):
    genre_matrix, genre_labels = build_genre_embedding(df['Genre'])
    year_vector = build_year_embedding(df['Year'])
    taste_vector = np.hstack([genre_matrix, year_vector])
    return taste_vector.mean(axis=0), genre_labels
