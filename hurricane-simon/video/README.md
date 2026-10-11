# Simon y Vallarta · explainer video

A calm, bilingual explainer, about 4 minutes long, made for YouTube. Its message: the category and the headlines don't tell you what to do on
your street; your risk depends on where you are, and Vallarta's mountains shape it. On-screen text is Spanish (metric) above
English (imperial). Spanish and English captions (`.srt`) and a ready-to-paste YouTube description are generated alongside.

Scenes: the observed GOES-18 loop and where Simon is; why the category is not the point; how the Sierra changes the wind and
rain (terrain cross-section); how mountain rain reaches the Pitillal and Cuale rivers (catchments traced from terrain data);
steep slopes; what the risk atlas maps; three buildings (Amapas 8th floor, Emiliano Zapata 3rd floor, El Pitillal street
level) with their threat timelines; a summary timeline; what to do; sources.

All numbers and times are read from `../map/data/map.json` (same pipeline as the map page), so a data refresh updates the video.

## Build

```bash
python3 tools/build_video_data.py $W data             # catchment view, drainage, terrain profile (WORK dir as for map/tools)
python3 tools/build_video_page.py /tmp/video.html      # inline data, images and fonts
node tools/render.js /tmp/video.html simon-vallarta.mp4 30 3   # 1080p30 H.264 + silent AAC, rendered in 3 parallel segments
node tools/captions.js /tmp/video.html .               # simon-vallarta.es.srt, simon-vallarta.en.srt, chapters.json
python3 tools/youtube.py chapters.json ../map/data/map.json data/atlas.json youtube.txt
```

Fonts: Red Hat Display/Text/Mono (SIL Open Font License, `fonts/OFL.txt`).
Not an official forecast. Follow Protección Civil Jalisco, SMN-CONAGUA and the NHC.
