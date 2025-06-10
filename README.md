# 🎧 Next Spin – Your AI Crate-Digging Companion

Next Spin is an AI-powered vinyl recommender built *for collectors, by collectors*. Whether you're building your taste, chasing rare pressings, or stacking high-ROI flips — this tool helps you discover what to spin (or snag) next.

---

## ✨ Key Features

This project is composed of two main components: a powerful collection analysis dashboard and a developing AI recommendation engine.

### 1. Crate Intelligence Dashboard (`crate_ui.py`)

An interactive Streamlit dashboard that analyzes a record collection to provide actionable insights.

* **🎯 Crate Picks (Value Score):** Identifies records that are a great value, balancing high collector demand against low market price.
* **💰 Smart Buys (Investment Score):** Pinpoints records that are not only a good value but are also scarce on the market, suggesting they have high potential to increase in value.
* **👑 Collector's Essentials:** Ranks records by their pure popularity (Want vs. Have ratio) to identify the "must-have" classics in a collection.
* **💎 Deep Cuts:** Uncovers hidden gems by finding records from popular artists that are surprisingly rare or overlooked by other collectors.
* **🎛️ Interactive Controls:** Features a dynamic "Price Sensitivity" slider that lets the user control how much budget impacts the scoring algorithms.

### 2. AI Recommendation Engine (In Development)

A sophisticated backend designed to provide personalized recommendations.

* ** Taste-Aligned Gems:** Uses embedding models to find deep cuts and new artists based on the sonic profile of your collection.
* ** Missing Links:** Discovers albums that bridge the stylistic gaps between different parts of your collection.

## 🧠 How It Works: The Data Pipeline

The application works through a multi-step data pipeline that takes raw collection data and transforms it into actionable intelligence.

1.  **Data Ingestion (`sample_collection.csv`):** The process starts with a basic CSV export from a user's Discogs collection.
2.  **Data Enrichment (`enrich_collection.py`):** A Python script uses the Discogs API (via `recommender/discogs_client.py`) to enrich the basic CSV with critical market data: lowest price, want/have counts, number for sale, cover art, etc.
3.  **Intelligence Layer (`crate_ui.py`):** The Streamlit dashboard loads this `enriched_collection.csv` to calculate its suite of scores and display the interactive analysis.
4.  **AI Modeling (`embedder.py`, `recommender.py`):** Separately, embedding models are trained on collection data to power the AI-driven recommendation features.

## 📂 Project Structure

The repository is organized into distinct modules for data processing, analysis, and recommendation.
```bash
NEXTSPIN-RECOMMENDER/
│
├── data/
│   ├── enriched_collection.csv   # The final dataset used by the UI
│   └── sample_collection.csv     # Raw input data from Discogs
│
├── notebooks/
│   ├── test_embedder.ipynb       # Prototyping for embedding models
│   └── test_recommender.ipynb    # Prototyping for the recommendation engine
│
├── recommender/
│   ├── discogs_client.py         # A client for interacting with the Discogs API
│   ├── embedder.py               # Generates vector embeddings from collection data
│   └── recommender.py            # Core recommendation logic
│
├── .gitignore
├── crate_ui.py                   # The main Streamlit web application
├── enrich_collection.py          # Script to enrich the raw collection data
├── README.md                     # You are here!
└── requirements.txt              # Project dependencies
```
## 🛠️ How to Run the Dashboard

To run the Crate Intelligence dashboard locally:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/nextspin-recommender.git](https://github.com/your-username/nextspin-recommender.git)
    cd nextspin-recommender
    ```

2.  **Set up a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Ensure you have the data:**
    Make sure an `enriched_collection.csv` file exists in the `data/` directory. You can generate one by running the enrichment scripts.

4.  **Run the Streamlit app:**
    ```bash
    streamlit run crate_ui.py
    ```

## 🗺️ Roadmap & Future Features

While the core analysis tools are functional, the vision for Next Spin is much larger. Future development is focused on:

-   **"Complete the Set" Tool:** A feature to automatically find missing releases from an artist's discography or a label's catalog.
-   **"Twin Crate Digger":** A social recommendation feature to see what collectors with similar tastes own that you don’t.
-   **Live Discogs/Spotify Integration:** Moving beyond CSVs to connect directly to user accounts for real-time analysis and taste profiling based on listening history.
-   **Value Trend Tracking:** Modeling and predicting future price changes for records.

## 👥 Who It’s For

-   Intermediate collectors growing their racks
-   New vinyl heads discovering their sound
-   Resellers spotting value trends and deep flips
-   Anyone who loves data-driven crate digging and curation
