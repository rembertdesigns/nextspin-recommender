import os
from dotenv import load_dotenv
from recommender.discogs_client import search_release

# Force load .env manually
load_dotenv()

# Confirm token is loaded
token = os.getenv("DISCOGS_TOKEN")
print("🔐 Loaded Token:", token[:6] + "..." if token else "❌ Token not found!")

# Run a Discogs search
print("🔍 Searching for: Miles Davis – Kind of Blue")
result = search_release("Kind of Blue", "Miles Davis")

if result:
    print("🎧 Found:", result['title'])
    print("🎛️ Label:", result.get('label'))
    print("🎚️ Genre:", result.get('genre'))
    print("📀 Year:", result.get('year'))
else:
    print("❌ No result found.")