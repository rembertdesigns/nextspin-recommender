import streamlit as st
import pandas as pd

# Load and prepare data
df = pd.read_csv("data/enriched_collection.csv")

# Ensure necessary fields are numeric
for col in ["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have", "Discogs_Num_For_Sale"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Filter for records with enough info to rank
df["valid_field_count"] = df[["Discogs_Lowest_Price", "Discogs_Want", "Discogs_Have"]].notna().sum(axis=1)
usable_df = df[df["valid_field_count"] >= 2].copy()

# Compute ValueScore (demand vs price vs availability)
usable_df["ValueScore"] = (
    usable_df["Discogs_Want"].fillna(1) / (usable_df["Discogs_Have"].fillna(1) + 1)
) * (1 / (usable_df["Discogs_Lowest_Price"].fillna(30) + 1))

# Compute SmartBuyScore (same as ValueScore + scarcity consideration)
usable_df["SmartBuyScore"] = (
    (usable_df["Discogs_Want"].fillna(1) / (usable_df["Discogs_Have"].fillna(1) + 1)) *
    (1 / (usable_df["Discogs_Lowest_Price"].fillna(30) + 1)) *
    (1 / (usable_df["Discogs_Num_For_Sale"].fillna(10) + 1))
)

# Top 5 Value Crate Picks
top_crate = usable_df.sort_values(by="ValueScore", ascending=False).head(5)

# Top 5 Smart Buys
smart_buys = usable_df.sort_values(by="SmartBuyScore", ascending=False).head(5)

# Streamlit UI
st.set_page_config(page_title="🎧 NextSpin Crate", layout="wide")
st.title("🧠 NextSpin: Crate Picks & Smart Buys")
st.caption("Curated using Discogs demand, price, scarcity, and collector insights")

# -----------------------
# 🎯 Crate Picks
# -----------------------
st.header("🎯 Top 5 Crate Picks (ValueScore)")
st.caption("These records rank highly for price vs. demand — optimized for collector value.")

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
            """)
            if pd.notna(row.get("Discogs_MasterID")):
                st.markdown(f"[🔗 View on Discogs](https://www.discogs.com/master/{int(row['Discogs_MasterID'])})")

st.divider()

# -----------------------
# 💰 Smart Buys
# -----------------------
st.header("💰 Smart Buys: Records Likely to Increase in Value")
st.caption("High demand + low supply + underpriced = records likely to rise in value.")

for _, row in smart_buys.iterrows():
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
                - 🧊 **For Sale**: {int(row['Discogs_Num_For_Sale']) if pd.notna(row['Discogs_Num_For_Sale']) else 'N/A'}
                - 📈 **SmartBuyScore**: `{row['SmartBuyScore']:.4f}`
            """)
            if pd.notna(row.get("Discogs_MasterID")):
                st.markdown(f"[🔗 View on Discogs](https://www.discogs.com/master/{int(row['Discogs_MasterID'])})")

st.success("✅ All insights based on live Discogs metadata.")

