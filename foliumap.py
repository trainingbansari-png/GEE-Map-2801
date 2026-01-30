import folium
import streamlit as st
from streamlit.components.v1 import html

# Create a basic Folium map centered at a location
m = folium.Map(location=[22.5, 68.0], zoom_start=8)

# Save the map as an HTML file
m.save("map.html")

# Display the map in Streamlit
with open("map.html", "r") as f:
    map_html = f.read()

html(map_html, height=600)
