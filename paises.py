"""
Descarga Natural Earth countries y extrae Portugal + Francia.
Guarda como paises.geojson para servir de fondo en el visor.
"""
import geopandas as gpd
from pathlib import Path

OUT = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/pred-estacional/paises.geojson")

# URL del shapefile de Natural Earth (50m countries — ligero pero suficiente)
URL = "https://naturalearth.s3.amazonaws.com/50m_cultural/ne_50m_admin_0_countries.zip"

print("Descargando Natural Earth (50m countries)...")
gdf = gpd.read_file(URL)
print(f"Países cargados: {len(gdf)}")
print(f"Columnas: {list(gdf.columns)[:10]}...")

# Filtrar Portugal + Francia (y descartar territorios de ultramar)
gdf_filt = gdf[gdf["NAME"].isin(["Portugal", "France"])].copy()
print(f"Filtrados: {len(gdf_filt)}")

# Recortar al bbox de la península (lon -10 a 5, lat 35-44.5)
# para quitar Azores, Madeira, Córcega, Guayana etc.
from shapely.geometry import box
bbox_geom = box(-10, 35, 5, 44.5)
gdf_filt["geometry"] = gdf_filt.geometry.intersection(bbox_geom)
# Quitar geometrías vacías
gdf_filt = gdf_filt[~gdf_filt.geometry.is_empty].copy()

# Solo columnas necesarias
gdf_filt = gdf_filt[["NAME", "geometry"]]

# Simplificar
gdf_filt["geometry"] = gdf_filt["geometry"].simplify(tolerance=0.005, preserve_topology=True)

if OUT.exists():
    OUT.unlink()
gdf_filt.to_file(OUT, driver="GeoJSON")

print(f"\nGuardado: {OUT}")
print(f"Tamaño: {OUT.stat().st_size/1024:.1f} KB")
for _, r in gdf_filt.iterrows():
    print(f"  {r['NAME']}")