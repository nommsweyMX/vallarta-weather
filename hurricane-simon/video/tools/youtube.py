"""Write the YouTube title, description (with chapters) and tags for either video.
Usage: youtube.py risk|forecast CHAPTERS.json MAP.json ATLAS.json OUT.txt"""
import sys, json, datetime as dt
prog, ch, mp, atlas, out = sys.argv[1], json.load(open(sys.argv[2])), json.load(open(sys.argv[3])), json.load(open(sys.argv[4])), sys.argv[5]
t = dt.datetime.strptime(mp['t_obs'], '%Y-%m-%dT%H:%MZ') - dt.timedelta(hours=6)
DES = ['dom', 'lun', 'mar', 'mié', 'jue', 'vie', 'sáb'][(t.weekday() + 1) % 7]; DEN = t.strftime('%a')
h12 = (t.hour % 12 or 12, 'am' if t.hour < 12 else 'pm')
asof_es = f'{DES} {t.day} oct {t:%H:%M} (hora del centro)'; asof_en = f'{DEN} Oct {t.day}, {h12[0]}:{t:%M} {h12[1]} CST'
adv = mp['advisory']['num']
names = {'title': ('Inicio', 'Start'), 'f-title': ('Inicio', 'Start'), 'credits': ('Fuentes', 'Sources')}
def name(c):
    if c['id'] in names: return names[c['id']]
    return tuple(c['title']) if c.get('title') else (c['id'], c['id'])
chap = '\n'.join(f"{c['t']} {name(c)[0]} / {name(c)[1]}" for c in ch)
DISCLAIMER_ES = f'Datos al {asof_es}, boletín {adv} del NHC. NO es un pronóstico oficial: sigue al SMN-CONAGUA, al Centro Nacional de Huracanes (NHC) y a Protección Civil de Puerto Vallarta y de Jalisco. Emergencias: 911.'
DISCLAIMER_EN = f'Data as of {asof_en}, NHC advisory {adv}. This is NOT an official forecast: follow SMN-CONAGUA, the National Hurricane Center (NHC) and Protección Civil of Puerto Vallarta and Jalisco. Emergencies: 911.'

if prog == 'forecast':
    title = 'Huracán Simon: el pronóstico para Puerto Vallarta, sin exagerar | Hurricane Simon: the Puerto Vallarta forecast, without the hype'
    es = ('Dónde estuvo Simon, a dónde va según el NHC, por qué cambia el pronóstico, cuándo sabremos con más certeza por dónde pasa y qué es lo más probable para Vallarta. '
          'También: por qué no habrá “vientos de 200 nudos” (ningún huracán medido los ha tenido; el récord es Patricia, 2015, con 185). '
          'La imagen de satélite se atenúa conforme el pronóstico debilita la tormenta: es un esquema, no un pronóstico de nubes.')
    en = ('Where Simon has been, where the NHC expects it to go, why the forecast keeps changing, when we will know its path with more certainty, and what is most likely for Vallarta. '
          'Also: why there will be no “200-knot winds” (no measured hurricane has had them; the record is Patricia, 2015, at 185). '
          'The satellite image fades as the forecast weakens the storm: a schematic, not a cloud forecast.')
    src = ['National Hurricane Center (NHC): public advisory, forecast discussion and wind speed probabilities, advisory ' + adv,
           'NHC: 2026 cone of uncertainty radii (eastern North Pacific); best track and model guidance (ATCF)',
           'SMN-CONAGUA: tropical cyclone advisory for Jalisco (rain, waves and wind on the coast)',
           'NOAA GOES-18 ABI: infrared band 13 (mesoscale and full disk)', 'NHC Tropical Cyclone Report: Hurricane Patricia (2015)']
    tags = 'huracán Simon, pronóstico, Puerto Vallarta, Jalisco, Nayarit, NHC, SMN, cono de incertidumbre, Hurricane Simon, hurricane forecast, Puerto Vallarta hurricane, Patricia'
else:
    title = 'Puerto Vallarta: por qué tu zona está en riesgo (huracán Simon) | Puerto Vallarta: why your area is at risk (Hurricane Simon)'
    es = ('Las cuatro amenazas de un huracán en Puerto Vallarta, explicadas con el Atlas de Peligros y Riesgos de Puerto Vallarta 2024 y el Atlas Nacional de Riesgos de CENAPRED: '
          'el agua (ríos Pitillal, Cuale y Ameca, calles que se inundan y el mar), las olas (cómo el fondo de Bahía de Banderas decide dónde llegan las más grandes), '
          'el viento (altura, laderas y edificios) y los deslaves. Incluye lo que pasó con Nora (2021) y Lidia (2023), tres lugares concretos (Amapas, Emiliano Zapata y El Pitillal) '
          'y, al final, qué significa Simon para estos riesgos. La categoría no te dice qué hacer en tu calle: tu lugar sí.')
    en = ('The four hurricane hazards in Puerto Vallarta, explained with the Puerto Vallarta 2024 hazard and risk atlas and CENAPRED’s national risk atlas: '
          'water (the Pitillal, Cuale and Ameca rivers, flooded streets and the sea), waves (how the floor of Banderas Bay decides where the biggest ones land), '
          'wind (height, slopes and buildings) and landslides. It covers what happened in Nora (2021) and Lidia (2023), three specific places (Amapas, Emiliano Zapata and El Pitillal) '
          'and, at the end, what Simon means for these risks. The category doesn’t tell you what to do on your street: where you are does.')
    src = ['NOAA GOES-18 ABI: infrared band 13 and rain-rate product (RRQPE)', 'National Hurricane Center (NHC), advisory ' + adv] + atlas.get('sources', []) + [
           'Bathymetry and terrain: AWS Terrain Tiles; streets, canals, buildings and coastline © OpenStreetMap contributors (ODbL)',
           'Methods: satellite storm-relative rainfall (NOAA TRaP), scaled to the SMN rain forecast; R-CLIPER and Kaplan & DeMaria inland decay; ASCE 7 exposure factors; Caine (1980) landslide threshold; linear wave-ray refraction (schematic)']
    tags = 'Puerto Vallarta, huracán Simon, Atlas de Riesgos, CENAPRED, Protección Civil, Río Pitillal, Río Cuale, Río Ameca, Bahía de Banderas, oleaje, deslaves, inundaciones, Hurricane Simon, flooding, landslides, storm surge'

txt = f"""TÍTULO / TITLE
{title}

DESCRIPCIÓN / DESCRIPTION
[ES] {es}
{DISCLAIMER_ES}

[EN] {en}
{DISCLAIMER_EN}
Text on screen: Spanish (metric units) and English (imperial units). Captions: Spanish and English (.srt files).

CAPÍTULOS / CHAPTERS
{chap}

FUENTES / SOURCES
""" + ''.join(f'- {s}\n' for s in src) + f"""
ETIQUETAS / TAGS
{tags}
"""
open(out, 'w', encoding='utf-8').write(txt); print('wrote', out)
