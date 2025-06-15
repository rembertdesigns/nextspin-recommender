import os
import streamlit as st
import pandas as pd
import requests
import time
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv
from streamlit.errors import StreamlitSecretNotFoundError

# --- Configuration & API Setup ---
load_dotenv()

DISCOGS_TOKEN = ""

try:
    DISCOGS_TOKEN = st.secrets["DISCOGS_TOKEN"]
except (StreamlitSecretNotFoundError, KeyError):
    print("INFO: secrets.toml not found or key is missing. Falling back to .env file for DISCOGS_TOKEN.")
    DISCOGS_TOKEN = os.getenv("DISCOGS_TOKEN")

if not DISCOGS_TOKEN:
    st.error("DISCOGS_TOKEN not found! Please ensure it is set in your .env file OR in Streamlit's secrets manager for deployment.")
    st.stop()

HEADERS = {
    "User-Agent": "NextSpinVinylApp/1.0",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}"
}

# --- Enhanced Styling ---
def apply_custom_css():
    st.markdown("""
    <style>
    /* Main app styling */
    .main {
        padding-top: 1rem;
    }
    
    /* Custom card styling */
    .record-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        color: white;
    }
    
    .record-card-light {
        background: white;
        border: 2px solid #f0f0f0;
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Score badges */
    .score-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        background: #ff6b6b;
        color: white;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0.2rem;
    }
    
    .score-badge-green {
        background: #51cf66;
    }
    
    .score-badge-blue {
        background: #339af0;
    }
    
    .score-badge-purple {
        background: #845ec2;
    }
    
    /* Enhanced metrics */
    .metric-container {
        background: linear-gradient(45deg, #ff9a9e 0%, #fecfef 100%);
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    /* Sidebar styling */
    .sidebar-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #f0f0f0;
        border-radius: 10px 10px 0 0;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    
    /* Loading animations */
    .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100px;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .record-card, .record-card-light {
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- Data Fetching Functions (same as original) ---
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
        time.sleep(0.5)
        
    return collection

@st.cache_data(ttl=3600, show_spinner=False)
def enrich_collection_data(releases):
    """Takes a list of release objects and enriches them with market stats."""
    enriched_records = []
    progress_bar = st.progress(0, text="Enriching collection with market data...")

    for i, release in enumerate(releases):
        info = release.get('basic_information', {})
        
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
        time.sleep(0.5)

    progress_bar.empty()
    return pd.DataFrame(enriched_records)

def run_full_pipeline(username):
    """Orchestrates the fetching and enriching process for a live user."""
    releases = fetch_user_collection(username)
    if releases:
        df = enrich_collection_data(releases)
        for col in ["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have", "Discogs_Num_For_Sale", "Discogs_Year"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    return pd.DataFrame()

@st.cache_data
def load_default_data(path):
    """Loads and prepares the default static data from a CSV file."""
    df = pd.read_csv(path)
    for col in ["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have", "Discogs_Num_For_Sale", "Discogs_Year"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# --- Enhanced Analytics Functions ---
def create_collection_overview(df):
    """Creates overview charts for the collection."""
    if df.empty:
        return None, None, None
    
    # Price distribution
    fig_price = px.histogram(
        df, x="Discogs_Lowest_Price", 
        title="Price Distribution",
        color_discrete_sequence=['#667eea']
    )
    fig_price.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#333')
    )
    
    # Genre distribution (top 10)
    genre_counts = df['Discogs_MasterGenres'].value_counts().head(10)
    fig_genre = px.bar(
        x=genre_counts.values, 
        y=genre_counts.index,
        orientation='h',
        title="Top 10 Genres",
        color_discrete_sequence=['#764ba2']
    )
    fig_genre.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#333')
    )
    
    # Year distribution
    year_counts = df['Discogs_Year'].value_counts().sort_index()
    fig_year = px.line(
        x=year_counts.index, 
        y=year_counts.values,
        title="Releases by Year",
        color_discrete_sequence=['#ff6b6b']
    )
    fig_year.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#333')
    )
    
    return fig_price, fig_genre, fig_year

def get_collection_stats(df):
    """Returns key collection statistics."""
    if df.empty:
        return {}
    
    return {
        "total_records": len(df),
        "total_value": df['Discogs_Lowest_Price'].sum(),
        "avg_price": df['Discogs_Lowest_Price'].mean(),
        "most_wanted": df.loc[df['Discogs_Want'].idxmax()] if not df['Discogs_Want'].isna().all() else None,
        "rarest": df.loc[df['Discogs_Have'].idxmin()] if not df['Discogs_Have'].isna().all() else None,
        "oldest": df.loc[df['Discogs_Year'].idxmin()] if not df['Discogs_Year'].isna().all() else None,
        "newest": df.loc[df['Discogs_Year'].idxmax()] if not df['Discogs_Year'].isna().all() else None
    }

# --- Enhanced UI Helper Functions ---
def display_enhanced_record(row, score_col=None, notes=None, rank=None):
    """Renders a single record with enhanced styling."""
    
    # Determine score badge color
    badge_class = "score-badge"
    if score_col:
        if "Value" in score_col:
            badge_class += " score-badge-green"
        elif "Smart" in score_col:
            badge_class += " score-badge-blue"
        elif "Essential" in score_col:
            badge_class += " score-badge-purple"
    
    with st.container():
        st.markdown('<div class="record-card-light">', unsafe_allow_html=True)
        
        cols = st.columns([1, 4, 1])
        
        with cols[0]:
            if pd.notna(row.get("Discogs_Thumb")):
                st.image(row["Discogs_Thumb"], width=120)
            else:
                st.markdown("📀", unsafe_allow_html=True)
        
        with cols[1]:
            # Rank badge
            if rank:
                st.markdown(f'<span class="score-badge">#{rank}</span>', unsafe_allow_html=True)
            
            st.markdown(f"**{row.get('Artist', 'N/A')}**")
            st.markdown(f"*{row.get('Title', 'N/A')}*")
            st.markdown(f"📅 {int(row.get('Discogs_Year', 0)) if pd.notna(row.get('Discogs_Year')) else 'Unknown'}")
            
            # Score display
            if score_col:
                score_label = score_col.replace('_', ' ').title()
                st.markdown(f'<span class="{badge_class}">{score_label}: {row.get(score_col, 0):.3f}</span>', unsafe_allow_html=True)
            
            # Metrics in a more compact format
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.metric("💰 Price", f"${row.get('Discogs_Lowest_Price', 0):.2f}")
            with metric_cols[1]:
                st.metric("❤️ Want", f"{int(row.get('Discogs_Want', 0)) if pd.notna(row.get('Discogs_Want')) else 'N/A'}")
            with metric_cols[2]:
                st.metric("📦 Have", f"{int(row.get('Discogs_Have', 0)) if pd.notna(row.get('Discogs_Have')) else 'N/A'}")
            
            if notes:
                st.markdown(f"💡 {notes}")
        
        with cols[2]:
            st.markdown("") # Spacer
            if st.button("➕ Add", key=f"add_{score_col}_{row.name}", use_container_width=True):
                if row.name not in st.session_state.crate:
                    st.session_state.crate.append(row.name)
                    st.success(f"Added to crate! 🎉")
            
            if pd.notna(row.get("Discogs_MasterID")):
                st.markdown(f"[🔗 Discogs](https://www.discogs.com/master/{int(row.get('Discogs_MasterID'))})")
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_crate_summary():
    """Enhanced crate display with analytics."""
    if not st.session_state.crate:
        st.sidebar.info("🎧 Your crate is empty. Start adding some records!")
        return
    
    # Get valid crate items
    if 'filtered_df' in st.session_state:
        valid_crate_items = [item for item in st.session_state.crate if item in st.session_state.filtered_df.index]
        st.session_state.crate = valid_crate_items
        
        if valid_crate_items:
            crate_df = st.session_state.filtered_df.loc[valid_crate_items]
            
            # Crate analytics
            total_price = crate_df['Discogs_Lowest_Price'].sum()
            avg_price = crate_df['Discogs_Lowest_Price'].mean()
            total_want = crate_df['Discogs_Want'].sum()
            
            # Display metrics
            st.sidebar.markdown('<div class="metric-container">', unsafe_allow_html=True)
            st.sidebar.metric("🎵 Records", len(crate_df))
            st.sidebar.metric("💰 Total Value", f"${total_price:.2f}")
            st.sidebar.metric("📊 Avg Price", f"${avg_price:.2f}")
            st.sidebar.metric("❤️ Total Want", f"{int(total_want)}")
            st.sidebar.markdown('</div>', unsafe_allow_html=True)
            
            # Expandable crate details
            with st.sidebar.expander("📋 Crate Details"):
                st.dataframe(
                    crate_df[['Artist', 'Title', 'Discogs_Lowest_Price']],
                    use_container_width=True
                )
            
            # Crate actions
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.crate = []
                    st.rerun()
            with col2:
                if st.button("💾 Export", use_container_width=True):
                    csv = crate_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name="my_crate.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

# --- Main App ---
st.set_page_config(
    page_title="🎧 NextSpin Crate", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo',
        'Report a bug': "https://github.com/your-repo/issues",
        'About': "NextSpin Crate Intelligence - Discover your next favorite record!"
    }
)

# Apply custom styling
apply_custom_css()

# Initialize session state
if 'crate' not in st.session_state:
    st.session_state.crate = []

# Enhanced header
st.markdown("""
<div style="text-align: center; padding: 2rem 0;">
    <h1 style="color: #667eea; font-size: 3rem; margin-bottom: 0;">🎧 NextSpin</h1>
    <h3 style="color: #764ba2; margin-top: 0;">Crate Intelligence</h3>
    <p style="color: #666; font-size: 1.2rem;">Discover your next favorite record with AI-powered recommendations</p>
</div>
""", unsafe_allow_html=True)

# Enhanced input section
with st.container():
    st.markdown("### 🎯 Get Started")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        with st.form("discogs_form"):
            discogs_username = st.text_input(
                "Enter Your Discogs Username",
                placeholder="e.g., vinylcollector123",
                help="Make sure your profile is public!"
            )
            submitted = st.form_submit_button("⚡ Analyze My Collection", use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Or")
        use_sample = st.button("🎲 Use Sample Data", use_container_width=True)

# Data loading
if submitted and discogs_username:
    with st.spinner(f"Analyzing {discogs_username}'s collection..."):
        app_df = run_full_pipeline(discogs_username)
        st.session_state.username = discogs_username
elif use_sample:
    app_df = load_default_data("data/enriched_collection.csv")
    st.session_state.username = "Sample Collection"
else:
    app_df = load_default_data("data/enriched_collection.csv")
    st.session_state.username = "Sample Collection"

if app_df.empty:
    st.error("Could not load data. Please check your username or ensure the sample data exists.")
    st.stop()

# Store in session state for crate functionality
st.session_state.app_df = app_df

# --- Enhanced Sidebar ---
with st.sidebar:
    st.markdown('<div class="sidebar-header"><h2>🎛️ Control Panel</h2></div>', unsafe_allow_html=True)
    
    # Collection overview
    st.markdown("### 📈 Collection Overview")
    stats = get_collection_stats(app_df)
    
    if stats:
        metric_cols = st.columns(2)
        with metric_cols[0]:
            st.metric("📀 Records", stats["total_records"])
            st.metric("💰 Total Value", f"${stats['total_value']:.0f}")
        with metric_cols[1]:
            st.metric("📊 Avg Price", f"${stats['avg_price']:.2f}")
            st.metric("📅 Years", f"{int(stats['oldest']['Discogs_Year']) if stats['oldest'] is not None else 'N/A'}-{int(stats['newest']['Discogs_Year']) if stats['newest'] is not None else 'N/A'}")
    
    st.markdown("---")
    
    # Filters
    st.markdown("### 🔍 Filters")
    search_term = st.text_input("🔎 Search", placeholder="Artist or title...")
    
    # Dynamic ranges
    max_price_val = app_df['Discogs_Lowest_Price'].fillna(1000).max()
    min_year_val, max_year_val = int(app_df['Discogs_Year'].dropna().min()), int(app_df['Discogs_Year'].dropna().max())
    
    min_price, max_price_select = st.slider(
        "💰 Price Range ($)", 0, int(max_price_val), (0, int(max_price_val))
    )
    
    min_year_select, max_year_select = st.slider(
        "📅 Year Range", min_year_val, max_year_val, (min_year_val, max_year_val)
    )
    
    # Genre filter with search
    unique_genres = sorted(list(app_df['Discogs_MasterGenres'].dropna().unique()))
    selected_genres = st.multiselect("🎵 Genres", unique_genres)
    
    # Algorithm settings
    st.markdown("### ⚙️ Algorithm Settings")
    price_weight = st.slider(
        "💸 Price Sensitivity", 0.5, 10.0, 1.0, 0.5,
        help="Higher values favor cheaper records"
    )
    
    st.markdown("---")
    
    # Crate display
    st.markdown("### 🧺 Your Crate")

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

st.session_state.filtered_df = filtered_df

# Display crate in sidebar
display_crate_summary()

# --- Analytics Dashboard ---
st.markdown("### 📊 Collection Analytics")

if not filtered_df.empty:
    # Create charts
    fig_price, fig_genre, fig_year = create_collection_overview(filtered_df)
    
    chart_cols = st.columns(3)
    with chart_cols[0]:
        if fig_price:
            st.plotly_chart(fig_price, use_container_width=True)
    with chart_cols[1]:
        if fig_genre:
            st.plotly_chart(fig_genre, use_container_width=True)
    with chart_cols[2]:
        if fig_year:
            st.plotly_chart(fig_year, use_container_width=True)

# --- Score Computations ---
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

# --- Enhanced Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Best Value", "💰 Smart Buys", "👑 Essentials", "💎 Deep Cuts", "📊 Data Explorer"
])

with tab1:
    st.markdown("### 🎯 Best Value Picks")
    st.markdown("*Records with the best want-to-have ratio considering price*")
    for i, (_, row) in enumerate(top_value.iterrows(), 1):
        display_enhanced_record(row, score_col="ValueScore", rank=i)

with tab2:
    st.markdown("### 💰 Smart Investment Buys")
    st.markdown("*Rare finds with high demand and limited supply*")
    for i, (_, row) in enumerate(top_smart.iterrows(), 1):
        display_enhanced_record(row, score_col="SmartBuyScore", rank=i)

with tab3:
    st.markdown("### 👑 Collector's Essentials")
    st.markdown("*Must-have records every collector wants*")
    for i, (_, row) in enumerate(top_essentials.iterrows(), 1):
        display_enhanced_record(row, score_col="EssentialScore", rank=i)

with tab4:
    st.markdown("### 💎 Hidden Gems")
    st.markdown("*Underrated releases from popular artists*")
    if 'Artist' in filtered_df.columns and not top_deep_cuts.empty:
        for i, (_, row) in enumerate(top_deep_cuts.iterrows(), 1):
            avg_want_for_artist = artist_avg_want.loc[row.name]
            notes = f"Artist's average want: {int(avg_want_for_artist)}"
            display_enhanced_record(row, score_col="DeepCutScore", notes=notes, rank=i)

with tab5:
    st.markdown("### 📊 Data Explorer")
    st.markdown("*Dive deep into your collection data*")
    
    # Data table with sorting and filtering
    st.dataframe(
        filtered_df[['Artist', 'Title', 'Discogs_Year', 'Discogs_MasterGenres', 
                    'Discogs_Lowest_Price', 'Discogs_Want', 'Discogs_Have',
                    'ValueScore', 'SmartBuyScore', 'EssentialScore']].round(3),
        use_container_width=True
    )
    
    # Export functionality
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Full Dataset",
        data=csv,
        file_name=f"{st.session_state.get('username', 'collection')}_analysis.csv",
        mime="text/csv"
    )

# --- Footer ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🎧 Made with ❤️ for vinyl enthusiasts | Data powered by Discogs API</p>
    <p><small>Showing {count} records from {total} total</small></p>
</div>
""".format(count=len(filtered_df), total=len(app_df)), unsafe_allow_html=True)

