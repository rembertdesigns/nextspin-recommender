import os
import streamlit as st
import pandas as pd
import requests
import time
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

# --- Configuration & API Setup ---
# Load environment variables from .env file for local development
load_dotenv()

DISCOGS_TOKEN = "" # Initialize an empty string

# This new pattern correctly handles the case where secrets.toml does not exist
try:
    # First, try to get the token from Streamlit's secrets (for deployment)
    DISCOGS_TOKEN = st.secrets["DISCOGS_TOKEN"]
except (StreamlitSecretNotFoundError, KeyError):
    # If secrets.toml doesn't exist or the key is missing,
    # fall back to the environment variable from the .env file.
    print("INFO: secrets.toml not found or key is missing. Falling back to .env file for DISCOGS_TOKEN.")
    DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

# Add a final check to ensure the token was found one way or another
if not DISCOGS_TOKEN:
    st.error("DISCOGS_TOKEN not found! Please ensure it is set in your .env file OR in Streamlit's secrets manager for deployment.")
    st.stop()

# Set the headers that will be used for all API calls
HEADERS = {
    "User-Agent": "NextSpinVinylApp/1.0",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}"
}


# --- Live Data Fetching Functions ---
@st.cache_data(ttl=3600, show_spinner="Fetching collection from Discogs...")
def fetch_user_collection(username):
    """Fetches all releases from a user's public Discogs collection (Folder 0: All)."""
    collection = []
    page = 1
    while True:
        url = f"https://api.discogs.com/users/{username}/collection/folders/0/releases?page={page}&per_page=100"
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200:
            st.error(f"Failed to fetch collection for '{username}'. Is the profile public and spelled correctly?")
            return None
        
        data = res.json()
        collection.extend(data.get('releases', []))
        
        pagination = data.get('pagination', {})
        if 'next' not in pagination.get('urls', {}) or page >= pagination.get('pages', 1):
            break
        page += 1
        time.sleep(0.5) # Be respectful of the API rate limit
        
    return collection

@st.cache_data(ttl=3600, show_spinner=False)
def enrich_collection_data(releases):
    """Takes a list of release objects and enriches them with market stats."""
    enriched_records = []
    progress_bar = st.progress(0, text="Enriching collection with market data...")

    for i, release in enumerate(releases):
        info = release.get('basic_information', {})
        
        # --- Get marketplace stats (price and availability) ---
        stats_url = f"https://api.discogs.com/marketplace/stats/{info.get('id')}"
        try:
            stats_res = requests.get(stats_url, headers=HEADERS)
            stats_data = stats_res.json() if stats_res.status_code == 200 else {}
        except requests.exceptions.RequestException:
            stats_data = {}

        record = {
            "Artist": ", ".join([artist['name'] for artist in info.get('artists', [])]),
            "Title": info.get('title'),
            "Discogs_Year": info.get('year'),
            "Discogs_MasterGenres": ", ".join(info.get('genres', [])) if info.get('genres') else None,
            "Discogs_Lowest_Price": stats_data.get('lowest_price', {}).get('value'),
            "Discogs_Num_For_Sale": stats_data.get('num_for_sale'),
            "Discogs_Want": release.get('community', {}).get('want'),
            "Discogs_Have": release.get('community', {}).get('have'),
            "Discogs_MasterID": info.get('master_id'),
            "Discogs_Thumb": info.get('thumb')
        }
        enriched_records.append(record)
        progress_bar.progress((i + 1) / len(releases), text=f"Enriching: {record['Artist']} - {record['Title']}")
        time.sleep(0.5) # Respect API rate limit

    progress_bar.empty()
    return pd.DataFrame(enriched_records)

def run_full_pipeline(username):
    """Orchestrates the fetching and enriching process for a live user."""
    releases = fetch_user_collection(username)
    if releases:
        df = enrich_collection_data(releases)
        # Basic data cleaning after enrichment
        for col in ["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have", "Discogs_Num_For_Sale", "Discogs_Year"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    return pd.DataFrame()


# --- Default Data Loading ---
@st.cache_data
def load_default_data(path):
    """Loads and prepares the default static data from a CSV file."""
    df = pd.read_csv(path)
    for col in ["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have", "Discogs_Num_For_Sale", "Discogs_Year"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# --- UI Helper Function ---
def display_record(row, score_col=None, notes=None):
    """Renders a single record in a consistent format."""
    with st.container(border=True):
        cols = st.columns([1, 4])
        with cols[0]:
            if pd.notna(row.get("Discogs_Thumb")):
                st.image(row["Discogs_Thumb"], width=150)
            else:
                st.markdown("📀 *No Image*")
        
        with cols[1]:
            st.subheader(f"{row.get('Artist', 'N/A')} — {row.get('Title', 'N/A')}")
            
            st.markdown(f"""
                - 💰 **Price**: ${row.get('Discogs_Lowest_Price', 0):.2f}
                - ❤️ **Want**: {int(row.get('Discogs_Want', 0)) if pd.notna(row.get('Discogs_Want')) else 'N/A'}
                - 📦 **Have**: {int(row.get('Discogs_Have', 0)) if pd.notna(row.get('Discogs_Have')) else 'N/A'}
            """)

            if score_col:
                score_label = score_col.replace('_', ' ').title()
                st.markdown(f"- **{score_label}**: `{row.get(score_col, 0):.4f}`")

            if notes:
                st.markdown(notes)

            if st.button("➕ Add to Crate", key=f"add_{score_col}_{row.name}"):
                if row.name not in st.session_state.crate:
                    st.session_state.crate.append(row.name)
                    st.toast(f"Added {row.get('Title', 'N/A')} to your crate!")

            if pd.notna(row.get("Discogs_MasterID")):
                st.markdown(f"[🔗 View on Discogs](https://www.discogs.com/master/{int(row.get('Discogs_MasterID'))})")


# --- Main App ---
st.set_page_config(page_title="🎧 NextSpin Crate", layout="wide")
st.title("🧠 NextSpin: Crate Intelligence")
st.caption("Analyze your Discogs collection or browse our sample crate.")

if 'crate' not in st.session_state:
    st.session_state.crate = []

with st.form("discogs_form"):
    discogs_username = st.text_input("Enter Your Discogs Username to Analyze Your Collection")
    submitted = st.form_submit_button("⚡ Analyze!")

if submitted and discogs_username:
    app_df = run_full_pipeline(discogs_username)
else:
    app_df = load_default_data("data/enriched_collection.csv")

if app_df.empty:
    st.warning("Could not load data. Please enter a valid, public Discogs username or ensure `enriched_collection.csv` exists.")
    st.stop()


# --- Sidebar Controls & Filtering ---
st.sidebar.header("Filter & Control Panel")
search_term = st.sidebar.text_input("Search Artist or Title")

# Get min/max for sliders from the dataframe to avoid errors
max_price_val = app_df['Discogs_Lowest_Price'].fillna(1000).max()
min_year_val, max_year_val = int(app_df['Discogs_Year'].dropna().min()), int(app_df['Discogs_Year'].dropna().max())

min_price, max_price_select = st.sidebar.slider(
    "Filter by Price Range ($)", 0, int(max_price_val), (0, int(max_price_val))
)

min_year_select, max_year_select = st.sidebar.slider(
    "Filter by Year", min_year_val, max_year_val, (min_year_val, max_year_val)
)

# Genre Filter
unique_genres = sorted(list(app_df['Discogs_MasterGenres'].dropna().unique()))
selected_genres = st.sidebar.multiselect("Filter by Genre", unique_genres)

price_weight = st.sidebar.slider(
    "Price Sensitivity (Higher = more budget-focused)", 0.5, 10.0, 1.0, 0.5
)

# Apply filters
filtered_df = app_df[
    (app_df['Discogs_Lowest_Price'] >= min_price) &
    (app_df['Discogs_Lowest_Price'] <= max_price_select) &
    (app_df['Discogs_Year'] >= min_year_select) &
    (app_df['Discogs_Year'] <= max_year_select)
].copy()

if selected_genres:
    filtered_df = filtered_df[filtered_df['Discogs_MasterGenres'].isin(selected_genres)]
if search_term:
    filtered_df = filtered_df[
        filtered_df['Artist'].str.contains(search_term, case=False, na=False) | 
        filtered_df['Title'].str.contains(search_term, case=False, na=False)
    ]

# --- Virtual Crate Display in Sidebar ---
st.sidebar.header("Your Virtual Crate")
if st.session_state.crate:
    # Filter crate list to only include items that are still in the filtered_df
    valid_crate_items = [item for item in st.session_state.crate if item in filtered_df.index]
    st.session_state.crate = valid_crate_items
    
    if valid_crate_items:
        crate_df = filtered_df.loc[valid_crate_items]
        st.sidebar.dataframe(crate_df[['Artist', 'Title', 'Discogs_Lowest_Price']])
        total_price = crate_df['Discogs_Lowest_Price'].sum()
        st.sidebar.metric("Total Crate Value", f"${total_price:.2f}")
        if st.sidebar.button("Clear Crate"):
            st.session_state.crate = []
            st.rerun()
    else:
        st.sidebar.info("Your crate is empty, or items were removed by filters.")
else:
    st.sidebar.info("Your crate is empty.")


# --- Score Computations (run on the filtered dataframe) ---
if not filtered_df.empty:
    filtered_df.loc[:, "ValueScore"] = (
        filtered_df["Discogs_Want"].fillna(1) / (filtered_df["Discogs_Have"].fillna(1) + 1)
    ) * (1 / (filtered_df["Discogs_Lowest_Price"].fillna(30) * price_weight + 1))
    
    filtered_df.loc[:, "SmartBuyScore"] = filtered_df["ValueScore"] * (
        1 / (filtered_df["Discogs_Num_For_Sale"].fillna(10) + 1)
    )
    
    filtered_df.loc[:, "EssentialScore"] = filtered_df["Discogs_Want"].fillna(1) / filtered_df["Discogs_Have"].fillna(1)
    
    if 'Artist' in filtered_df.columns:
        artist_avg_want = filtered_df.groupby('Artist')['Discogs_Want'].transform('mean')
        filtered_df.loc[:, 'DeepCutScore'] = (artist_avg_want / filtered_df['Discogs_Want'].fillna(1)) / filtered_df['Discogs_Have'].fillna(1)
    else:
        filtered_df.loc[:, 'DeepCutScore'] = 0

    top_value = filtered_df.sort_values(by="ValueScore", ascending=False).head(5)
    top_smart = filtered_df.sort_values(by="SmartBuyScore", ascending=False).head(5)
    top_essentials = filtered_df.sort_values(by="EssentialScore", ascending=False).head(5)
    top_deep_cuts = filtered_df.sort_values(by="DeepCutScore", ascending=False).head(5)
else:
    st.warning("No records match the current filter settings.")
    st.stop()


# --- UI Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Crate Picks (Value)", "💰 Smart Buys (Investment)", "👑 Collector's Essentials", "💎 Deep Cuts (Hidden Gems)"
])

with tab1:
    st.header("Top 5 Crate Picks")
    for _, row in top_value.iterrows():
        display_record(row, score_col="ValueScore")

with tab2:
    st.header("Top 5 Smart Buys")
    for _, row in top_smart.iterrows():
        display_record(row, score_col="SmartBuyScore")

with tab3:
    st.header("Top 5 Collector's Essentials")
    for _, row in top_essentials.iterrows():
        display_record(row, score_col="EssentialScore")

with tab4:
    st.header("Top 5 Deep Cuts")
    if 'Artist' in filtered_df.columns and not top_deep_cuts.empty:
        for _, row in top_deep_cuts.iterrows():
            avg_want_for_artist = artist_avg_want.loc[row.name]
            notes = f"- *Artist's Avg. Want: {int(avg_want_for_artist)}*"
            display_record(row, score_col="DeepCutScore", notes=notes)

