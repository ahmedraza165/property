import geopandas as gpd
from shapely.geometry import Point

# Load PAD-US GeoJSON or Shapefile
gdf = gpd.read_file("PADUS3_1_GDB/ProtectedAreas.shp")

# Point to check
pt = Point(-81.647850337264, 26.573644678695)

# Check if point intersects any protected area
protected = gdf[gdf.geometry.contains(pt)]
if not protected.empty:
    print("Protected area found:", protected[['GAP_STATUS', 'MANAGER']])
else:
    print("Not a protected area")
