import folium
import streamlit as st

# Create a basic map centered at a location
m = folium.Map(location=[22.5, 68.0], zoom_start=8)

# Display map in Streamlit
st.write(m)
