import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import leafmap.foliumap as leafmap
import requests
from io import BytesIO
import zipfile
import mapclassify
import rasterio
from rasterio.features import shapes
import shapely.geometry

st.set_page_config(page_title='NPP Dashboard', layout='wide')

st.title('Net Primary Productivity Dashboard')
st.write('This dashboard can be used for visualizing Net Primary Productivity (NPP) changes over time. ' \
"Please select a county using the dropdown menu. It's boundary will be displayed over the NPP raster layer.  " \
"Use the map layer control to toggle between the 2002 and 2022 NPP raster layers. " \
'A quantitative bar chart shows the increase or descrease in NPP between 2002 and 2022 for each county.')




# Cache the geodata loading
@st.cache_data
def load_tiger_counties():
    """Load US Census TIGER/Line Shapefile for counties"""
    # TIGER/Line Shapefiles URL for counties (2023)
    tiger_url = "https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip"
    
    with st.spinner("Loading US Census TIGER county shapefiles..."):
        # Download and extract
        response = requests.get(tiger_url)
        z = zipfile.ZipFile(BytesIO(response.content))
        z.extractall("/tmp/tiger_counties")
        
        # Read shapefile
        gdf = gpd.read_file("/tmp/tiger_counties/tl_2023_us_county.shp")
        gdf['GEOID'] = gdf['GEOID'].astype(str).str.zfill(5)
        gdf = gdf.to_crs(epsg=4326)
        print(gdf.head())
    return gdf

url = r"C:\Users\bugni\Documents\GEOG6835\Week10\utah_counties_npp_change_2002_2022.csv"
@st.cache_data
def read_csv(url):
    df = pd.read_csv(url)
    df = df[['NAME', 'GEOID', 'STATEFP', '2002', '2022', 'NPP_Change']]
    df['STATEFP'] = df['STATEFP'].astype(str).str.zfill(2)
    df['GEOID'] = df['GEOID'].astype(str).str.zfill(5)
    return df

#rasters NPP 2002 and 2022
npp_2002_path = r"C:\Users\bugni\Documents\GEOG6835\Week10\utah_npp_2002.tif"
npp_2022_path = r"C:\Users\bugni\Documents\GEOG6835\Week10\utah_npp_2022.tif"




TIGER = load_tiger_counties()
npp_df = read_csv(url)

#filter both datasets to Utah counties only
TIGER = TIGER[TIGER['STATEFP'] == '49']
npp_df = npp_df[npp_df['STATEFP'] == '49']

counties = npp_df.NAME.unique()
selected_county = st.sidebar.selectbox('Select a County', counties)

county_npp = npp_df[npp_df['NAME'] == selected_county]

#Create description statistics
st.sidebar.dataframe(county_npp.describe())

## Create the map

selected_gdf = TIGER[TIGER['NAME'] == selected_county]
print(selected_gdf.head())

selected_gdf = selected_gdf.merge(county_npp, on='NAME', how='left')

st.write(f"## Visualize Net Primary Productivity (2002 vs. 2022): {selected_county} County, Utah")

m = leafmap.Map(
    layers_control=True,  
    draw_control=False,
    measure_control=False,
    fullscreen_control=False,
)
#m.add_basemap('CartoDB.DarkMatter')

# Add the 2002 NPP Layer
m.add_raster(
    npp_2002_path,
    layer_name='NPP 2002',       
    cmap="YlGn",
    zoom_to_layer=True,

)

# Add the 2022 NPP Layer
m.add_raster(
    npp_2022_path,
    layer_name='NPP 2022',       
    cmap="YlGn",
    zoom_to_layer=False,         
)

#add the selected county boundary and zoom to it
m.add_gdf(
    selected_gdf,
    layer_name=f"{selected_county} Boundary",
    style={'color': 'yellow', 'fillColor': 'transparent', 'weight': 2.5},
    zoom_to_layer=True,
)

m_split_streamlit = m.to_streamlit(1000, 600)



# Create a grouped bar chart for all Utah counties
st.write(f"## Net Primary Productivity (2002 vs. 2022) in Utah by County")

fig, ax = plt.subplots(figsize=(12, 6))

# Plot the 2002 and 2022 columns side-by-side grouped by county name
npp_df.plot(
    kind='bar', 
    ax=ax, 
    color=['#2ca02c', '#1f77b4'], # Green for 2002, Blue for 2022
    x='NAME', 
    y=['2002', '2022'], 
    xlabel="Utah Counties",
    ylabel='NPP Value'
)

ax.set_title('Net Primary Productivity Comparison by County (2002 vs 2022)')
ax.set_xticklabels(npp_df['NAME'], rotation=90, ha='right')
ax.set_ylim(0, 1.5 * npp_df[['2002', '2022']].values.max())
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Display the chart in Streamlit
st.pyplot(fig)