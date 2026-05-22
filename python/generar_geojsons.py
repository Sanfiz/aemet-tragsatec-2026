"""
Genera dos GeoJSON para el visor de cuencas:
  1. cuencas.geojson  — 16 cuencas (península + Baleares)
  2. rios.geojson     — ríos principales (orden ≥4) de la zona

Ambos en EPSG:4326, simplificados para web.
"""
import geopandas as gpd
from pathlib import Path

# Rutas (ajusta si difieren)
SHP_CUENCAS = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/EMBALSES/data-basins/DemarcHidrograficas_mayo2023.shp")
SHP_RIVERS  = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/EMBALSES/data-basins/HydroRIVERS_v10_eu_shp/HydroRIVERS_v10_eu.shp")

OUT_DIR = Path("/etc/ecmwf/nfs/dh2_perm_b/esp9221/pred-estacional")
OUT_CUENCAS = OUT_DIR / "cuencas.geojson"
OUT_RIOS    = OUT_DIR / "rios.geojson"

# Bounding box península + Baleares (lon_min, lat_min, lon_max, lat_max)
# Lon: -10 (Galicia) a 5 (Menorca)
# Lat: 35 (Algeciras) a 44 (Cantábrico)
BBOX_PEN_BAL = (-10.0, 35.0, 5.0, 44.5)

# Cuencas peninsulares + Baleares (16)
CODIGOS_PEN_BAL = [
    "ES010",  # MIÑO-SIL
    "ES014",  # GALICIA-COSTA
    "ES017",  # CANTÁBRICO ORIENTAL
    "ES018",  # CANTÁBRICO OCCIDENTAL
    "ES020",  # DUERO
    "ES030",  # TAJO
    "ES040",  # GUADIANA
    "ES050",  # GUADALQUIVIR
    "ES060",  # CUENCAS MEDITERRÁNEAS ANDALUZAS
    "ES063",  # GUADALETE Y BARBATE
    "ES064",  # TINTO, ODIEL Y PIEDRAS
    "ES070",  # SEGURA
    "ES080",  # JÚCAR
    "ES091",  # EBRO
    "ES100",  # DISTRITO DE CUENCA FLUVIAL DE CATALUÑA
    "ES110",  # ISLAS BALEARES
]

# =========================
# 1. CUENCAS
# =========================
print("="*60)
print("1. CUENCAS")
print("="*60)
gdf = gpd.read_file(SHP_CUENCAS, encoding="utf-8").to_crs("EPSG:4326")
print(f"Total demarcaciones cargadas: {len(gdf)}")

gdf_filt = gdf[gdf["CodDemarc"].isin(CODIGOS_PEN_BAL)].copy()
gdf_filt = gdf_filt[["CodDemarc", "Nombre", "geometry"]]
print(f"Filtradas (península + Baleares): {len(gdf_filt)}")

# Simplificar (mantenemos buena resolución, 0.005° ≈ 500m)
gdf_filt["geometry"] = gdf_filt["geometry"].simplify(tolerance=0.005, preserve_topology=True)

if OUT_CUENCAS.exists():
    OUT_CUENCAS.unlink()
gdf_filt.to_file(OUT_CUENCAS, driver="GeoJSON")
print(f"\nGuardado: {OUT_CUENCAS}")
print(f"Tamaño: {OUT_CUENCAS.stat().st_size/1024:.0f} KB")

# =========================
# 2. RÍOS HydroRIVERS
# =========================
print("\n" + "="*60)
print("2. RÍOS")
print("="*60)
print("Cargando HydroRIVERS (puede tardar 30s)...")

# Leer solo la bbox para no cargar Europa entera
gdf_rios = gpd.read_file(SHP_RIVERS, bbox=BBOX_PEN_BAL)
print(f"Ríos en bbox: {len(gdf_rios)}")
print(f"Columnas disponibles: {list(gdf_rios.columns)}")

# El campo de jerarquía en HydroRIVERS suele ser 'ORD_STRA' (Strahler order)
# Filtramos por orden ≥4 para tener solo los grandes
if "ORD_STRA" in gdf_rios.columns:
    ord_col = "ORD_STRA"
elif "ord_stra" in gdf_rios.columns:
    ord_col = "ord_stra"
else:
    # Buscar columna que parezca de orden
    ord_col = None
    for c in gdf_rios.columns:
        if "stra" in c.lower() or "order" in c.lower():
            ord_col = c
            break
    print(f"⚠ Campo ORD_STRA no encontrado. Usando: {ord_col}")

print(f"Distribución por orden Strahler:")
print(gdf_rios[ord_col].value_counts().sort_index())

# Filtrar orden ≥4 (ríos principales)
gdf_rios_filt = gdf_rios[gdf_rios[ord_col] >= 4].copy()
print(f"\nRíos con orden ≥4: {len(gdf_rios_filt)}")

# Mantener solo columnas necesarias para el visor
keep_cols = [ord_col, "geometry"]
gdf_rios_filt = gdf_rios_filt[keep_cols]
gdf_rios_filt = gdf_rios_filt.rename(columns={ord_col: "ord"})

# Asegurar CRS
gdf_rios_filt = gdf_rios_filt.to_crs("EPSG:4326")

# Simplificar líneas (tolerance ligero)
gdf_rios_filt["geometry"] = gdf_rios_filt["geometry"].simplify(tolerance=0.005, preserve_topology=True)

if OUT_RIOS.exists():
    OUT_RIOS.unlink()
gdf_rios_filt.to_file(OUT_RIOS, driver="GeoJSON")
print(f"\nGuardado: {OUT_RIOS}")
print(f"Tamaño: {OUT_RIOS.stat().st_size/1024:.0f} KB")

print("\n" + "="*60)
print("RESUMEN")
print("="*60)
print(f"  cuencas.geojson: {OUT_CUENCAS.stat().st_size/1024:.0f} KB ({len(gdf_filt)} cuencas)")
print(f"  rios.geojson:    {OUT_RIOS.stat().st_size/1024:.0f} KB ({len(gdf_rios_filt)} ríos)")

print("\nRecuerda añadir AMBOS a _quarto.yml en resources:")
print("  resources:")
print("    - images/")
print("    - cuencas.geojson")
print("    - rios.geojson")
