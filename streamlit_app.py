"""
streamlit_app.py
-----------------
Web UI for the Ottawa Winter 2026 satellite imagery pulled in the companion
Colab notebook (Ottawa_Winter2026_GEE.ipynb).

This app supports two modes, so it works whether or not you want to expose
your Earth Engine credentials to the deployed app:

  MODE 1 - "Static" (default, recommended for a quick deployed link)
      Just displays the PNG thumbnail exported from the Colab notebook.
      No Earth Engine credentials needed on the Streamlit server at all.
      -> Put 'ottawa_winter_2026_rgb.png' (produced by the notebook) in the
         same folder as this file before deploying.

  MODE 2 - "Live" (optional)
      Re-queries Earth Engine directly from the Streamlit app and renders an
      interactive map, using a Google service account key you provide via
      Streamlit's secrets manager. Turn this on with the sidebar toggle.

Run locally with:   streamlit run streamlit_app.py
Deploy for a public link via Streamlit Community Cloud (share.streamlit.io) -
point it at the GitHub repo containing this file + the PNG (and, for Mode 2,
your service-account secret configured in the app's "Secrets" settings).
"""

import os
import streamlit as st

# --------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------
st.set_page_config(page_title="Ottawa Winter 2026 — Satellite View", layout="wide")
st.title("Ottawa Region — Winter 2026 RGB Satellite Imagery")
st.caption(
    "Sentinel-2 true-color composite of the Ottawa region, "
    "Dec 2025 – Feb 2026, pulled via Google Earth Engine."
)

# --------------------------------------------------------------------------
# Mode toggle
# --------------------------------------------------------------------------
mode = st.sidebar.radio(
    "Display mode",
    ["Static image (from Colab export)", "Live Earth Engine query"],
    help=(
        "Static mode just shows the PNG the notebook already generated — "
        "no credentials needed. Live mode re-runs the query on Earth Engine "
        "right now, using a service account key stored in Streamlit secrets."
    ),
)

STATIC_IMAGE_PATH = "ottawa_winter_2026_rgb.png"

# --------------------------------------------------------------------------
# MODE 1 — Static image
# --------------------------------------------------------------------------
if mode == "Static image (from Colab export)":
    if os.path.exists(STATIC_IMAGE_PATH):
        st.image(
            STATIC_IMAGE_PATH,
            caption="Ottawa, Winter 2025/2026 — Sentinel-2 RGB",
            use_container_width=True,
        )
        st.success("Showing the image exported from the Colab notebook.")
    else:
        st.warning(
            f"Couldn't find '{STATIC_IMAGE_PATH}' next to this app. "
            "Run the Colab notebook's export step first, download the PNG it "
            "creates, and place it in this same project folder — then redeploy."
        )

# --------------------------------------------------------------------------
# MODE 2 — Live Earth Engine query
# --------------------------------------------------------------------------
else:
    st.info(
        "Live mode queries Earth Engine directly from this app. It needs a "
        "Google service account with Earth Engine access, added to this app's "
        "Streamlit secrets as `EE_SERVICE_ACCOUNT` (email) and "
        "`EE_PRIVATE_KEY` (the key JSON contents)."
    )

    try:
        import ee
        import geemap.foliumap as geemap  # folium-based Map, works inside Streamlit

        # --- Initialize Earth Engine using a service account (no interactive
        #     login — this is what makes "Live mode" possible on a server) ---
        service_account = st.secrets["EE_SERVICE_ACCOUNT"]
        private_key = st.secrets["EE_PRIVATE_KEY"]
        credentials = ee.ServiceAccountCredentials(service_account, key_data=private_key)
        ee.Initialize(credentials)

        # --- Same AOI + filtering logic as the Colab notebook ---
        ottawa_bbox = ee.Geometry.BBox(west=-76.05, south=45.20, east=-75.35, north=45.55)

        start_date = st.sidebar.text_input("Start date", "2025-12-01")
        end_date = st.sidebar.text_input("End date", "2026-02-28")
        max_cloud = st.sidebar.slider("Max cloud cover (%)", 0, 100, 20)

        s2 = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(ottawa_bbox)
            .filterDate(start_date, end_date)
        )
        s2_clear = s2.filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloud))

        if s2_clear.size().getInfo() > 0:
            image = s2_clear.sort("CLOUDY_PIXEL_PERCENTAGE").first().select(["B4", "B3", "B2"])
            st.caption("Using the single least-cloudy scene in range.")
        else:
            image = s2.select(["B4", "B3", "B2"]).median()
            st.caption("No scene under the cloud threshold — using a median composite instead.")

        image = image.multiply(0.0001).clip(ottawa_bbox)
        vis_params = {"min": 0.0, "max": 0.3, "gamma": 1.3}

        m = geemap.Map(center=[45.40, -75.70], zoom=10)
        m.addLayer(image, vis_params, "Ottawa Winter RGB")
        m.to_streamlit(height=600)

    except KeyError:
        st.error(
            "Missing Earth Engine credentials in Streamlit secrets. "
            "Add `EE_SERVICE_ACCOUNT` and `EE_PRIVATE_KEY` under this app's "
            "Settings > Secrets, or switch back to Static mode in the sidebar."
        )
    except Exception as e:
        st.error(f"Earth Engine query failed: {e}")

st.divider()
st.caption(
    "Source notebook: Ottawa_Winter2026_GEE.ipynb — run it in Google Colab to "
    "regenerate the image or export a fresh GeoTIFF."
)
