"""Inject forecast.json into src/page.html.
Writes hurricane-simon/index.html (full document, for GitHub Pages) and, optionally,
a bare fragment for hosts that supply their own <html>/<head>/<body> skeleton."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = open(os.path.join(ROOT, 'src', 'page.html'), encoding='utf-8').read()
data = json.load(open(os.path.join(ROOT, 'data', 'forecast.json')))
blob = json.dumps(data, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
frag = src.replace('__FORECAST_JSON__', blob).replace('__NMOD__', str(data['locs'][0]['n']))
assert '__FORECAST_JSON__' not in frag and '__NMOD__' not in frag
cut = frag.index('</style>') + len('</style>')
head, body = frag[:cut], frag[cut:]
doc = ('<!doctype html>\n<html lang="en" data-lang="both">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       '<meta name="description" content="Hour-by-hour rain, wind and threat forecast for Hurricane Simon at three Puerto Vallarta addresses: worst case, model average and best case, in English and Spanish.">\n'
       + head + '\n</head>\n<body>\n' + body + '\n</body>\n</html>\n')
open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8').write(doc)
if len(sys.argv) > 1:
    open(sys.argv[1], 'w', encoding='utf-8').write(frag)
print('index.html', len(doc), 'bytes', '| fragment' if len(sys.argv) > 1 else '')
