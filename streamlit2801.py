import streamlit as st
import ee
import geemap.foliumap as geemap
from google.oauth2 import service_account
from datetime import date

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="GEE Streamlit")
st.title("🌍 Streamlit + Google Earth Engine")

# 2. Session State Initialization
# This prevents the map from disappearing after you click it
if 'map_loaded' not in st.session_state:
    st.session_state.map_loaded = False

# 3. Earth Engine Initialization
def initialize_ee():
    try:
        if "GCP_SERVICE_ACCOUNT_JSON" not in st.secrets:
            st.error("Missing GCP_SERVICE_ACCOUNT_JSON in Streamlit secrets!")
            return False
            
        service_account_info = dict(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
        SCOPES = ['https://www.googleapis.com/auth/earthengine.readonly']
        
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, 
            scopes=SCOPES
        )
        
        ee.Initialize(credentials)
        return True
    except Exception as e:
        st.error(f"❌ Earth Engine init failed: {e}")
        return False

# 4. Sidebar UI
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

    run_button = st.button("🚀 Search Images")

# 5. Logic execution
if initialize_ee():
    if run_button:
        st.session_state.map_loaded = True

    if st.session_state.map_loaded:
        # Create ROI
        roi = ee.Geometry.Rectangle([lon_ul, lat_lr, lon_lr, lat_ul])

        collection_ids = {
            "Sentinel-2": "COPERNICUS/S2_SR_HARMONIZED",
            "Landsat-8": "LANDSAT/LC08/C02/T1_L2",
            "Landsat-9": "LANDSAT/LC09/C02/T1_L2",
            "MODIS": "MODIS/006/MOD09GA",
        }

        # Filter Collection
        collection = (
            ee.ImageCollection(collection_ids[satellite])
            .filterBounds(roi)
            .filterDate(str(start_date), str(end_date))
        )

        try:
            count = collection.size().getInfo()
            st.write(f"🖼️ **Images Found:** {count}")

            if count > 0:
                image = collection.median().clip(roi)
                
                # Setup Map
                m = geemap.Map(center=[(lat_ul + lat_lr) / 2, (lon_ul + lon_lr) / 2], zoom=8)
                
                if satellite == "Sentinel-2":
                    vis = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 3000, "gamma": 1.4}
              else:
        # Create a Median Composite
        image = collection.median().clip(roi)

        # 1. Force the use of the Folium backend for Streamlit
        import geemap.foliumap as gmap 
        
        # 2. Initialize the map
        Map = gmap.Map(center=[(lat_ul + lat_lr) / 2, (lon_ul + lon_lr) / 2], zoom=8)

        # 3. Add Layers
        if satellite == "Sentinel-2":
            vis_params = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 3000, "gamma": 1.4}
        else:
            vis_params = {"min": 0, "max": 3000}

        Map.addLayer(image, vis_params, f"{satellite}")
        Map.addLayer(roi, {"color": "red"}, "ROI")

        # 4. Final Render
        st.write("### 🗺️ Interactive Map")
        Map.to_streamlit(height=600)
