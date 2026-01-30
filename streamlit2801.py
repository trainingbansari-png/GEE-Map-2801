import streamlit as st
import ee
import geemap  # Standard geemap
from datetime import date
import json

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
        # If using Streamlit Secrets (Recommended for deployment):
        secret_info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
        credentials = ee.ServiceAccountCredentials(secret_info['client_email'], key_data=secret_info['private_key'])

        # Initialize Earth Engine with the credentials
        ee.Initialize(credentials, project='my-project-2801-485801')
        return True
    except Exception as e:
        st.error(f"Error initializing Earth Engine: {e}")
        return False

# Initialize Earth Engine
if initialize_ee():
    st.success("✅ Earth Engine initialized successfully!")

# --------------------------------------------------
# Sidebar UI for setting parameters
# --------------------------------------------------
with st.sidebar:
    st.header("🔍 Search Parameters")

    # User input for latitude and longitude for the region of interest
    lat_ul = st.number_input("Upper-Left Latitude", value=22.5)
    lon_ul = st.number_input("Upper-Left Longitude", value=68.0)
    lat_lr = st.number_input("Lower-Right Latitude", value=21.5)
    lon_lr = st.number_input("Lower-Right Longitude", value=69.0)

    # User input for selecting satellite and date range
    satellite = st.selectbox(
        "Satellite",
        ["Sentinel-2", "Landsat-8", "Landsat-9", "MODIS"]
    )

    start_date = st.date_input("Start Date", date(2024, 1, 1))
    end_date = st.date_input("End Date", date(2024, 12, 31))

    run = st.button("🚀 Search Images")

# --------------------------------------------------
# Processing and Displaying Results
# --------------------------------------------------
if run:
    # Ensure coordinates are correct and create a region of interest (ROI)
    roi = ee.Geometry.Rectangle([lon_ul, lat_lr, lon_lr, lat_ul])

    # Dictionary of satellite image collection IDs
    collection_ids = {
        "Sentinel-2": "COPERNICUS/S2_SR_HARMONIZED",
        "Landsat-8": "LANDSAT/LC08/C02/T1_L2",
        "Landsat-9": "LANDSAT/LC09/C02/T1_L2",
        "MODIS": "MODIS/006/MOD09GA"
    }

    # Filter the image collection by ROI and date range
    collection = (
        ee.ImageCollection(collection_ids[satellite])
        .filterBounds(roi)
        .filterDate(str(start_date), str(end_date))
    )

    # Get the number of images in the collection
    count = collection.size().getInfo()
    st.write(f"🖼️ **Images Found:** {count}")

    if count == 0:
        st.warning("No images found for the selected parameters.")
    else:
        # Calculate the median of the collection and clip to the ROI
        image = collection.median().clip(roi)

        # Create map
        Map = geemap.Map(
            center=[(lat_ul + lat_lr) / 2, (lon_ul + lon_lr) / 2],
            zoom=8
        )

        # Visualization parameters for Sentinel-2 (RGB bands)
        if satellite == "Sentinel-2":
            vis_params = {
                "bands": ["B4", "B3", "B2"],
                "min": 0,
                "max": 3000,
                "gamma": 1.4
            }
        else:
            vis_params = {}

        # Add the image layer and ROI to the map
        Map.addLayer(image, vis_params, f"{satellite}")
        Map.addLayer(roi, {}, "ROI")

        # Enable drawing tools on the map
        Map.add_draw_control()

        # Render the map in Streamlit
        Map.to_streamlit(height=600)
