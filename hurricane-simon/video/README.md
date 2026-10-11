# Simon y Vallarta · two explainer videos

Two calm, bilingual videos for YouTube, built from one template (`src/video.html`) with a program switch. On-screen text is
Spanish (metric) above English (imperial). Spanish and English captions (`.srt`) and a ready-to-paste YouTube description are
generated for each.

**1 · `forecast`: Simon, the forecast without the hype (about 3 minutes).** Where Simon came from (NHC best track, coloured by
category, with an intensity chart); where it is going (official NHC track and 2026 cone, with the satellite image moved along the
track and faded to the forecast strength: a schematic, not a cloud forecast); why the forecast keeps changing (steering, model
tracks and intensity guidance); when we will know (cone radii as the storm nears); what is most likely now (NHC wind odds for
Puerto Vallarta, the hurricane warning, the SMN forecast); and why "200-knot winds" is not happening.

**2 · `risk`: Puerto Vallarta, why your area is at risk (about 8½ minutes).** The four hazards explained with the Puerto Vallarta
2024 hazard and risk atlas and CENAPRED's national risk atlas: an overview map; water from the rivers (Pitillal, Cuale, Ameca),
from city streets and from the sea; waves over the bay's bathymetry (wave-ray refraction, schematic); wind with height, slopes and
buildings; landslides; three buildings (Amapas 8th floor, Emiliano Zapata 3rd floor, El Pitillal street level); and, at the end,
what Simon means for these risks.

Numbers and times are read from `../map/data/map.json` (same pipeline as the map page) and, for the forecast program,
`../forecast/data/forecast.json`, so a data refresh updates both videos.

## Build

```bash
python3 ../forecast/tools/forecast_data.py $W ../forecast/data   # best track, NHC forecast, cone, model aids (WORK/atcf, WORK/nhc.json)
python3 tools/build_video_data.py $W data                        # catchment view, drainage, terrain profile (WORK dir as for map/tools)
python3 tools/waves.py $W data; python3 tools/lowcoast.py $W data/lowcoast_city.png; python3 tools/colonias.py Colonias_DU_PV.shp data/colonias.json
python3 tools/build_video_page.py /tmp/forecast.html forecast    # inline data, images and fonts (or: risk)
node tools/render.js /tmp/forecast.html simon-forecast.mp4 30 3  # 1080p30 H.264 + silent AAC, rendered in 3 parallel segments
node tools/captions.js /tmp/forecast.html . simon-forecast       # simon-forecast.es.srt, .en.srt, .chapters.json
python3 tools/youtube.py forecast simon-forecast.chapters.json ../map/data/map.json data/atlas.json youtube-forecast.txt
```

Fonts: Red Hat Display/Text/Mono (SIL Open Font License, `fonts/OFL.txt`).
Not an official forecast. Follow SMN-CONAGUA, the NHC and Protección Civil of Puerto Vallarta and Jalisco.
