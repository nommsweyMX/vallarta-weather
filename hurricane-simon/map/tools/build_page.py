"""Inject map.json, layers.json and the images (as data URIs) into src/page.html.
Writes hurricane-simon/map/index.html (full document) and, optionally, a bare fragment (argv[1])
for hosts that supply their own <html>/<head>/<body> skeleton."""
import json, os, sys, glob, base64
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); DATA = os.path.join(ROOT, 'data')
src = open(os.path.join(ROOT, 'src', 'page.html'), encoding='utf-8').read()
J = lambda f: json.dumps(json.load(open(os.path.join(DATA, f), encoding='utf-8')), separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
imgs = {}
for f in sorted(glob.glob(os.path.join(DATA, 'img', '*'))):
    name = os.path.basename(f); key = name if name.startswith('ir') else os.path.splitext(name)[0]
    mime = 'image/webp' if f.endswith('.webp') else 'image/png'
    imgs[key] = f'data:{mime};base64,' + base64.b64encode(open(f, 'rb').read()).decode()
mp = json.load(open(os.path.join(DATA, 'map.json')))
missing = [f for f in mp['ir']['frames'] if f not in imgs]
assert not missing, ('missing IR frames', missing[:3])
frag = src.replace('__MAP_JSON__', J('map.json')).replace('__LAYERS_JSON__', J('layers.json')).replace('__IMG_JSON__', json.dumps(imgs, separators=(',', ':')))
assert '__MAP_JSON__' not in frag and '__LAYERS_JSON__' not in frag and '__IMG_JSON__' not in frag
cut = frag.index('</style>') + len('</style>')
head, body = frag[:cut], frag[cut:]
doc = ('<!doctype html>\n<html lang="en" data-lang="both">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       '<meta name="description" content="Hurricane Simon over Puerto Vallarta: observed GOES-18 satellite loop, extrapolated wind and rain on a street map, and when the wind, flood and landslide threats reach three buildings. English (imperial) and Spanish (metric).">\n'
       + head + '\n</head>\n<body>\n' + body + '\n</body>\n</html>\n')
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(doc)
if len(sys.argv) > 1:   # hosted copy: the sibling page is published separately, so link to it directly
    sib = sys.argv[2] if len(sys.argv) > 2 else None
    open(sys.argv[1], 'w', encoding='utf-8').write(frag.replace('<a href="../">', f'<a href="{sib}">') if sib else frag)
print('map/index.html', len(doc), 'bytes', '| fragment' if len(sys.argv) > 1 else '')
