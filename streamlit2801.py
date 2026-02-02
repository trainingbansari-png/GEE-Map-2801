import streamlit as st
import ee
import geemap
from google.oauth2 import service_account
from datetime import date
import folium
from folium.plugins import Draw

# --- Page Config ---
st.set_page_config(layout="wide")
st.title("🌍 Streamlit + Google Earth Engine")

# --- Session State to keep the map alive ---
if "map_ready" not in st.session_state:
    st.session_state.map_ready = False

# --- Initialize Earth Engine ---
def initialize_ee():
    try:
        if "GCP_SERVICE_ACCOUNT_JSON" not in st.secrets:
            st.error("Missing GCP_SERVICE_ACCOUNT_JSON in Streamlit secrets!")
            return False
            
        service_account_info = dict(st.secrets["GCP_SERVICE_ACCOUNT_JSON"])
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, 
            scopes=['https://www.googleapis.com/auth/earthengine.readonly']
        )
        ee.Initialize(credentials)
        return True
    except Exception as e:
        st.error(f"❌ Earth Engine init failed: {e}")
        return False

# --- Sidebar UI ---
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

    if st.button("🚀 Search Images"):
        st.session_state.map_ready = True

# --- Main Logic ---
if initialize_ee():
    if st.session_state.map_ready:
        try:
            # Create map and draw rectangle
            center_lat = (lat_ul + lat_lr) / 2
            center_lon = (lon_ul + lon_lr) / 2
            m = folium.Map(location=[center_lat, center_lon], zoom_start=8)

            # Add drawing tools (for rectangle)
            draw = Draw(export=True)
            draw.add_to(m)

            # --- Display the map in Streamlit ---
            map_html = m._repr_html_()
            st.components.v1.html(map_html, height=600)

            # Get coordinates from the drawn shape
            if "drawn_coordinates" in st.session_state:
                drawn_coords = st.session_state.drawn_coordinates
                st.write(f"Drawn Rectangle Coordinates: {drawn_coords}")

                # --- Create ROI from drawn rectangle ---
                if drawn_coords:
                    lat_ul, lon_ul = drawn_coords[1]
                    lat_lr, lon_lr = drawn_coords[0]

                    # Map Collection IDs
                    collection_ids = {
                        "Sentinel-2": "COPERNICUS/S2_SR_HARMONIZED",
                        "Landsat-8": "LANDSAT/LC08/C02/T1_L2",
                        "Landsat-9": "LANDSAT/LC09/C02/T1_L2",
                        "MODIS": "MODIS/006/MOD09GA",
                    }

                    # Filter and process image collection
                    collection = (
                        ee.ImageCollection(collection_ids[satellite])
                        .filterBounds(ee.Geometry.Rectangle([lon_ul, lat_lr, lon_lr, lat_ul]))
                        .filterDate(str(start_date), str(end_date))
                    )

                    count = collection.size().getInfo()
                    st.info(f"🖼️ Images Found: {count}")

                    if count > 0:
                        image = collection.median().clip(ee.Geometry.Rectangle([lon_ul, lat_lr, lon_lr, lat_ul]))

                        # Get map ID and tile URL
                        if satellite == "Sentinel-2":
                            vis = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 3000, "gamma": 1.4}
                        else:
                            vis = {"min": 0, "max": 3000}

                        map_id_dict = ee.Image(image).getMapId(vis)
                        tile_url = map_id_dict['tile_fetcher'].url_format

                        # Add the Earth Engine layer to the map
                        folium.TileLayer(
                            tiles=tile_url,
                            attr='Google Earth Engine',
                            name=satellite,
                            overlay=True,
                            control=True
                        ).add_to(m)

                        # Add drawn rectangle to the map
                        folium.Rectangle(
                            bounds=[[lat_lr, lon_ul], [lat_ul, lon_lr]],
                            color="red",
                            fill=False
                        ).add_to(m)

                        # Render the map as static HTML
                        map_html = m._repr_html_()
                        st.components.v1.html(map_html, height=600)
                    
                    else:
                        st.warning("No images found for these coordinates/dates.")

        except Exception as e:
            st.error(f"Processing Error: {e}")
