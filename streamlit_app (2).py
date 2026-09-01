"""
streamlit_app.py
-----------------
Dashboard for the Ottawa Winter 2026 satellite imagery pipeline
(see the companion notebook: Ottawa_Winter2026_GEE.ipynb).

MODE 1 - "Static" (default, recommended for a quick deployed link)
    Displays the PNGs + stats exported by the Colab notebook. No Earth Engine
    credentials needed on the server at all.
    Expects these files next to this script (all produced by the notebook):
        ottawa_winter_2026_rgb.png
        ottawa_winter_2026_ndsi.png
        ottawa_december_2025.png
        ottawa_february_2026.png
        ottawa_stats.json

MODE 2 - "Live" (optional)
    Re-queries Earth Engine directly from the app using a service-account key
    stored in Streamlit secrets (EE_SERVICE_ACCOUNT, EE_PRIVATE_KEY), and
    renders an interactive map with adjustable date range / cloud threshold.

Run locally with:   streamlit run streamlit_app.py
Deploy via Streamlit Community Cloud (share.streamlit.io) for a public link.
"""

import os
import json
import streamlit as st

# --------------------------------------------------------------------------
# Page setup + light custom styling
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Ottawa Winter 2026 — Satellite Dashboard",
    page_icon="🛰️",
    layout="wide",
)

st.markdown(
    """
    <style>
        .main > div {padding-top: 1.5rem;}
        .metric-card {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            padding: 1.1rem 1.3rem; border-radius: 12px; color: white;
        }
        .metric-card h3 {margin: 0; font-size: 0.85rem; opacity: 0.8; font-weight: 500;}
        .metric-card p {margin: 0.2rem 0 0 0; font-size: 1.6rem; font-weight: 700;}
        h1 {font-weight: 800;}
        .stCaption {opacity: 0.75;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛰️ Ottawa Winter 2026 — Satellite Dashboard")
st.caption(
    "Sentinel-2 imagery via Google Earth Engine · cloud-masked composite, "
    "Dec 2025 – Feb 2026 · Ottawa, Ontario"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def asset(name):
    return os.path.join(BASE_DIR, name)


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------
mode = st.sidebar.radio(
    "Data source",
    ["📦 Static (Colab export)", "🌐 Live Earth Engine"],
    help=(
        "Static just shows what the notebook already generated — no credentials "
        "needed. Live re-runs the query against Earth Engine right now."
    ),
)
st.sidebar.divider()
with st.sidebar.expander("ℹ️ How this works", expanded=False):
    st.write(
        "A Colab notebook pulls Sentinel-2 imagery for Ottawa, masks clouds "
        "pixel-by-pixel using the Scene Classification (SCL) band, builds a "
        "median composite, and computes NDSI to flag snow cover. This app "
        "displays the results."
    )

# --------------------------------------------------------------------------
# MODE 1 — Static dashboard
# --------------------------------------------------------------------------
if mode.startswith("📦"):

    stats_path = asset("ottawa_stats.json")
    stats = None
    if os.path.exists(stats_path):
        with open(stats_path) as f:
            stats = json.load(f)

    # --- Top metric row ---
    if stats:
        c1, c2, c3, c4 = st.columns(4)
        cards = [
            (c1, "Mean NDSI", f"{stats['mean_ndsi']:.2f}"),
            (c2, "Snow-covered area", f"{stats['snow_fraction_pct']:.0f}%"),
            (c3, "Scenes used", f"{stats['n_scenes_full_winter']}"),
            (c4, "Date range", f"{stats['date_range'][0][:7]} → {stats['date_range'][1][:7]}"),
        ]
        for col, label, value in cards:
            col.markdown(
                f'<div class="metric-card"><h3>{label}</h3><p>{value}</p></div>',
                unsafe_allow_html=True,
            )
        st.write("")
    else:
        st.info(
            "Run the notebook's stats step and add `ottawa_stats.json` next to "
            "this app to populate the metric cards above."
        )

    tab_rgb, tab_ndsi, tab_compare, tab_about = st.tabs(
        ["🌍 True Color", "❄️ Snow Index (NDSI)", "📆 Dec vs. Feb", "📋 About"]
    )

    with tab_rgb:
        path = asset("ottawa_winter_2026_rgb.png")
        if os.path.exists(path):
            st.image(path, use_container_width=True,
                      caption="Sentinel-2 true-color composite — Winter 2025/2026")
        else:
            st.warning(f"Missing `{os.path.basename(path)}` — export it from the notebook first.")

    with tab_ndsi:
        path = asset("ottawa_winter_2026_ndsi.png")
        if os.path.exists(path):
            st.image(path, use_container_width=True,
                      caption="NDSI — brighter blue/white = higher snow signal")
            st.caption(
                "NDSI = (Green − SWIR1) / (Green + SWIR1). Values above ~0.4 "
                "typically indicate snow or ice cover."
            )
        else:
            st.warning(f"Missing `{os.path.basename(path)}` — export it from the notebook first.")

    with tab_compare:
        col1, col2 = st.columns(2)
        dec_path, feb_path = asset("ottawa_december_2025.png"), asset("ottawa_february_2026.png")
        if os.path.exists(dec_path):
            col1.image(dec_path, use_container_width=True, caption="December 2025")
        else:
            col1.warning("Missing December composite.")
        if os.path.exists(feb_path):
            col2.image(feb_path, use_container_width=True, caption="February 2026")
        else:
            col2.warning("Missing February composite.")
        st.caption("Same cloud-masking pipeline applied to two shorter windows within the season.")

    with tab_about:
        st.markdown(
            """
            **Pipeline**
            1. Sentinel-2 Surface Reflectance imagery filtered to Ottawa, Dec 2025 – Feb 2026.
            2. Cloud/shadow masking via the SCL band, pixel-by-pixel (not scene-level).
            3. Median composite across the window.
            4. NDSI computed for snow-cover analysis.
            5. Exported as PNGs + summary stats, served here.

            **Source:** `Ottawa_Winter2026_GEE.ipynb` (Google Colab + Earth Engine).
            """
        )

# --------------------------------------------------------------------------
# MODE 2 — Live Earth Engine query
# --------------------------------------------------------------------------
else:
    st.info(
        "Live mode queries Earth Engine directly from this app using a service "
        "account. Add `EE_SERVICE_ACCOUNT` and `EE_PRIVATE_KEY` under this app's "
        "Settings → Secrets."
    )

    start_date = st.sidebar.text_input("Start date", "2025-12-01")
    end_date = st.sidebar.text_input("End date", "2026-02-28")
    show_ndsi = st.sidebar.checkbox("Overlay NDSI (snow index)", value=False)

    try:
        import ee
        import geemap.foliumap as geemap

        credentials = ee.ServiceAccountCredentials(
            st.secrets["EE_SERVICE_ACCOUNT"], key_data=st.secrets["EE_PRIVATE_KEY"]
        )
        ee.Initialize(credentials)

        ottawa_bbox = ee.Geometry.BBox(west=-76.05, south=45.20, east=-75.35, north=45.55)

        def mask_clouds(image):
            scl = image.select("SCL")
            clear = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(11))
            return image.updateMask(clear)

        coll = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(ottawa_bbox)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60))
            .map(mask_clouds)
        )
        n_scenes = coll.size().getInfo()
        composite = coll.median().multiply(0.0001)

        rgb = composite.select(["B4", "B3", "B2"]).clip(ottawa_bbox)
        st.metric("Scenes used", n_scenes)

        m = geemap.Map(center=[45.40, -75.70], zoom=10)
        m.addLayer(rgb, {"min": 0.0, "max": 0.3, "gamma": 1.3}, "RGB")

        if show_ndsi:
            ndsi = composite.normalizedDifference(["B3", "B11"]).rename("NDSI").clip(ottawa_bbox)
            m.addLayer(
                ndsi,
                {"min": -0.2, "max": 0.8, "palette": ["654321", "ffffff", "00baff"]},
                "NDSI",
            )
        m.addLayerControl()
        m.to_streamlit(height=600)

    except KeyError:
        st.error(
            "Missing Earth Engine credentials in Streamlit secrets. Add "
            "`EE_SERVICE_ACCOUNT` and `EE_PRIVATE_KEY`, or switch back to Static mode."
        )
    except Exception as e:
        st.error(f"Earth Engine query failed: {e}")

st.divider()
st.caption("Built with Google Earth Engine, Colab, and Streamlit.")
