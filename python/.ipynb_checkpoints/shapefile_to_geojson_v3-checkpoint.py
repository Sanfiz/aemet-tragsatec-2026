"""
Convierte el shapefile a GeoJSON ligero, solo con las 8 cuencas
que SÍ están en los datos. Mantiene encoding correcto.
"""
import geopandas as gpd
from pathlib import Path

SHP_PATH = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/EMBALSES/data-basins/DemarcHidrograficas_mayo2023.shp")
OUT_PATH = Path("/home/esp9921/PERM/pred-estacional/cuencas.geojson")

# Solo las 8 cuencas con datos
CODIGOS = ["ES010", "ES018", "ES020", "ES030", "ES040", "ES050", "ES070", "ES080"]

gdf = gpd.read_file(SHP_PATH, encoding="utf-8").to_crs("EPSG:4326")
print(f"Total demarcaciones: {len(gdf)}")

gdf_filt = gdf[gdf["CodDemarc"].isin(CODIGOS)].copy()
print(f"Filtradas (8): {len(gdf_filt)}")

# Solo columnas necesarias
gdf_filt = gdf_filt[["CodDemarc", "Nombre", "geometry"]]

# Simplificar geometría
gdf_filt["geometry"] = gdf_filt["geometry"].simplify(tolerance=0.01, preserve_topology=True)

if OUT_PATH.exists():
    OUT_PATH.unlink()
gdf_filt.to_file(OUT_PATH, driver="GeoJSON")

print(f"\nGuardado: {OUT_PATH}")
print(f"Tamaño: {OUT_PATH.stat().st_size / 1024:.0f} KB")

import json
with open(OUT_PATH) as f:
    g = json.load(f)
print(f"\nFeatures finales: {len(g['features'])}")
for feat in g["features"]:
    print(f"  {feat['properties']['CodDemarc']}  {feat['properties']['Nombre']}")
