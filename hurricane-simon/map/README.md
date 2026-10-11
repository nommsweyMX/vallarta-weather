# Simon over Vallarta · Simon sobre Vallarta

A street-level map of Hurricane Simon for Greater Puerto Vallarta. It is built from **observations, not model
averages**. The GOES-18 satellite tracks the eye every 10 minutes, and the storm's current satellite rain
pattern is carried forward along that observed motion. The NHC's official track is shown for comparison.

`index.html` is a single self-contained page: data and images are inlined, and there is no build step to view it.

- **Satellite loop**: the last 4 hours of GOES-18 band-13 infrared (1-minute mesoscale sector, every 10 min),
  parallax-corrected. Past "now", the newest image (full-disk, to cover the south) slides along the track.
- **Street map** with three views: Greater Vallarta, Amapas & Emiliano Zapata, and El Pitillal. It shows
  shaded-relief terrain, streets, buildings and rivers (OpenStreetMap). Animated layers are wind streaks,
  rain rate, steep slopes that light up once rain passes the Caine (1980) landslide threshold, and rivers
  colored by catchment rain.
- **Three buildings**, each with its own exposure:
  - Amapas: 8th floor, north-facing windows.
  - Francisca Rodríguez 336, Emiliano Zapata: 3rd floor, elevated, ringed by 8-story buildings.
  - Cinco de Mayo & España, El Pitillal: street level, 2-story house.

  Each gets wind at its height (ASCE 7 exposure factors), rain, street runoff, river and landslide timelines,
  plus the times each threat arrives.
- **Units:** English uses mph, inches and miles. Spanish uses km/h, mm and km.

## Rebuild

```bash
W=/tmp/simon-map && mkdir -p $W/goes $W/osm $W/raw
pip install h5py scipy numpy pillow
# satellite: mesoscale band 13 + rain rate (scripts in the session log fetch these from noaa-goes18 on AWS)
#   $W/goes/ir/*CMIPM2-M6C13*.nc, $W/goes/rr/*RRQPEF*.nc, $W/goes/fd/*CMIPF-M6C13*.nc (latest full disk)
python3 tools/process_sat.py $W/goes $W/mapwork            # eye fixes, motion, IR frames, storm-relative rain
python3 ../tools/nhc_parse.py $W/nhc_raw $W/nhc.json       # NHC TCP/TCM/PWS
# terrain: AWS terrarium tiles z8 -> $W/tiles_reg, z12 -> $W/tiles_ws, z13 -> $W/tiles
# streets/water: Overpass JSON in $W/osm, OSM API extracts in $W/osm/zr_api.xml and $W/raw/osm__*.xml
python3 tools/build_map.py $W $W/mapwork/map.json          # tracks, building series, catchments
python3 tools/build_layers.py $W $W/mapwork/layers         # base images, vector layers
tools/stage.sh $W && python3 tools/build_page.py
```

Not an official forecast. Follow Protección Civil Jalisco, SMN-CONAGUA and the NHC.
