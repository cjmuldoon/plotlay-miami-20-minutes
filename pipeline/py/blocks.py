# Miami-Dade County's residents by 2020 Census block (TIGER/Line 2020 tabblock20, POP20 from the 2020 redistricting
# data), each at the block's internal point (INTPTLAT20/INTPTLON20), with its block group and the Census place
# (city, town, village or CDP) its internal point falls in. Public domain (US Census Bureau).
#   python3 -I py/blocks.py <build dir>
# Out: raw/census/people-miami.json  { blocks: [{ geoid, people, ll, place }], places: { geoid: name } }
#      raw/census/blocks-miami.geojson (simplified outlines, for the maps), raw/census/places-miami.geojson
import sys, os, json, zipfile, io
import shapefile
from shapely.geometry import shape, Point, mapping
from shapely.strtree import STRtree
B = sys.argv[1]; C = os.path.join(B, 'raw/census')
def read(zp):
    z = zipfile.ZipFile(zp); base = [n[:-4] for n in z.namelist() if n.endswith('.shp')][0]
    return shapefile.Reader(shp=io.BytesIO(z.read(base + '.shp')), dbf=io.BytesIO(z.read(base + '.dbf')), shx=io.BytesIO(z.read(base + '.shx')))
pl = read(os.path.join(C, 'tl_2020_12_place.zip'))
places, geoms = {}, []
for sr in pl.iterShapeRecords():
    r = sr.record.as_dict(); g = shape(sr.shape.__geo_interface__)
    # Miami-Dade's extent, roughly: keep places that touch it
    if g.bounds[2] < -80.9 or g.bounds[0] > -80.0 or g.bounds[3] < 25.1 or g.bounds[1] > 26.0: continue
    places[r['GEOID']] = {'name': r['NAMELSAD'], 'short': r['NAME'], 'kind': r['LSAD'], 'g': g}
ids = list(places); tree = STRtree([places[i]['g'] for i in ids])
bl = read(os.path.join(C, 'tl_2020_12086_tabblock20.zip'))
out, feats, tot = [], [], 0
for sr in bl.iterShapeRecords():
    r = sr.record.as_dict()
    if r['COUNTYFP20'] != '086': continue
    p = int(r['POP20'])
    if p <= 0: continue
    lat, lng = float(r['INTPTLAT20']), float(r['INTPTLON20'])
    pt = Point(lng, lat); hit = None
    for k in tree.query(pt):
        if places[ids[k]]['g'].contains(pt): hit = ids[k]; break
    out.append({'geoid': r['GEOID20'], 'people': p, 'll': [round(lat, 6), round(lng, 6)], 'place': hit})
    g = shape(sr.shape.__geo_interface__).simplify(0.00005, preserve_topology=True)
    feats.append({'type': 'Feature', 'properties': {'geoid': r['GEOID20'], 'people': p}, 'geometry': json.loads(json.dumps(mapping(g)), parse_float=lambda x: round(float(x), 5))})
    tot += p
used = {b['place'] for b in out if b['place']}
json.dump({'county': 'Miami-Dade County, Florida (12086)', 'census': '2020 Census, P.L. 94-171 redistricting data (POP20 on TIGER/Line 2020 tabblock20)', 'residents': tot,
           'blocks': out, 'places': {k: {'name': places[k]['name'], 'short': places[k]['short'], 'kind': places[k]['kind']} for k in used}}, open(os.path.join(C, 'people-miami.json'), 'w'))
json.dump({'type': 'FeatureCollection', 'features': feats}, open(os.path.join(C, 'blocks-miami.geojson'), 'w'))
json.dump({'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'properties': {'geoid': k, 'name': places[k]['short']}, 'geometry': mapping(places[k]['g'].simplify(0.0002))} for k in used]}, open(os.path.join(C, 'places-miami.geojson'), 'w'))
print('blocks with people', len(out), 'residents', tot, 'places', len(used), 'not in a place', sum(b['people'] for b in out if not b['place']))
