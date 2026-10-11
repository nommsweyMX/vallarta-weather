"""Colonia polygons from the Atlas de Peligros y Riesgos Puerto Vallarta 2024 GIS package (Colonias_DU_PV, UTM 13N),
converted to lat/lon and simplified, for labelling neighbourhoods named in flood and landslide reports.
Usage: colonias.py COLONIAS.shp OUT.json"""
import sys, json, shapefile, pyproj
from shapely.geometry import shape, mapping
src, out = sys.argv[1], sys.argv[2]
tr = pyproj.Transformer.from_crs('EPSG:32613', 'EPSG:4326', always_xy=True)
r = shapefile.Reader(src, encoding='latin-1')
fields = [f[0] for f in r.fields[1:]]
cols = []
for sr in r.iterShapeRecords():
    rec = dict(zip(fields, sr.record)); g = shape(sr.shape.__geo_interface__)
    if g.is_empty: continue
    g = g.simplify(15)
    polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
    rings = [[[round(c, 5) for c in tr.transform(x, y)] for x, y in p.exterior.coords] for p in polys]
    c = g.representative_point(); clon, clat = tr.transform(c.x, c.y)
    name = rec.get('NOMBRE') or rec.get('NOM_COL') or rec.get('nombre') or ''
    cols.append(dict(name=str(name).strip(), lat=round(clat, 5), lon=round(clon, 5), rings=rings))
json.dump(cols, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print(len(cols), 'colonias; fields', fields[:8])
