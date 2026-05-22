# --------------------
# Convierte el shapefile a GeoJSON 
# --------------------

import geopandas as gpd
from pathlib import Path
import json

SHP_PATH = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/EMBALSES/data-basins/DemarcHidrograficas_mayo2023.shp")
OUT_PATH = Path("/home/esp9221/PERM/pred-estacional/cuencas.geojson")

# Códigos de las 8 demarcaciones 
CODIGOS_VALIDOS = ["ES010", "ES014", "ES017", "ES018", "ES020", "ES030", 
                   "ES040", "ES050", "ES060", "ES063", "ES064", "ES070",
                   "ES080", "ES091", "ES100"]

# Cargar
gdf = gpd.read_file(SHP_PATH, encoding="utf-8").to_crs("EPSG:4326")
print(f"Total demarcaciones: {len(gdf)}")

# Mostrar nombres reales 
print("\nTodas las demarcaciones con nombre real:")
for _, row in gdf.iterrows():
    print(f"  {row['CodDemarc']:8s}  {row['Nombre']}")

# Filtrar solo las que usamos
gdf_filt = gdf[gdf["CodDemarc"].isin(CODIGOS_VALIDOS)].copy()
print(f"\nFiltradas: {len(gdf_filt)}")

# Quedarnos solo con las columnas que necesitamos 
gdf_filt = gdf_filt[["CodDemarc", "Nombre", "geometry"]]

# Simplificar geometria 
gdf_filt["geometry"] = gdf_filt["geometry"].simplify(tolerance=0.01, preserve_topology=True)

# Guardar
if OUT_PATH.exists():
    OUT_PATH.unlink()
gdf_filt.to_file(OUT_PATH, driver="GeoJSON")
print(f"\nGuardado: {OUT_PATH}")
print(f"Tamaño: {OUT_PATH.stat().st_size / 1024:.0f} KB")

# Check

with open(OUT_PATH) as f:
    g = json.load(f)
print(f"\nCarcateristicas en GeoJSON: {len(g['features'])}")
for feat in g["features"]:
    props = feat["properties"]
    print(f"  {props['CodDemarc']}  {props['Nombre']}")