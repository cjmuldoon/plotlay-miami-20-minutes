# How far does 20 minutes get you in Miami?

For every resident of Miami-Dade County, Florida (2,701,767 people in 25,813 Census blocks with
people), the trip to eight everyday places: Downtown, the nearest beach, Miami International Airport, the nearest
hospital emergency department, the nearest university campus, the ballpark, the Everglades and the nearest big mall.
By car at the speed limit with no traffic, in the morning and evening rush hour, and by public transport.

The showcase: https://www.getplotlay.com/showcase/miami-20-minutes/ . Made with [Plotlay](https://www.getplotlay.com)'s
How far by car (with road rules) and How far by public transport.

## The answer

Read as a general saying, the test is whether at least half the places (4 of the 8) are within 20 minutes:

| Run | Residents with 4 or more of the 8 within 20 minutes |
|---|---|
| Car, speed limit, no traffic (`free`) | **59.3%** |
| Car, morning rush hour (`am`) | **21.5%** |
| Car, evening rush hour (`pm`) | **18.0%** |
| Public transport, arriving 8 to 9 am (`pt`) | **0.8%** |

Read literally, all eight within 20 minutes: 0.0% in every run. The Everglades decide it: only
2.1% of residents are within 20 minutes of Shark Valley or the Coe Visitor Center
even with no traffic.

The typical resident has 4 of the 8 within 20 minutes at the speed limit, 3 in the
morning rush hour, 2 in the evening and 0 by public transport. Residents by how many
of the 8 are within 20 minutes (0 to 8), at the speed limit: 0.6%, 0.1%, 5.0%, 35.0%, 12.4%, 8.1%, 7.2%, 31.7%, 0.0%.

| Within 20 minutes of | Car, speed limit | Car, morning rush | Car, evening rush | Public transport |
|---|---|---|---|---|
| An ER | 99.4% | 90.9% | 86.3% | 10.8% |
| A mall | 99.4% | 80.5% | 72.3% | 10.3% |
| A university | 87.8% | 59.6% | 53.0% | 3.8% |
| A beach | 51.6% | 23.3% | 19.8% | 4.7% |
| The ballpark | 45.1% | 16.7% | 14.7% | 1.5% |
| The airport | 43.7% | 9.3% | 6.6% | 0.0% |
| Downtown | 40.8% | 15.2% | 13.0% | 4.6% |
| The Everglades | 2.1% | 0.2% | 0.2% | 0.0% |
| Half or more (4 of 8) | 59.3% | 21.5% | 18.0% | 0.8% |
| All eight | 0.0% | 0.0% | 0.0% | 0.0% |

## Who and where

- **Residents**: the 2020 Census (P.L. 94-171 redistricting data, `POP20`), 2,701,767 people in 25,813
  blocks with people, each block placed at its internal point (`INTPTLAT20`, `INTPTLON20`). Each block also carries
  the Census place (city, town, village or CDP) its internal point falls in.
- **The eight places**. Only places inside Miami-Dade count. Each trip goes to the nearest place of its kind:

- **Downtown Miami (Government Center)** (1 point): Downtown Miami at Government Center, 111 NW 1st Street (the Stephen P. Clark Government Center and its Metrorail and Metromover station).
- **The nearest beach** (171 points): OpenStreetMap sand beaches (natural=beach) of 1 ha or more in Miami-Dade: 17, from Golden Beach and Sunny Isles down Miami Beach and South Beach to Key Biscayne and the bay beaches, each a point every 500 m along its outline (171 points).
- **Miami International Airport** (1 point): Miami International Airport, the departures road in front of the main terminal by Concourse E.
- **The nearest hospital emergency department** (20 points): General hospitals in Miami-Dade with emergency services in the CMS Hospital General Information file (October 2026), with Jackson Health System’s four campuses (one listing in the file) counted apart, and HCA Florida Mercy in Coconut Grove: 20. Children’s, veterans’ and freestanding emergency rooms are left out.
- **The nearest university campus** (7 points): The teaching campuses of Florida International University (Modesto A. Maidique in Westchester, Biscayne Bay in North Miami), the University of Miami (Coral Gables, the Miller School medical campus), Barry University, St. Thomas University and Florida Memorial University. Miami Dade College and branch campuses of out-of-county universities are left out.
- **loanDepot park** (1 point): loanDepot park in Little Havana, home of the Miami Marlins (the middle of its OpenStreetMap outline).
- **The Everglades (Shark Valley or the Coe Visitor Center)** (2 points): Everglades National Park’s two entrances in Miami-Dade, whichever is nearer: the Shark Valley Visitor Center on the Tamiami Trail and the Ernest F. Coe Visitor Center west of Homestead.
- **The nearest big mall** (16 points): Named malls in OpenStreetMap (shop=mall) in Miami-Dade with an outline of 2 ha or more: 16. Centres mapped another way (The Falls is mapped as retail land) are missed; others nearby stand in.

## Method

The drive and transit times come from Plotlay's own engine (`src/core/drivetime.js` with `roadrules.js` for the car,
`transitroute.js` for public transport). The engine is not in this repository; `pipeline/scripts/run.mjs` shows how it
was called and with which settings.

- **Roads**: OpenStreetMap, Geofabrik's Florida extract of November 2026 (2026-11-20), cut to a
  box round the county that reaches into southern Broward: 27,117 km of road, 279,278 one-way
  stretches, 4,493 turn bans, 8,677 traffic-signal nodes joined into 3,418 sets of lights.
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
  2026, arriving between 8 and 9 am: the median trip over departures every 2 minutes. Up to 3 transfers;
  walking at 5.1 km/h on OpenStreetMap streets and paths, at most 1,200 m to or from a stop. Each home is
  read from the street nodes within 250 m of it. Beaches with more than 50 points are thinned to 50 for
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
`pd.read_csv('data/block_minutes.csv', dtype={'block_geoid': str, 'place_geoid': str})`.

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
