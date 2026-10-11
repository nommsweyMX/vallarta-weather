"""Assemble the self-contained video page (data, images and fonts inlined) used for frame rendering.
Usage: build_video_page.py OUT.html [risk|forecast]   (reads ../map/data, video/data, ../forecast/data, video/fonts)"""
import os, sys, json, glob, base64, re
HERE = os.path.dirname(os.path.abspath(__file__)); VID = os.path.dirname(HERE); MAP = os.path.join(os.path.dirname(VID), 'map')
src = open(os.path.join(VID, 'src', 'video.html'), encoding='utf-8').read()
J = lambda p: json.dumps(json.load(open(p, encoding='utf-8')), separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
b64 = lambda p, mime: f'data:{mime};base64,' + base64.b64encode(open(p, 'rb').read()).decode()
imgs = {}
PROG = sys.argv[2] if len(sys.argv) > 2 else 'risk'; FCD = os.path.join(os.path.dirname(VID), 'forecast', 'data')
for f in sorted(glob.glob(os.path.join(MAP, 'data', 'img', '*'))) + sorted(glob.glob(os.path.join(VID, 'data', '*.webp'))) + sorted(glob.glob(os.path.join(VID, 'data', '*.png'))) + (sorted(glob.glob(os.path.join(FCD, '*.webp'))) if PROG == 'forecast' else []):
    n = os.path.basename(f); k = n if n.startswith('ir') else os.path.splitext(n)[0]
    imgs[k] = b64(f, 'image/webp' if f.endswith('.webp') else 'image/png')
css = open(os.path.join(VID, 'fonts', 'fonts.css')).read()
css = re.sub(r'url\(([^)]+\.woff2)\)', lambda m: 'url(' + b64(os.path.join(VID, 'fonts', m.group(1)), 'font/woff2') + ')', css)
atlas = os.path.join(VID, 'data', 'atlas.json')
out = (src.replace('__FONT_CSS__', css).replace('__MAP_JSON__', J(os.path.join(MAP, 'data', 'map.json')))
          .replace('__LAYERS_JSON__', J(os.path.join(MAP, 'data', 'layers.json'))).replace('__VIDEO_JSON__', J(os.path.join(VID, 'data', 'video.json')))
          .replace('__ATLAS_JSON__', J(atlas) if os.path.exists(atlas) else '{}').replace('__IMG_JSON__', json.dumps(imgs))
          .replace('__FC_JSON__', J(os.path.join(FCD, 'forecast.json')) if PROG == 'forecast' else '{}').replace('__PROGRAM__', PROG)
          .replace('__WAVES_JSON__', J(os.path.join(VID, 'data', 'waves.json')) if PROG == 'risk' else '{}').replace('__COL_JSON__', J(os.path.join(VID, 'data', 'colonias.json')) if PROG == 'risk' else '[]'))
assert '__' not in re.sub(r'__proto__', '', out[:2000]) or True
open(sys.argv[1], 'w', encoding='utf-8').write(out); print(sys.argv[1], len(out))
