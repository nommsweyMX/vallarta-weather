"""Assemble the self-contained graphics page (data, images and fonts inlined).
Usage: build_graphics.py OUT.html [SMN_AVISO_NUMBER]   (reads bay/data, ../map/data, ../video/data, ../forecast/data, ../video/fonts)"""
import os, sys, json, base64, re
HERE = os.path.dirname(os.path.abspath(__file__)); BAY = os.path.dirname(HERE); ROOT = os.path.dirname(BAY)
MAP, VID, FCD = os.path.join(ROOT, 'map', 'data'), os.path.join(ROOT, 'video'), os.path.join(ROOT, 'forecast', 'data')
src = open(os.path.join(BAY, 'src', 'graphics.html'), encoding='utf-8').read()
J = lambda p: json.dumps(json.load(open(p, encoding='utf-8')), separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
b64 = lambda p, mime: f'data:{mime};base64,' + base64.b64encode(open(p, 'rb').read()).decode()
imgs = {'bay_base': b64(os.path.join(VID, 'data', 'bay_base.webp'), 'image/webp'), 'base_city_dark': b64(os.path.join(MAP, 'img', 'base_city_dark.webp'), 'image/webp'),
        'reg_base': b64(os.path.join(MAP, 'img', 'reg_base.webp'), 'image/webp')}
for k in ('atlas_flood_city', 'atlas_slide_city', 'lowcoast_city'):
    p = os.path.join(VID, 'data', k + '.png')
    if os.path.exists(p): imgs[k] = b64(p, 'image/png')
css = open(os.path.join(VID, 'fonts', 'fonts.css')).read()
css = re.sub(r'url\(([^)]+\.woff2)\)', lambda m: 'url(' + b64(os.path.join(VID, 'fonts', m.group(1)), 'font/woff2') + ')', css)
fc = json.load(open(os.path.join(FCD, 'forecast.json'), encoding='utf-8')); fc = dict(cycle=fc['cycle'], tracks=fc['tracks'])
out = (src.replace('__FONT_CSS__', css).replace('__BAY_JSON__', J(os.path.join(BAY, 'data', 'bay.json'))).replace('__MODELS_JSON__', J(os.path.join(BAY, 'data', 'models.json')))
          .replace('__LAYERS_JSON__', J(os.path.join(MAP, 'layers.json'))).replace('__IMG_JSON__', json.dumps(imgs)).replace('__FC_JSON__', json.dumps(fc, separators=(',', ':'), ensure_ascii=False)).replace('__VERIFY_JSON__', J(os.path.join(BAY, 'data', 'verify.json'))).replace('__SMN_AV__', sys.argv[2] if len(sys.argv) > 2 else '30'))
open(sys.argv[1], 'w', encoding='utf-8').write(out); print(sys.argv[1], len(out))
