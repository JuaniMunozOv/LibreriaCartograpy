# -------- SECCIÓN 1 --------

import os
os.environ["PROJ_LIB"] = indique su ruta"
import matplotlib.pyplot as plt
from cartograpy import data

# Crear carpeta de salida
os.makedirs("salidas", exist_ok=True)

# Cliente de GeoBoundaries
client = data.GeoBoundaries()

# Descargar límites de Argentina: ADM0 (país) y ADM1 (provincias)
arg_adm0 = client.adm("ARG", "ADM0")
arg_adm1 = client.adm("ARG", "ADM1")

# Filtrar provincia de San Juan
san_juan_df = arg_adm1[arg_adm1["shapeName"].str.contains("San Juan", case=False)]

# Guardar GeoJSONs
arg_adm0.to_file("salidas/argentina_adm0.geojson", driver="GeoJSON")
san_juan_df.to_file("salidas/san_juan_departamentos.geojson", driver="GeoJSON")

# Visualización
fig, ax = plt.subplots(figsize=(10, 10))
arg_adm0.plot(ax=ax, color='white', edgecolor='black')
san_juan_df.plot(ax=ax, color='lightblue', edgecolor='blue')
ax.set_title("Mapa de Argentina identificando la provincia de San Juan ")
ax.axis("off")
plt.savefig("salidas/mapa_argentina_sanjuan.png", dpi=300)
plt.show()


# -------- FIN SECCIÓN 1 --------

# -------- SECCIÓN 2 --------

import os, random
import cartopy.crs as ccrs
from cartograpy import data
from cartograpy.processing import add_column, centroids
from cartograpy.mapper import Map, get_fonts

# 1. Preparar entorno y carpeta de salidas
os.environ["PROJ_LIB"] = (  "indique su ruta"  # Ajuste según su sistema operativo
)
os.makedirs("salidas", exist_ok=True)

# 2. Descargar provincia de San Juan (ADM1) y sus departamentos (ADM2)
client     = data.GeoBoundaries()
adm1       = client.adm("ARG", "ADM1")
san_juan   = adm1[adm1["shapeName"].str.contains("San Juan", case=False)].copy()
adm2       = client.adm("ARG", "ADM2")
# Filtramos solo los deptos que intersectan la provincia
san_juan_depts = adm2[adm2.intersects(san_juan.unary_union)].copy()

# 3. Añadir columna random_data con valores entre 0 y 100
san_juan_depts = add_column(
    df=san_juan_depts,
    column_name="random_data",
    expression="random.randint(0, 100)",
    globals_dict={"random": random}
)

# 4. Calcular centroides de cada departamento
centroids_df = centroids(san_juan_depts)

# 5. Construir el mapa
mapa = Map(
    figsize=(10, 8),
    projection=ccrs.PlateCarree(),
    data_crs=ccrs.PlateCarree()  # indicamos que los datos ya están en lat/lon
)

# 5.1 Mapa cloropleth de random_data por departamento
mapa.add_polygons_cloropleth(
    gdf=san_juan_depts,
    column_to_plot="random_data",
    title="Datos Aleatorios por Departamento (San Juan)",
    cmap="viridis"
)

# 5.2 Añadir centroides en rojo
mapa.add_points(
    centroids_df,
    label="Centroides",
    size=25,
    color="red"
)

# 5.3 Decoraciones: flecha norte, escala y grillas con etiquetas pequeñas
# Flecha
minx, miny, maxx, maxy = san_juan_depts.total_bounds
mapa.add_arrow(3, position=(minx, maxy), zoom=0.06, color="black")
# Barra de escala
mapa.add_scale_bar(length=50, units="km", pad=0.02)
# Grillas y etiquetas reducidas
gl = mapa.add_gridlines(
    draw_labels=True,
    linestyle="--",
    color="gray",
    linewidth=0.5
)
gl.xlabel_style = {"size": 6}
gl.ylabel_style = {"size": 6}

# 5.4 Ajustar tipografía y título
font = get_fonts("Arial")[0]
mapa.set_font(font, size=8)
mapa.set_title(
    "Centroides de Departamentos de San Juan con Datos Aleatorios",
    fontsize=14,
    pad=12
)

# 6. Mostrar y guardar
mapa.show()
mapa.save("salidas/mapa_centroides_sanjuan.png")
print("✅ Mapa de centroides guardado en: salidas/mapa_centroides_sanjuan.png")

# -------- FIN SECCIÓN 2 --------


# -------- SECCIÓN 3 --------
import os
# 1. Variable PROJ_LIB para Windows (antes de geopandas/pyproj)
os.environ["PROJ_LIB"] = (
    indique su ruta"
)
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import cartopy.crs as ccrs
from cartograpy.mapper import Map, get_fonts
from cartograpy import data
from shapely.geometry import mapping

# 2. Carpeta de salida
os.makedirs("salidas", exist_ok=True)

# 3. Obtener polígono de San Juan desde GeoBoundaries
client = data.GeoBoundaries()
arg_adm1 = client.adm("ARG", "ADM1")
san_juan = arg_adm1[arg_adm1["shapeName"].str.contains("San Juan", case=False)].copy()

# 3.1. Guardar GeoJSON para uso posterior
san_juan.to_file("salidas/san_juan_departamentos.geojson", driver="GeoJSON")

# 3.2. Asegurar CRS WGS84
san_juan = san_juan.to_crs(epsg=4326)

# 4. Definir rutas de ráster
dem_input  = "DSMCopernicus.tif"
dem_output = "salidas/dem_sanjuan_clipped.tif"

# 5. Recortar DEM y convertir 0 → nodata
with rasterio.open(dem_input) as src:
    arr, transform = mask(
        src,
        [mapping(geom) for geom in san_juan.geometry],
        crop=True
    )
    meta = src.meta.copy()


# 5.2. Actualizar metadata
meta.update({
    "driver":  "GTiff",
    "height":  arr.shape[1],
    "width":   arr.shape[2],
    "transform": transform,
    "crs":     "EPSG:4326"
})

# 5.3. Guardar ráster recortado
with rasterio.open(dem_output, "w", **meta) as dst:
    dst.write(arr)

print(f"✅ DEM recortado guardado en: {dem_output}")

# 6. Crear mapa con Cartograpy/Cartopy
mapa = Map(figsize=(10, 6), projection=ccrs.PlateCarree())

# 6.1. Añadir ráster
mapa.add_raster(
    dem_output,
    cmap="terrain",
    title="Elevación – DSM Copernicus (San Juan)"
)

# 6.2. Ajustar extensión al polígono (+10% margen)
minx, miny, maxx, maxy = san_juan.total_bounds
dx, dy = maxx - minx, maxy - miny
pad = 0.1
mapa.ax.set_extent(
    [minx - dx*pad, maxx + dx*pad, miny - dy*pad, maxy + dy*pad],
    crs=ccrs.PlateCarree()
)

# 6.3. Contorno de San Juan
mapa.add_polygons(
    san_juan,
    facecolor="none",
    edgecolor="black",
    linewidth=1.2
)

# 6.4. Decoraciones: flecha de norte, escala y grillas
mapa.add_arrow(3, position=(minx, maxy), zoom=0.05, color="black")
mapa.add_scale_bar(length=50, units="km", pad=0.02)

# Configurar gridlines y etiquetas más pequeñas
gl = mapa.add_gridlines(draw_labels=True)
gl.toplabels = False
gl.rightlabels = False
gl.xlabel_style = {"size": 6}
gl.ylabel_style = {"size": 6}

# 6.5. Ajustar fuente y título
font = get_fonts("Arial")[0]
mapa.set_font(font, size=6)
mapa.set_title(
    "Modelo de Elevación – DSM Copernicus (San Juan)",
    fontsize=14, color="black", pad=12
)

# 6.6. Reducir tamaño de los ticks del colorbar
if hasattr(mapa, "cbar") and mapa.cbar is not None:
    mapa.cbar.ax.tick_params(labelsize=6)

# 7. Mostrar y guardar
mapa.show()
mapa.save("salidas/mapa_dem_copernicus.png")
print("✅ Mapa topográfico guardado en: salidas/mapa_dem_copernicus.png")