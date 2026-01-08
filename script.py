import geopandas as gpd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from shapely import wkb

db_url = "postgresql+psycopg2://rcpchCensususer:password@db:5432/rcpchCensusdb"
engine = create_engine(db_url)

data_zone_code = "S01009966"  # Replace as needed

query = f"""
SELECT data_zone_code, 
       geom, 
       ST_AsEWKB(geom_3857) AS geom_3857, 
       ST_AsEWKB(geom_3857_simp_z0_4) AS geom_3857_simp_z0_4
FROM deprivation_scores_datazone
WHERE data_zone_code = '{data_zone_code}' AND year = 2011
"""
gdf = gpd.read_postgis(query, engine, geom_col="geom")

# Convert WKB hex to shapely objects
gdf["geom_3857"] = gdf["geom_3857"].apply(lambda x: wkb.loads(bytes(x)) if x else None)
gdf["geom_3857_simp_z0_4"] = gdf["geom_3857_simp_z0_4"].apply(
    lambda x: wkb.loads(bytes(x)) if x else None
)

# Create GeoDataFrames for each geometry column
gdf_geom = gdf.set_geometry("geom")
gdf_3857 = gdf.set_geometry("geom_3857")
gdf_simp = gdf.set_geometry("geom_3857_simp_z0_4")

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
gdf_geom.plot(ax=axes[0], color="blue", edgecolor="black")
axes[0].set_title("geom (WGS84)")
gdf_3857.plot(ax=axes[1], color="green", edgecolor="black")
axes[1].set_title("geom_3857 (Web Mercator)")
gdf_simp.plot(ax=axes[2], color="red", edgecolor="black")
axes[2].set_title("geom_3857_simp_z0_4 (Simplified)")
plt.tight_layout()
plt.savefig("geometry_comparison.png")
