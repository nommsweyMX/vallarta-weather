# Simon, hour by hour · Simon, hora por hora

Hour-by-hour rain forecast for Hurricane Simon (EP20, October 2026) at three Puerto Vallarta
addresses, from Saturday 10 Oct 12:00 to Monday 12 Oct 12:00 CST (UTC−6):

| Address | Point used | Notes |
|---|---|---|
| Amapas at Cafeto & Olas Altas | 20.5984, −105.2382 | Zona Romántica, 90 m from Playa Los Muertos |
| Cinco de Mayo & Calle España, El Pitillal | 20.6477, −105.2087 | OSM node 5612797225, 160 m from the Río Pitillal |
| Francisco Rodríguez 336, C.P. 48380 | ≈20.6012, −105.2358 | OSM spells it Francisca Rodríguez; no house numbers mapped, position approximate |

`index.html` is a single self-contained page (data inlined, no build step to view). It animates
the 48 hours in three panes: **worst case** (wettest model at each address), **model average**
(hour-by-hour mean of all models) and **best case** (driest model), or one pane per address.
English, Spanish, or both at once.

## Data

- **Global models** via [Open-Meteo](https://open-meteo.com/), nearest grid cell
  (`cell_selection=nearest`; the default land-cell choice snapped ECMWF 12 km north):
  ECMWF IFS, UK Met Office 10 km, ICON, GFS, GEM, CMA GRAPES, ARPEGE, JMA GSM, ECMWF AIFS, AI-GFS.
- **Hurricane models** HAFS-A and HAFS-B from NOAA's open-data bucket
  (`noaa-nws-hafs-pds`), byte-range reads of APCP/PRMSL/WIND from the fixed 6 km **parent** grid.
  The 2 km moving storm nest is not used: its accumulations are storm-relative, so a fixed
  point's running total falls over time.
- **Ensembles** (212 members: ECMWF 51, ECMWF AIFS 51, ICON 40, GFS 31, GEM 21, UK Met Office 18)
  for the odds section.
- **NHC** products are parsed by `tools/nhc_parse.py` (public advisory, forecast advisory with
  34/50/64-kt wind radii, Puerto Vallarta wind probabilities). The alert, track table, odds and the
  worst-case wind (an estimate at each address if the center follows the NHC track exactly) come
  from them.
- **Threat levels** (wind, rain per hour, 24-h rain, surge and waves, Río Pitillal, street runoff)
  use the thresholds listed in the page's "How this was made" section.

## Refresh

```bash
cd hurricane-simon
D=/tmp/simon && mkdir -p $D/om $D/ens $D/hafs
python3 tools/fetch_om.py  $D/om  ecmwf_ifs,ukmo_global_deterministic_10km,icon_global,gfs_global,gem_global,cma_grapes_global,meteofrance_arpege_world,jma_gsm,ecmwf_aifs025_single,ncep_aigfs025,bom_access_global,kma_gdps,gfs_graphcast025
python3 tools/fetch_ens.py $D/ens ecmwf_ifs025,gfs025,icon_global_eps,gem_global,ecmwf_aifs025,ukmo_global_ensemble_20km
pip install pygrib numpy   # HAFS GRIB decoding
HAFS_DOM=parent python3 tools/fetch_hafs.py hfsa 2026101012 $D/hafs 6 54    # cycle, first/last forecast hour of the window
HAFS_DOM=parent python3 tools/fetch_hafs.py hfsb 2026101012 $D/hafs 6 54
mkdir -p $D/waves && python3 tools/fetch_waves.py hfsa 2026101012 $D/waves 6 54
# NHC: save TCPEP5, TCMEP5, PWSEP5 from https://www.nhc.noaa.gov/text/MIA<product>.shtml into $D/nhc_raw, then
python3 tools/nhc_parse.py $D/nhc_raw $D/nhc.json
python3 tools/build_data.py $D data/forecast.json
python3 tools/build_page.py
```

The window dates are fixed in `fetch_*.py` and `build_data.py`. For a newer HAFS cycle, the
window still starts at 18 UTC 10 Oct: with cycle 12Z use forecast hours `6 54`, with 18Z `0 48`.

Not an official forecast. Follow Protección Civil, SMN-CONAGUA and the NHC.
