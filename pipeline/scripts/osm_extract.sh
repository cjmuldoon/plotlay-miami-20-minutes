#!/bin/bash
# The OpenStreetMap inputs for Miami-Dade County, Florida, from Geofabrik's Florida extract
# (osmosis_replication_timestamp 2026-11-20T21:21:21Z). The county's Census blocks span about 25.13 to 25.98 N,
# 80.87 to 80.12 W; the box adds a margin, and reaches into southern Broward so trips near the county line can use
# its roads:
#   raw/osm/roads.opl          drivable ways, traffic signal nodes, turn restriction relations
#   raw/osm/places.geojsonseq  beaches, shopping centres, hospitals, universities, stadiums, terminals, parks
#   raw/osm/walk.geojsonseq    walkable ways for public transport
#   bash scripts/osm_extract.sh <florida-latest.osm.pbf>
set -euo pipefail
cd "$(dirname "$0")/../raw/osm"
PBF="$1"; BOX=-80.98,25.08,-80.05,26.10
osmium extract -b "$BOX" "$PBF" -o miami-box.pbf --overwrite -s smart
osmium tags-filter miami-box.pbf w/highway=motorway,motorway_link,trunk,trunk_link,primary,primary_link,secondary,secondary_link,tertiary,tertiary_link,unclassified,residential,living_street,service,road n/highway=traffic_signals r/type=restriction -o roads.pbf --overwrite
osmium cat roads.pbf -f opl -o roads.opl --overwrite
osmium tags-filter miami-box.pbf nwr/natural=beach nwr/shop=mall nwr/amenity=hospital nwr/amenity=university nwr/leisure=stadium nwr/aeroway=terminal nwr/boundary=national_park nwr/tourism=information -o places.pbf --overwrite
osmium export places.pbf -f geojsonseq -a type,id -o places.geojsonseq --overwrite
osmium tags-filter miami-box.pbf w/highway -o walk.pbf --overwrite
osmium export walk.pbf -f geojsonseq -o walk.geojsonseq --overwrite --geometry-types=linestring
ls -la roads.opl places.geojsonseq walk.geojsonseq
