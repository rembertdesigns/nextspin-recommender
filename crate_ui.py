import streamlit as st
import pandas as pd
import requests

# Load and prepare data
df = pd.read_csv("data/enriched_collection.csv")

# Ensure necessary fields are numeric
for col in ["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Filter for records with enough info to rank
df["valid_field_count"] = df[["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have"]].notna().sum(axis=1)
usable_df = df[df["valid_field_count"] >= 2].copy()

# Compute ValueScore and RarityScore
usable_df["ValueScore"] = (
    usable_df["Discogs_Want"].fillna(1) / (usable_df["Discogs_Have"].fillna(1) + 1)
) * (1 / (usable_df["Discogs_Lowest_Price"].fillna(30) + 1))

usable_df["RarityScore"] = (
    (1 / (usable_df["Discogs_Have"].fillna(1) + 1)) * 10
)

# Top 5
top_crate = usable_df.sort_values(by="ValueScore", ascending=False).head(5)

# Streamlit UI
st.set_page_config(page_title="🎧 NextSpin Crate", layout="wide")
st.title("🧠 NextSpin: Top 5 Crate Picks")
st.caption("Curated using Discogs demand, price, and scarcity — ranked by ValueScore™")

for _, row in top_crate.iterrows():
    with st.container():
        cols = st.columns([1, 3])

        with cols[0]:
            if pd.notna(row.get("Discogs_Thumb")):
                st.image(row["Discogs_Thumb"], width=150)
            else:
                st.markdown("📀 *No Image*")

        with cols[1]:
            st.subheader(f"{row['Artist']} — {row['Title']}")
            st.markdown(f"""
                - 💰 **Price**: ${row['Discogs_Lowest_Price']:.2f}  
                - ❤️ **Want**: {int(row['Discogs_Want']) if pd.notna(row['Discogs_Want']) else 'N/A'}  
                - 📦 **Have**: {int(row['Discogs_Have']) if pd.notna(row['Discogs_Have']) else 'N/A'}  
                - 🧠 **ValueScore**: `{row['ValueScore']:.4f}`  
                - 🔥 **RarityScore**: `{row['RarityScore']:.2f}`
            """)
            if pd.notna(row.get("Discogs_MasterID")):
                master_id = int(row["Discogs_MasterID"])
                st.markdown(f"[🔗 View on Discogs](https://www.discogs.com/master/{master_id})")
                
                with st.expander("🔍 Dig Deeper: See All Versions"):
                    url = f"https://api.discogs.com/masters/{master_id}/versions"
                    headers = {"User-Agent": "NextSpinVinylApp/1.0"}
                    res = requests.get(url, headers=headers)
                    if res.status_code == 200:
                        versions = res.json().get("versions", [])
                        for v in versions[:5]:  # limit to 5 for now
                            st.markdown(f"- `{v.get('year', 'N/A')}` | {', '.join(v.get('format', []))} | {v.get('label', ['N/A'])[0]} | 💵 ${v.get('price', {}).get('value', 'N/A')}")
                    else:
                        st.warning("Couldn't fetch version details.")

st.success("✨ All records shown based on ValueScore logic.")

# Optional Heatmap Summary
st.subheader("📊 Rarity vs. Value Heatmap")
st.caption("Hover to explore where records sit in terms of demand vs. scarcity.")
import plotly.express as px

if not usable_df.empty:
    heatmap = px.scatter(
        usable_df,
        x="Discogs_Have",
        y="Discogs_Want",
        size="ValueScore",
        color="RarityScore",
        hover_name="Title",
        title="💡 Demand vs. Scarcity Bubble Chart"
    )
    st.plotly_chart(heatmap, use_container_width=True)
