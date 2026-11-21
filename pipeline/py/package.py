# The public repository (repo-src/) and the page's data download for "How far does 20 minutes get you in Miami?": the
# minutes for every 2020 Census block to each of the eight places (car at the speed limit, morning and evening rush hour,
# typical speeds; public transport), wide and long, the places table, the places, the numbers, the pipeline's own code,
# README and licences. The notebook is written by gen_notebook.py and executed afterwards; the zip is made by zip.py.
#   python3 -I py/package.py <build dir>
import sys, os, json, csv, shutil, re, subprocess
B = sys.argv[1]
R = os.path.join(B, 'repo-src'); shutil.rmtree(R, ignore_errors=True)
for d in ('data', 'python', 'pipeline/scripts', 'pipeline/py', 'scripts'): os.makedirs(os.path.join(R, d), exist_ok=True)
T = json.load(open(os.path.join(B, 'out/times.json'))); N = json.load(open(os.path.join(B, 'numbers.json')))
IDS = ['cbd', 'beach', 'airport', 'hospital', 'uni', 'stadium', 'glades', 'shops']
RUNS = ['free', 'am', 'pm', 'typical', 'pt']
key = lambda run, d: f'pt_{d}' if run == 'pt' else f'car_{run}_{d}'
cols = [f'{run}_{d}' for run in RUNS for d in IDS]
blank = lambda v: '' if v is None else v

# wide: one row per block (Power BI, Excel); long: one row per block, run and place, unreached rows left out
with open(os.path.join(R, 'data/block_minutes.csv'), 'w', newline='') as f, open(os.path.join(R, 'data/block_minutes_long.csv'), 'w', newline='') as g:
    w = csv.writer(f); w.writerow(['block_geoid', 'place_geoid', 'residents', 'lat', 'lng', *cols])
    wl = csv.writer(g); wl.writerow(['block_geoid', 'run', 'place', 'minutes'])
    for i, h in enumerate(T['homes']):
        vals = [T['runs'][key(run, d)][i] for run in RUNS for d in IDS]
        w.writerow([h['code'], blank(h['place']), h['people'], h['ll'][0], h['ll'][1], *map(blank, vals)])
        for run in RUNS:
            for d in IDS:
                v = T['runs'][key(run, d)][i]
                if v is not None: wl.writerow([h['code'], run, d, v])
assert os.path.getsize(os.path.join(R, 'data/block_minutes_long.csv')) < 50e6
shutil.copy(os.path.join(B, 'tables/places.csv'), os.path.join(R, 'data/places_table.csv'))
shutil.copy(os.path.join(B, 'tables/destinations.csv'), os.path.join(R, 'data/shares_by_place.csv'))

# the places, straight from scripts/destinations.mjs (the same code the run used)
js = ("import { destinations } from " + json.dumps('file://' + os.path.join(os.path.abspath(B), 'scripts/destinations.mjs')) +
      "; console.log(JSON.stringify(destinations(" + json.dumps(os.path.abspath(B)) + ")));")
DEST = json.loads(subprocess.run(['node', '--input-type=module', '-e', js], capture_output=True, text=True, check=True).stdout)
with open(os.path.join(R, 'data/places.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['kind', 'name', 'lat', 'lng'])
    for d in DEST:
        for p in d['points']: w.writerow([d['id'], p['name'], round(p['ll'][0], 6), round(p['ll'][1], 6)])
json.dump({k: v for k, v in N.items() if k not in ('counter', 'hist_cbd')}, open(os.path.join(R, 'data/numbers.json'), 'w'), indent=1)

def scrub(src, dst):
    # the public copy names no local folders
    t = open(src).read(); P = 'Projects' + '_Local'
    t = re.sub(r'\$HOME/' + P + r'/plotlay-worktrees/[a-z0-9-]+', '$PLOTLAY_REPO', t)
    t = re.sub(r'\$HOME/' + P + r'/plotlay-outputs', '$OUTPUTS', t).replace('~/' + P + '/plotlay-outputs', '$OUTPUTS')
    assert P not in t and '/Us' + 'ers/' not in t, src
    open(dst, 'w').write(t); shutil.copymode(src, dst)
for f in ('run.mjs', 'osm_extract.sh', 'opl.mjs', 'destinations.mjs'): scrub(os.path.join(B, 'scripts', f), os.path.join(R, 'pipeline/scripts', f))
for f in ('blocks.py', 'numbers.py', 'package.py', 'gen_notebook.py'): scrub(os.path.join(B, 'py', f), os.path.join(R, 'pipeline/py', f))

open(os.path.join(R, 'scripts/get_gtfs.sh'), 'w').write('''#!/bin/bash
# Fetches the Miami-Dade Transit GTFS timetable into pipeline/raw/gtfs/, where pipeline/scripts/run.mjs reads it.
# The file is not in this repository: it is Miami-Dade County's, published under the County's disclaimer
# (https://www.miamidade.gov/global/disclaimer/disclaimer.page). The run used the feed current on 22 November 2026;
# the feed changes with each service change, so a later download can give slightly different times.
#   bash scripts/get_gtfs.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p pipeline/raw/gtfs
curl -fL --retry 3 -A 'Mozilla/5.0 (compatible; gtfs-fetch)' \\
  -o pipeline/raw/gtfs/miami-dade-transit.zip \\
  https://www.miamidade.gov/transit/googletransit/current/google_transit.zip
ls -la pipeline/raw/gtfs/miami-dade-transit.zip
''')
os.chmod(os.path.join(R, 'scripts/get_gtfs.sh'), 0o755)
open(os.path.join(R, '.gitignore'), 'w').write('.ipynb_checkpoints/\n__pycache__/\n.DS_Store\npipeline/raw/\npipeline/out/\n')

pc = lambda x: f'{x * 100:.1f}%'
A, D = N['all'], N['destinations']
rows = '\n'.join(f"| {D[d]['short']} | {pc(D[d]['runs']['free']['within_20'])} | {pc(D[d]['runs']['am']['within_20'])} | {pc(D[d]['runs']['pm']['within_20'])} | {pc(D[d]['runs']['pt']['within_20'])} |"
                 for d in sorted(IDS, key=lambda d: -D[d]['runs']['free']['within_20']))
hows = '\n'.join(f"- **{d['name']}** ({len(d['points'])} point{'s' if len(d['points']) != 1 else ''}): {d['how']}" for d in DEST)
net = N['network']
readme = f"""# How far does 20 minutes get you in Miami?

For every resident of Miami-Dade County, Florida ({N['residents']:,} people in {N['blocks']:,} Census blocks with
people), the trip to eight everyday places: Downtown, the nearest beach, Miami International Airport, the nearest
hospital emergency department, the nearest university campus, the ballpark, the Everglades and the nearest big mall.
By car at the speed limit with no traffic, in the morning and evening rush hour, and by public transport.

The showcase: https://www.getplotlay.com/showcase/miami-20-minutes/ . Made with [Plotlay](https://www.getplotlay.com)'s
How far by car (with road rules) and How far by public transport.

## The answer

Read as a general saying, the test is whether at least half the places (4 of the 8) are within 20 minutes:

| Run | Residents with 4 or more of the 8 within 20 minutes |
|---|---|
| Car, speed limit, no traffic (`free`) | **{pc(A['free']['half_20'])}** |
| Car, morning rush hour (`am`) | **{pc(A['am']['half_20'])}** |
| Car, evening rush hour (`pm`) | **{pc(A['pm']['half_20'])}** |
| Public transport, arriving 8 to 9 am (`pt`) | **{pc(A['pt']['half_20'])}** |

Read literally, all eight within 20 minutes: {pc(A['free']['within_20'])} in every run. The Everglades decide it: only
{pc(D['glades']['runs']['free']['within_20'])} of residents are within 20 minutes of Shark Valley or the Coe Visitor Center
even with no traffic.

The typical resident has {A['free']['median_count']} of the 8 within 20 minutes at the speed limit, {A['am']['median_count']} in the
morning rush hour, {A['pm']['median_count']} in the evening and {A['pt']['median_count']} by public transport. Residents by how many
of the 8 are within 20 minutes (0 to 8), at the speed limit: {', '.join(pc(x) for x in A['free']['count_dist'])}.

| Within 20 minutes of | Car, speed limit | Car, morning rush | Car, evening rush | Public transport |
|---|---|---|---|---|
{rows}
| Half or more (4 of 8) | {pc(A['free']['half_20'])} | {pc(A['am']['half_20'])} | {pc(A['pm']['half_20'])} | {pc(A['pt']['half_20'])} |
| All eight | {pc(A['free']['within_20'])} | {pc(A['am']['within_20'])} | {pc(A['pm']['within_20'])} | {pc(A['pt']['within_20'])} |

## Who and where

- **Residents**: the 2020 Census (P.L. 94-171 redistricting data, `POP20`), {N['residents']:,} people in {N['blocks']:,}
  blocks with people, each block placed at its internal point (`INTPTLAT20`, `INTPTLON20`). Each block also carries
  the Census place (city, town, village or CDP) its internal point falls in.
- **The eight places**. Only places inside Miami-Dade count. Each trip goes to the nearest place of its kind:

{hows}

## Method

The drive and transit times come from Plotlay's own engine (`src/core/drivetime.js` with `roadrules.js` for the car,
`transitroute.js` for public transport). The engine is not in this repository; `pipeline/scripts/run.mjs` shows how it
was called and with which settings.

- **Roads**: OpenStreetMap, Geofabrik's Florida extract of November 2026 ({net['osm_extract'].split(', ')[1][:10]}), cut to a
  box round the county that reaches into southern Broward: {net['km']:,} km of road, {net['one_way_stretches']:,} one-way
  stretches, {net['turn_bans']:,} turn bans, {net['signal_nodes']:,} traffic-signal nodes joined into {net['sets_of_lights']:,} sets of lights.
- **Road rules** (Plotlay's, for the United States): keeping right; one-way streets and turn bans; a wait at each set
  of traffic lights and at each junction; the posted speed limit, and where none is mapped the usual US limit for
  the class of road (30 mph on local streets up to 65 mph on motorways).
- **Trips**: from each block to the nearest place of each kind, by the quickest route.
- **Runs**:

  | Run | What it is |
  |---|---|
  | `free` | At the speed limit, no traffic |
  | `am` | Morning rush hour: [TomTom Traffic Index 2025](https://www.tomtom.com/traffic-index/miami-traffic/), Miami metro area, busiest hour 8 to 9 am: highways 75.5% slower than free flow, other roads 73.6% |
  | `pm` | Evening rush hour: busiest hour 5 to 6 pm: highways 98.9% slower, other roads 86.5% |
  | `typical` | Plotlay's older model of typical speeds by road class, kept for comparison |
  | `pt` | Public transport |

  TomTom's figures were read on 22 November 2026. The rush hour is a city-wide average slowdown applied to every road
  of its kind, not a traffic forecast.
- **Public transport**: Miami-Dade Transit's GTFS timetable (Metrorail, Metromover, Metrobus) for Tuesday 24 November
  2026, arriving between 8 and 9 am: the median trip over departures every 2 minutes. Up to {N['pt']['transfers']} transfers;
  walking at 5.1 km/h on OpenStreetMap streets and paths, at most {N['pt']['walk_max_m']:,} m to or from a stop. Each home is
  read from the street nodes within {N['pt']['home_from_nodes_m']} m of it. Beaches with more than 50 points are thinned to 50 for
  public transport. The MIA Mover from the Miami Intermodal Center is not in the timetable, so public transport to the
  airport terminal is understated.

This is a model, not a traffic forecast. Its accuracy depends on OpenStreetMap (roads, speed limits, turn bans,
lights), on the timetable and on the cited rush-hour slowdown. Trips are door to door from the middle of each block
and leave out parking.

## Files

| File | What it is |
|---|---|
| `data/block_minutes.csv` | Minutes per Census block: `block_geoid`, `place_geoid` (empty outside any Census place), `residents`, `lat`, `lng`, then `<run>_<place>` for runs `free`, `am`, `pm`, `typical`, `pt` and places `cbd` (Downtown), `beach`, `airport`, `hospital`, `uni`, `stadium` (the ballpark), `glades` (the Everglades), `shops` (a big mall). Empty: not reached (road-less islands, or no trip within the limits). |
| `data/block_minutes_long.csv` | The same in long form: `block_geoid`, `run`, `place`, `minutes`; unreached rows left out. |
| `data/places_table.csv` | By Census place: residents, `share_half_<run>` (residents with 4 or more of the 8), places within 20 minutes on average, minutes to Downtown, the share within 20 minutes of each place. |
| `data/shares_by_place.csv` | Per destination and run: share and residents within 20 minutes, the median minutes, within 15 and 30, not reached. |
| `data/places.csv` | Every point used for the eight places: `kind`, `name`, `lat`, `lng`. |
| `data/numbers.json` | Every number on the showcase page. |
| `python/miami_20_minutes.ipynb` | A narrated notebook: reads only `../data`, gets the headline again and draws the charts. |
| `pipeline/` | The code that made it: `scripts/osm_extract.sh` (OpenStreetMap inputs, with osmium), `py/blocks.py` (Census blocks), `scripts/destinations.mjs` (the places), `scripts/run.mjs` (the engine run; needs Plotlay's engine), `py/numbers.py` (the numbers and tables), `py/package.py` and `py/gen_notebook.py` (this repository). |
| `scripts/get_gtfs.sh` | Fetches the Miami-Dade Transit GTFS. |

Power BI: `block_minutes.csv` and `places_table.csv` open with Get data, Text/CSV; set `block_geoid` and `place_geoid`
to text so the leading digits stay, and `lat` and `lng` place each block on a map visual. Pandas:
`pd.read_csv('data/block_minutes.csv', dtype={{'block_geoid': str, 'place_geoid': str}})`.

## Run it again

The inputs are not in the repository. Put them under `pipeline/raw/`:

- `pipeline/raw/osm/`: from Geofabrik's `florida-latest.osm.pbf` (https://download.geofabrik.de/north-america/us/florida.html),
  `bash pipeline/scripts/osm_extract.sh florida-latest.osm.pbf`.
- `pipeline/raw/census/`: https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_12_tabblock20.zip (saved as
  `tl_2020_12086_tabblock20.zip`) and https://www2.census.gov/geo/tiger/TIGER2020/PLACE/tl_2020_12_place.zip, then
  `python3 pipeline/py/blocks.py pipeline` (needs pyshp and shapely).
- `pipeline/raw/gtfs/`: `bash scripts/get_gtfs.sh`.
- The hospital list was checked against the CMS Hospital General Information file
  (https://data.cms.gov/provider-data/dataset/xubh-q36u); the points are in `scripts/destinations.mjs`.

Then `node --max-old-space-size=12288 pipeline/scripts/run.mjs <plotlay engine>` and `python3 pipeline/py/numbers.py pipeline`.

## Sources

- OpenStreetMap, (c) OpenStreetMap contributors, Open Database License 1.0: roads, footpaths, beaches and malls.
- U.S. Census Bureau, TIGER/Line Shapefiles 2020 (blocks and places) and the 2020 Census: public domain.
- Centers for Medicare & Medicaid Services, Hospital General Information: public domain.
- TomTom Traffic Index 2025, Miami (https://www.tomtom.com/traffic-index/miami-traffic/): the figures are cited, not redistributed.
- Miami-Dade Transit GTFS: fetched by `scripts/get_gtfs.sh`, not redistributed.

## Licence

- **Code** (`pipeline/`, `scripts/`, `python/`): MIT, see `LICENSE`.
- **Data** (`data/`): the minutes, the beach and mall points and everything else made from OpenStreetMap are a derived
  database under the Open Database License 1.0, see `LICENSE-DATA`. If you publish a database made from them, offer it
  under the same licence and credit OpenStreetMap contributors. The Census and CMS columns are public domain.

Independent work using open data, not endorsed by Miami-Dade County, Miami-Dade Transit, TomTom or the U.S. Census Bureau.
"""
assert chr(0x2014) not in readme
open(os.path.join(R, 'README.md'), 'w').write(readme)
open(os.path.join(R, 'LICENSE'), 'w').write("""MIT License

Copyright (c) 2026 Plotlay

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""")
open(os.path.join(R, 'LICENSE-DATA'), 'w').write("""The tables in data/ are made from OpenStreetMap data, (c) OpenStreetMap contributors, and are made available under
the Open Database License (ODbL) 1.0: https://opendatacommons.org/licenses/odbl/1-0/ . If you publish a database
made from them, offer it under the same licence and credit OpenStreetMap contributors.

Residents, blocks and places: U.S. Census Bureau, 2020 Census and TIGER/Line 2020, public domain.
Hospitals: Centers for Medicare & Medicaid Services, Hospital General Information, public domain.
Public transport times: made from Miami-Dade Transit's GTFS timetable, which is not redistributed here.
Rush-hour slowdown: TomTom Traffic Index 2025 (Miami), cited from tomtom.com/traffic-index; the figures are TomTom's.
""")
print('repo-src', sum(len(fs) for _, _, fs in os.walk(R)), 'files')
