import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
from shapely.geometry import shape

# Import your backend functions directly (No Flask needed)
from place_search import find_places
from planner import make_grid, load_roads, plan_on_graph

st.set_page_config(page_title="FloodSafe Prototype", layout="wide")
st.title("FloodSafe: Disaster Logistics & Evacuation Engine")

# --- 1. SEARCH ---
st.sidebar.header("1. Location Search")
query = st.sidebar.text_input("Search place:", "Udaipur, Rajasthan")
if st.sidebar.button("Search"):
    try:
        results = find_places(query)
        if results:
            st.session_state['center'] = [results[0]['lat'], results[0]['lon']]
            st.sidebar.success(f"Found: {results[0]['name']}")
    except Exception as e:
        st.sidebar.error(str(e))

if 'center' not in st.session_state:
    st.session_state['center'] = [24.5854, 73.7125]

# --- 2. MAP DRAWING ---
st.write("### Step 1: Draw a boundary on the map to begin")
m = folium.Map(location=st.session_state['center'], zoom_start=13)
Draw(export=False, draw_options={'polyline':False, 'circle':False, 'marker':False, 'circlemarker':False}).add_to(m)

map_data = st_folium(m, height=450, use_container_width=True)

# --- 3. ALLOCATION ENGINE ---
if map_data and map_data.get("all_drawings"):
    st.write("---")
    st.write("### Step 2: Allocation Parameters")
    boundary_geo = map_data["all_drawings"][-1]["geometry"]
    
    col1, col2 = st.columns(2)
    resolution = col1.slider("H3 Resolution", 7, 11, 9)
    density = col2.number_input("Population Density (people/km²)", value=3000)
    
    if st.button("Run FloodSafe Allocation Engine", type="primary"):
        with st.spinner("Building H3 Grid, Fetching OSM Roads, and Calculating Routes..."):
            try:
                # 1. Generate Grid
                grid = make_grid(boundary_geo, resolution, density)
                
                # 2. Create an automatic shelter at the center of the drawn area
                center = shape(boundary_geo).centroid
                shelters = [{"id": "s1", "name": "Primary Shelter", "lat": center.y, "lon": center.x, "capacity": 50000}]
                floods = [] # No flood zones for basic test
                
                # 3. Load Graph
                graph = load_roads(shape(boundary_geo).wkt)
                
                # 4. Plan Routes
                plan = plan_on_graph(graph, grid, shelters, floods)
                
                st.success("✅ Engine execution complete!")
                
                st.write("### Evacuation Summary")
                summary = plan['summary']
                s_col1, s_col2, s_col3 = st.columns(3)
                s_col1.metric("Total Demand (People)", f"{summary['demand']:,}")
                s_col2.metric("Assigned to Shelter", f"{summary['assigned']:,}")
                s_col3.metric("Unassigned", f"{summary['unassigned']:,}")
                
            except Exception as e:
                st.error(f"Error during execution: {e}")
