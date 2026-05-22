"""
Regenera solo rios.geojson con orden Strahler >= 7.
"""
import geopandas as gpd
from pathlib import Path

SHP_RIVERS = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/EMBALSES/data-basins/HydroRIVERS_v10_eu_shp/HydroRIVERS_v10_eu.shp")
OUT_RIOS   = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/pred-estacional/rios.geojson")

BBOX = (-10.0, 35.0, 5.0, 44.5)
UMBRAL = 7

print("Cargando HydroRIVERS dentro del bbox...")
gdf = gpd.read_file(SHP_RIVERS, bbox=BBOX)
print(f"Ríos en bbox: {len(gdf)}")

gdf_filt = gdf[gdf["ORD_STRA"] >= UMBRAL].copy()
gdf_filt = gdf_filt[["ORD_STRA", "geometry"]].rename(columns={"ORD_STRA": "ord"})
gdf_filt = gdf_filt.to_crs("EPSG:4326")
gdf_filt["geometry"] = gdf_filt["geometry"].simplify(tolerance=0.005, preserve_topology=True)

if OUT_RIOS.exists():
    OUT_RIOS.unlink()
gdf_filt.to_file(OUT_RIOS, driver="GeoJSON")

print(f"\nGuardado: {OUT_RIOS}")
print(f"Tamaño: {OUT_RIOS.stat().st_size/1024:.0f} KB ({len(gdf_filt)} ríos con orden >={UMBRAL})")
