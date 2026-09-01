"""
Ottawa Winter 2025/2026 — Sentinel-2 Satellite Viewer
-------------------------------------------------------
A small Streamlit app that displays the Sentinel-2 true-color images
produced by Ottawa_Winter2026_MultiImage.ipynb, alongside their
cloud-cover statistics from ottawa_winter_2026_cloud_summary.csv.

Run with:
    streamlit run stream.py

Expected files in the same folder as this script:
    ottawa_early_december_2025.png
    ottawa_late_december_2025.png
    ottawa_mid_january_2026.png
    ottawa_early_february_2026.png
    ottawa_late_february_2026.png
    ottawa_winter_2026_cloud_summary.csv
"""

from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

APP_DIR = Path(__file__).parent
CSV_PATH = APP_DIR / "ottawa_winter_2026_cloud_summary.csv"

# Maps each "Window" label from the CSV to its image filename, following the
# naming convention used by the notebook: ottawa_<label lowercased, spaces->_>.png
def image_filename(window_label: str) -> str:
    return f"ottawa_{window_label.replace(' ', '_').lower()}.png"

st.set_page_config(
    page_title="Ottawa Winter 2025/2026 — Satellite Viewer",
    page_icon="🛰️",
    layout="wide",
)

# --------------------------------------------------------------------------
# Load data
# --------------------------------------------------------------------------

@st.cache_data
def load_summary(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["Image file"] = df["Window"].apply(image_filename)
    df["Image exists"] = df["Image file"].apply(lambda f: (APP_DIR / f).exists())
    return df

if not CSV_PATH.exists():
    st.error(
        f"Couldn't find `{CSV_PATH.name}` next to this script. "
        "Make sure it's in the same folder as stream.py."
    )
    st.stop()

summary_df = load_summary(CSV_PATH)

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------

st.title("🛰️ Ottawa Winter 2025/2026 — Sentinel-2 Satellite Viewer")
st.caption(
    "True-color (B4/B3/B2) Sentinel-2 Surface Reflectance imagery over the "
    "Ottawa region, one image per date window, sourced from Google Earth "
    "Engine (`COPERNICUS/S2_SR_HARMONIZED`)."
)

with st.expander("ℹ️ About this data", expanded=False):
    st.markdown(
        """
For each time window, the source notebook picks the **least-cloudy**
available Sentinel-2 scene. If even the least-cloudy scene exceeds the
cloud-cover threshold (50%), it falls back to a **median composite**
across all scenes in that window instead, which cancels out clouds by
taking the per-pixel median value.

- **Cloud cover (%)** is the `CLOUDY_PIXEL_PERCENTAGE` of the scene used
  (or of the cloudiest candidate, when a composite was used instead).
- **Used composite** is `True` when a median composite replaced a single
  scene because it was too cloudy.
        """
    )

st.divider()

# --------------------------------------------------------------------------
# Sidebar controls
# --------------------------------------------------------------------------

st.sidebar.header("Options")
view_mode = st.sidebar.radio("View mode", ["Grid", "Single window"], index=0)

sort_by_cloud = st.sidebar.checkbox("Sort by cloud cover", value=False)
display_df = summary_df.sort_values("Cloud cover (%)") if sort_by_cloud else summary_df

cloud_threshold = st.sidebar.slider(
    "Highlight windows cloudier than (%)", min_value=0, max_value=100, value=50
)

# --------------------------------------------------------------------------
# Cloudiness summary table
# --------------------------------------------------------------------------

st.subheader("Cloudiness summary")


def highlight_cloudy(row):
    is_cloudy = row["Cloud cover (%)"] > cloud_threshold
    return ["background-color: #ffe4e1" if is_cloudy else "" for _ in row]


st.dataframe(
    display_df.drop(columns=["Image file", "Image exists"]).style.apply(
        highlight_cloudy, axis=1
    ),
    use_container_width=True,
    hide_index=True,
)

avg_cloud = summary_df["Cloud cover (%)"].mean()
n_composite = int(summary_df["Used composite (too cloudy)"].sum())
col1, col2, col3 = st.columns(3)
col1.metric("Windows shown", len(summary_df))
col2.metric("Average cloud cover", f"{avg_cloud:.1f}%")
col3.metric("Windows using a composite", n_composite)

st.divider()

# --------------------------------------------------------------------------
# Image display
# --------------------------------------------------------------------------

def caption_for(row) -> str:
    tag = "median composite" if row["Used composite (too cloudy)"] else "single scene"
    return f"{row['Window']} — {row['Date used']} ({tag}, {row['Cloud cover (%)']:.1f}% cloud)"


if view_mode == "Grid":
    st.subheader("All windows")
    cols = st.columns(3)
    for i, (_, row) in enumerate(display_df.iterrows()):
        img_path = APP_DIR / row["Image file"]
        with cols[i % 3]:
            if row["Image exists"]:
                st.image(str(img_path), use_container_width=True)
            else:
                st.warning(f"Missing image: {row['Image file']}")
            st.caption(caption_for(row))
else:
    st.subheader("Single window")
    labels = display_df["Window"].tolist()
    choice = st.selectbox("Choose a window", labels)
    row = display_df[display_df["Window"] == choice].iloc[0]
    img_path = APP_DIR / row["Image file"]

    if row["Image exists"]:
        st.image(str(img_path), use_container_width=True)
    else:
        st.warning(f"Missing image: {row['Image file']}")

    st.caption(caption_for(row))

    m1, m2 = st.columns(2)
    m1.metric("Cloud cover", f"{row['Cloud cover (%)']:.1f}%")
    m2.metric("Used composite", "Yes" if row["Used composite (too cloudy)"] else "No")

st.divider()
st.caption(
    "Data generated by Ottawa_Winter2026_MultiImage.ipynb using the Google "
    "Earth Engine Python API. This app only reads the exported PNGs and CSV "
    "— it does not call Earth Engine itself."
)
