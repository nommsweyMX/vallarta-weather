#!/bin/sh
# copy processed products from a work directory into map/data (map.json, layers.json, images)
set -e
W=$1; D=$(dirname "$0")/../data
mkdir -p "$D/img"; rm -f "$D"/img/*
cp "$W/mapwork/map.json" "$D/map.json"; cp "$W/mapwork/layers/layers.json" "$D/layers.json"
cp "$W"/mapwork/layers/*.webp "$W"/mapwork/layers/slope_*.png "$D/img/"
python3 - "$W" "$D" <<'PY'
import json, shutil, sys
W, D = sys.argv[1], sys.argv[2]
ir = json.load(open(W + '/mapwork/map.json'))['ir']
for f in ir['frames'] + ([ir['ext']['file']] + [l['file'] for l in ir['ext'].get('levels', [])] if ir.get('ext') else []): shutil.copy(W + '/mapwork/frames/' + f, D + '/img/' + f)
PY
ls "$D/img" | wc -l
