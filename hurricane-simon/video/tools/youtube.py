"""Write the YouTube title, description (with chapters) and tags for the explainer.
Usage: youtube.py CHAPTERS.json MAP.json [ATLAS.json] OUT.txt"""
import sys, json, datetime as dt
ch = json.load(open(sys.argv[1])); mp = json.load(open(sys.argv[2]))
atlas = json.load(open(sys.argv[3])) if len(sys.argv) > 4 else {}
out = sys.argv[-1]
t = dt.datetime.strptime(mp['t_obs'], '%Y-%m-%dT%H:%MZ') - dt.timedelta(hours=6)
DES = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'][(t.weekday() + 1) % 7]; DEN = t.strftime('%a')
h12 = (t.hour % 12 or 12, 'am' if t.hour < 12 else 'pm')
asof_es = f'{DES} {t.day} oct {t:%H:%M} (hora del centro)'; asof_en = f'{DEN} Oct {t.day}, {h12[0]}:{t:%M} {h12[1]} CST'
names = {'title': ('Inicio', 'Start'), 'now': ('Dónde está Simon', 'Where Simon is now'), 'category': ('Más allá de la categoría', 'Beyond the category'),
         'mountains': ('Las montañas cambian la tormenta', 'How the mountains change the storm'), 'catchments': ('De la sierra a tu calle', 'From the mountains to your street'),
         'slopes': ('Laderas empinadas', 'Steep slopes'), 'atlas': ('Lo que dice el Atlas de Riesgos', 'What the risk atlas says'), 'amapas': ('Amapas, 8.º piso', 'Amapas, 8th floor'),
         'ezapata': ('Emiliano Zapata, 3.er piso', 'Emiliano Zapata, 3rd floor'), 'pitillal': ('El Pitillal, nivel de calle', 'El Pitillal, street level'),
         'timeline': ('El domingo, hora por hora', 'Sunday, hour by hour'), 'todo': ('Qué hacer', 'What to do'), 'credits': ('Fuentes', 'Sources')}
chap = '\n'.join(f"{c['t']} {names.get(c['id'], (c['id'], c['id']))[0]} / {names.get(c['id'], (c['id'], c['id']))[1]}" for c in ch)
src = atlas.get('sources', [])
txt = f"""TÍTULO / TITLE
Huracán Simon y Puerto Vallarta: tu riesgo depende de dónde estás | Hurricane Simon and Puerto Vallarta: your risk depends on where you are

DESCRIPCIÓN / DESCRIPTION
[ES] Explicación tranquila, sin exageraciones, de cómo puede afectar el huracán Simon a Puerto Vallarta. La idea central: la categoría y los titulares no te dicen qué hacer en tu calle. Lo que importa es tu lugar: si estás cerca de un río, bajo una ladera o en un piso alto. El video muestra imágenes reales del satélite GOES-18, cómo la Sierra cambia el viento y la lluvia, cómo el agua de la sierra llega a los ríos Pitillal y Cuale horas después, y qué significa para tres lugares de Vallarta (Amapas, Emiliano Zapata y El Pitillal).
Datos al {asof_es}. Los horarios son estimaciones y cambiarán con cada boletín. NO es un pronóstico oficial: sigue a Protección Civil de Puerto Vallarta y de Jalisco, al SMN-CONAGUA y al Centro Nacional de Huracanes (NHC). Emergencias: 911.

[EN] A calm, no-hype explainer of how Hurricane Simon may affect Puerto Vallarta. The main point: the category and the headlines don't tell you what to do on your street. What matters is where you are: near a river, below a slope, or on a high floor. The video shows real GOES-18 satellite images, how the Sierra changes the wind and rain, how mountain rain reaches the Pitillal and Cuale rivers hours later, and what it means for three places in Vallarta (Amapas, Emiliano Zapata and El Pitillal).
Data as of {asof_en}. Times are estimates and will change with each advisory. This is NOT an official forecast: follow Protección Civil of Puerto Vallarta and Jalisco, SMN-CONAGUA and the National Hurricane Center (NHC). Emergencies: 911.
Text on screen: Spanish (metric units) and English (imperial units). Captions: Spanish and English.

CAPÍTULOS / CHAPTERS
{chap}

FUENTES / SOURCES
- NOAA GOES-18 ABI: infrared band 13 (mesoscale sector) and rain-rate product (RRQPE)
- National Hurricane Center (NHC), advisory {mp['advisory']['num']}
""" + ''.join(f'- {s}\n' for s in src) + """- Terrain: AWS Terrain Tiles; streets, buildings and coastline © OpenStreetMap contributors (ODbL)
- Methods: satellite-based storm-relative rainfall (NOAA TRaP method), R-CLIPER intensity scaling, Kaplan & DeMaria inland decay, ASCE 7 exposure factors, Caine (1980) landslide threshold

ETIQUETAS / TAGS
huracán Simon, Puerto Vallarta, Bahía de Banderas, Jalisco, Protección Civil, Río Pitillal, Río Cuale, deslaves, inundaciones, Hurricane Simon, Puerto Vallarta hurricane, flooding, landslides, GOES-18
"""
open(out, 'w', encoding='utf-8').write(txt); print('wrote', out)
