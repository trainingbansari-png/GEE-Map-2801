import streamlit as st
import ee
import geemap
#import geemap.foliumap as geemap
from datetime import date
import json
from ee.oauth import ServiceAccountCredentials

# --------------------------------------------------
# Page config (MUST be first Streamlit command)
# --------------------------------------------------
st.set_page_config(layout="wide")
st.title("🌍 Streamlit + Google Earth Engine")

# --------------------------------------------------
# Earth Engine Initialization
# --------------------------------------------------
def initialize_ee():
    try:
        # Load service account JSON from Streamlit secrets
        service_account_info = json.loads(
            st.secrets["GCP_SERVICE_ACCOUNT_JSON"]
        )

        credentials = ServiceAccountCredentials(
            service_account_info["client_email"],
            key_data=json.dumps(service_account_info)
        )

        ee.Initialize(
            credentials=credentials,
            project="my-project-2801-485801"
        )
        return True

    except Exception as e:
        st.error(f"❌ Earth Engine init failed: {e}")
        return False


if initialize_ee():
    st.success("✅ Earth Engine initialized successfully!")

# --------------------------------------------------
# Sidebar UI
# --------------------------------------------------
with st.sidebar:
    st.header("🔍 Search Parameters")

    lat_ul = st.number_input("Upper-Left Latitude", value=22.5)
    lon_ul = st.number_input("Upper-Left Longitude", value=68.0)
    lat_lr = st.number_input("Lower-Right Latitude", value=21.5)
    lon_lr = st.number_input("Lower-Right Longitude", value=69.0)

    satellite = st.selectbox(
        "Satellite",
        ["Sentinel-2", "Landsat-8", "Landsat-9", "MODIS"]
    )

    start_date = st.date_input("Start Date", date(2024, 1, 1))
    end_date = st.date_input("End Date", date(2024, 12, 31))

    run = st.button("🚀 Search Images")

# --------------------------------------------------
# Processing
# --------------------------------------------------
if run:
    roi = ee.Geometry.Rectangle([lon_ul, lat_lr, lon_lr, lat_ul])

    collection_ids = {
        "Sentinel-2": "COPERNICUS/S2_SR_HARMONIZED",
        "Landsat-8": "LANDSAT/LC08/C02/T1_L2",
        "Landsat-9": "LANDSAT/LC09/C02/T1_L2",
        "MODIS": "MODIS/006/MOD09GA",
    }

    collection = (
        ee.ImageCollection(collection_ids[satellite])
        .filterBounds(roi)
        .filterDate(start_date.isoformat(), end_date.isoformat())
    )

    count = collection.size().getInfo()
    st.write(f"🖼️ **Images Found:** {count}")

    if count == 0:
        st.warning("No images found for the selected parameters.")
    else:
        image = collection.median().clip(roi)

        Map = geemap.Map(
            center=[(lat_ul + lat_lr) / 2, (lon_ul + lon_lr) / 2],
            zoom=8,
        )

        if satellite == "Sentinel-2":
            vis_params = {
                "bands": ["B4", "B3", "B2"],
                "min": 0,
                "max": 3000,
                "gamma": 1.4,
            }
        else:
            vis_params = {}

        Map.addLayer(image, vis_params, satellite)
        Map.addLayer(roi, {}, "ROI")

        Map.add_draw_control()
        Map.to_streamlit(height=600)
