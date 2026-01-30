import folium
import streamlit as st
from streamlit.components.v1 import html

# Create a simple Folium map centered at a location
m = folium.Map(location=[22.5, 68.0], zoom_start=8)

# Get the HTML representation of the map
map_html = m._repr_html_()  # This generates the HTML required for embedding

# Display the map using Streamlit's HTML component
html(map_html, height=600)
