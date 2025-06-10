import streamlit as st
import pandas as pd

# --- Data Loading and Preparation ---
@st.cache_data
def load_data(path):
    """Loads and prepares the data from a CSV file."""
    df = pd.read_csv(path)
    # Ensure necessary fields are numeric
    for col in ["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have", "Discogs_Num_For_Sale"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Filter for records with enough info to rank
    df["valid_field_count"] = df[["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have"]].notna().sum(axis=1)
    usable_df = df[df["valid_field_count"] >= 2].copy()
    return usable_df

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
            st.subheader(f"{row['Artist']} — {row['Title']}")
            
            # Base Stats
            st.markdown(f"""
                - 💰 **Price**: ${row['Discogs_Lowest_Price']:.2f}
                - ❤️ **Want**: {int(row['Discogs_Want']) if pd.notna(row['Discogs_Want']) else 'N/A'}
                - 📦 **Have**: {int(row['Discogs_Have']) if pd.notna(row['Discogs_Have']) else 'N/A'}
            """)

            # Display specific score for the tab
            if score_col:
                score_label = score_col.replace('_', ' ').title()
                st.markdown(f"- **{score_label}**: `{row[score_col]:.4f}`")

            # Display any extra notes (like for Deep Cuts)
            if notes:
                st.markdown(notes)
            
            # Discogs Link
            if pd.notna(row.get("Discogs_MasterID")):
                st.markdown(f"[🔗 View on Discogs](https://www.discogs.com/master/{int(row['Discogs_MasterID'])})")


# --- Main App ---
st.set_page_config(page_title="🎧 NextSpin Crate", layout="wide")
st.title("🧠 NextSpin: Crate Intelligence")
st.caption("Curated using Discogs demand, price, scarcity, and collector insights")

# --- Sidebar Controls ---
st.sidebar.header("Score Controls")
price_weight = st.sidebar.slider(
    "Price Sensitivity (Higher = more budget-focused)", 
    min_value=0.5, 
    max_value=10.0, 
    value=1.0,  # A neutral starting point
    step=0.5,
    help="Adjust how much low prices should impact the Value and SmartBuy scores."
)

# --- Core Logic & Score Computations ---
usable_df = load_data("data/enriched_collection.csv")

# 1. ENHANCED ValueScore & SmartBuyScore (with dynamic weighting)
usable_df["ValueScore"] = (
    usable_df["Discogs_Want"].fillna(1) / (usable_df["Discogs_Have"].fillna(1) + 1)
) * (1 / (usable_df["Discogs_Lowest_Price"].fillna(30) * price_weight + 1))

usable_df["SmartBuyScore"] = usable_df["ValueScore"] * (
    1 / (usable_df["Discogs_Num_For_Sale"].fillna(10) + 1)
)

# 2. NEW "Collector's Essential" Score
usable_df["EssentialScore"] = usable_df["Discogs_Want"].fillna(1) / usable_df["Discogs_Have"].fillna(1)

# 3. NEW "Deep Cut" Score
if 'Artist' in usable_df.columns:
    artist_avg_want = usable_df.groupby('Artist')['Discogs_Want'].transform('mean')
    usable_df['DeepCutScore'] = (artist_avg_want / usable_df['Discogs_Want'].fillna(1)) / usable_df['Discogs_Have'].fillna(1)
else:
    # If no 'Artist' column, disable this feature
    st.warning("Artist column not found, 'Deep Cuts' analysis disabled.")
    usable_df['DeepCutScore'] = 0


# --- Prepare Top 5 Lists ---
top_value = usable_df.sort_values(by="ValueScore", ascending=False).head(5)
top_smart = usable_df.sort_values(by="SmartBuyScore", ascending=False).head(5)
top_essentials = usable_df.sort_values(by="EssentialScore", ascending=False).head(5)
top_deep_cuts = usable_df.sort_values(by="DeepCutScore", ascending=False).head(5)

# --- Revamped UI with Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Crate Picks (Value)", 
    "💰 Smart Buys (Investment)", 
    "👑 Collector's Essentials", 
    "💎 Deep Cuts (Hidden Gems)"
])

with tab1:
    st.header("Top 5 Crate Picks (ValueScore)")
    st.caption("These records rank highly for price vs. demand — optimized for collector value.")
    for _, row in top_value.iterrows():
        display_record(row, score_col="ValueScore")

with tab2:
    st.header("Top 5 Smart Buys (Investment Potential)")
    st.caption("High demand + low supply + underpriced = records likely to rise in value.")
    for _, row in top_smart.iterrows():
        display_record(row, score_col="SmartBuyScore")

with tab3:
    st.header("Top 5 Collector's Essentials (Popularity)")
    st.caption("These are the consensus classics in the collection, ranked by demand vs. ownership, ignoring price.")
    for _, row in top_essentials.iterrows():
        display_record(row, score_col="EssentialScore")

with tab4:
    st.header("Top 5 Deep Cuts (Hidden Gems)")
    st.caption("Records from popular artists in this collection that are unusually rare or overlooked.")
    if 'Artist' in usable_df.columns:
        for _, row in top_deep_cuts.iterrows():
            avg_want_for_artist = artist_avg_want.loc[row.name]
            notes = f"- *Artist's Avg. Want: {int(avg_want_for_artist)}*"
            display_record(row, score_col="DeepCutScore", notes=notes)
    else:
        st.info("This feature requires an 'Artist' column in your data.")

st.success("✅ Analysis complete. Adjust the Price Sensitivity slider to re-calculate scores.")

