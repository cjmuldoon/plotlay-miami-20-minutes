#!/bin/bash
# Fetches the Miami-Dade Transit GTFS timetable into pipeline/raw/gtfs/, where pipeline/scripts/run.mjs reads it.
# The file is not in this repository: it is Miami-Dade County's, published under the County's disclaimer
# (https://www.miamidade.gov/global/disclaimer/disclaimer.page). The run used the feed current on 22 November 2026;
# the feed changes with each service change, so a later download can give slightly different times.
#   bash scripts/get_gtfs.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p pipeline/raw/gtfs
curl -fL --retry 3 -A 'Mozilla/5.0 (compatible; gtfs-fetch)' \
  -o pipeline/raw/gtfs/miami-dade-transit.zip \
  https://www.miamidade.gov/transit/googletransit/current/google_transit.zip
ls -la pipeline/raw/gtfs/miami-dade-transit.zip
