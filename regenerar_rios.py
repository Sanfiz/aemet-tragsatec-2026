"""
Regenera rios.geojson con:
- Más ríos (orden Strahler >= 5, ~1964 ríos)
- Solo en península ibérica (recorte por contorno de España + Portugal)
"""
import geopandas as gpd
from pathlib import Path

SHP_RIVERS = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/EMBALSES/data-basins/HydroRIVERS_v10_eu_shp/HydroRIVERS_v10_eu.shp")
OUT_RIOS   = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/pred-estacional/rios.geojson")
CUENCAS    = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/pred-estacional/cuencas.geojson")
PAISES     = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/pred-estacional/paises.geojson")

UMBRAL = 5  # antes era 7
BBOX = (-10.0, 35.0, 5.0, 44.5)

print(f"Cargando HydroRIVERS (orden >= {UMBRAL})...")
gdf = gpd.read_file(SHP_RIVERS, bbox=BBOX)
gdf_filt = gdf[gdf["ORD_STRA"] >= UMBRAL].copy()
gdf_filt = gdf_filt[["ORD_STRA", "geometry"]].rename(columns={"ORD_STRA": "ord"})
gdf_filt = gdf_filt.to_crs("EPSG:4326")
print(f"Ríos en bbox con orden >={UMBRAL}: {len(gdf_filt)}")

# Construir máscara: España (cuencas) + Portugal (excluyendo Francia)
gdf_cuencas = gpd.read_file(CUENCAS).to_crs("EPSG:4326")
gdf_paises = gpd.read_file(PAISES).to_crs("EPSG:4326")

# Quedarnos solo con Portugal
gdf_portugal = gdf_paises[gdf_paises["NAME"] == "Portugal"]
print(f"Portugal: {len(gdf_portugal)} feature(s)")

# Unión de geometrías para máscara
from shapely.ops import unary_union
mask = unary_union(list(gdf_cuencas.geometry) + list(gdf_portugal.geometry))
print("Máscara Iberia construida")

# Buffer pequeño para no perder ríos justo en la frontera (1 km ≈ 0.01°)
mask_buf = mask.buffer(0.01)

# Filtrar ríos: solo los que intersectan con la máscara
print("Recortando ríos a península...")
mask_filter = gdf_filt.geometry.intersects(mask_buf)
gdf_iberia = gdf_filt[mask_filter].copy()
print(f"Ríos en península ibérica: {len(gdf_iberia)}")

# Recortar la geometría a la máscara (para que los tramos exteriores no se dibujen)
gdf_iberia["geometry"] = gdf_iberia.geometry.intersection(mask_buf)
gdf_iberia = gdf_iberia[~gdf_iberia.geometry.is_empty]

# Simplificar
gdf_iberia["geometry"] = gdf_iberia["geometry"].simplify(tolerance=0.005, preserve_topology=True)

if OUT_RIOS.exists():
    OUT_RIOS.unlink()
gdf_iberia.to_file(OUT_RIOS, driver="GeoJSON")

print(f"\nGuardado: {OUT_RIOS}")
print(f"Tamaño: {OUT_RIOS.stat().st_size/1024:.0f} KB ({len(gdf_iberia)} ríos)")
print("\nRECUERDA: copia rios.geojson a docs/ (o haz quarto render)")