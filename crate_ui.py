import streamlit as st
import pandas as pd

# Load and prepare data
df = pd.read_csv("data/enriched_collection.csv")

# Clean numeric fields
for col in ["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have", "Discogs_Community_Rating"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["valid_field_count"] = df[["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have"]].notna().sum(axis=1)
usable_df = df[df["valid_field_count"] >= 2].copy()

# Compute scores
usable_df["ValueScore"] = (
    usable_df["Discogs_Want"].fillna(1) / (usable_df["Discogs_Have"].fillna(1) + 1)
) * (1 / (usable_df["Discogs_Lowest_Price"].fillna(30) + 1))

usable_df["RarityScore"] = (
    1 / (usable_df["Discogs_Have"].fillna(1) + 1)
) * (usable_df["Discogs_Want"].fillna(0) + 1)

# UI setup
st.set_page_config(page_title="🎧 NextSpin Crate", layout="wide")
st.title("🧠 NextSpin: Crate Explorer")
st.caption("Filter and rank your collection using Discogs metadata.")

# Sidebar Filters
with st.sidebar:
    st.header("🎛️ Filters")

    price_range = st.slider("💰 Price Range", 0.0, 100.0, (0.0, 60.0))
    year_range = st.slider("📅 Year Range", 1950, 2025, (1960, 2025))
    genre_filter = st.multiselect("🎵 Genre Filter", sorted(df["Discogs_Genre"].dropna().unique().tolist()))
    min_rating = st.slider("⭐ Min Rating", 0.0, 5.0, 3.5)
    
    st.divider()
    strategy = st.radio("🧪 Ranking Strategy", ["ValueScore", "RarityScore", "Discogs_Community_Rating"])

# Apply filters
filtered = usable_df[
    (usable_df["Discogs_Lowest_Price"].between(*price_range)) &
    (usable_df["Discogs_Year"].between(*year_range)) &
    (usable_df["Discogs_Community_Rating"] >= min_rating)
]

if genre_filter:
    filtered = filtered[filtered["Discogs_Genre"].isin(genre_filter)]

# Rank by strategy
ranked = filtered.sort_values(by=strategy, ascending=False).head(10)

# Results Display
for _, row in ranked.iterrows():
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            if pd.notna(row.get("Discogs_Thumb")):
                st.image(row["Discogs_Thumb"], width=140)
            else:
                st.markdown("📀 *No Image*")

        with cols[1]:
            st.subheader(f"{row['Artist']} — {row['Title']}")
            st.markdown(f"""
            - 💰 **Price**: ${row['Discogs_Lowest_Price']:.2f}
            - 📅 **Year**: {int(row['Discogs_Year']) if pd.notna(row['Discogs_Year']) else 'N/A'}
            - 🎵 **Genre**: {row['Discogs_Genre']}
            - ❤️ **Want**: {int(row['Discogs_Want']) if pd.notna(row['Discogs_Want']) else 'N/A'}
            - 📦 **Have**: {int(row['Discogs_Have']) if pd.notna(row['Discogs_Have']) else 'N/A'}
            - ⭐ **Rating**: {row['Discogs_Community_Rating']:.2f}
            - 🧠 **{strategy}**: `{row[strategy]:.4f}`
            """)
            if pd.notna(row.get("Discogs_MasterID")):
                st.markdown(f"[🔗 View on Discogs](https://www.discogs.com/master/{int(row['Discogs_MasterID'])})")

st.success("🔍 Crate filtered and ranked successfully.")
