# vallarta-weather

Weather & hazard tooling for Puerto Vallarta / Bahía de Banderas (PVR), built as a single-file
web app: the **WHY-ARTA Hazard Atlas**, fronted by **Vallarta View** — tonight's storm outlook
in plain words for regular humans, with the full science underneath.

> ¿WHY-arta? · Educational, not official guidance. In an emergency, Protección Civil rules.

## Publish (GitHub Pages)

`index.html` at the repo root is the atlas, ready for Pages:

```bash
git clone https://github.com/<you>/vallarta-weather && cd vallarta-weather
# drop this bundle's contents in, then:
git add -A && git commit -m "Publish: Banderas Hazard Atlas (weather cut)" && git push
```

Then once in the repo: **Settings → Pages → Deploy from a branch → `main` / root**.
The site lands at `https://<you>.github.io/vallarta-weather/`. The `.nojekyll` file keeps
GitHub from running the HTML through Jekyll.

## Quick start

Open `why-arta-hazard-atlas.html` in any modern browser. No build, no server, no dependencies
to install — everything is inline except two runtime conveniences that need an internet
connection:

- **Street maps** — Leaflet 1.9.4 + OpenStreetMap/OpenTopoMap tiles (CDN).
- **Auto-log model terms** — Open-Meteo fetch (see *Live data* below).

Offline, both degrade honestly: maps show a "needs internet" note, and the Afternoon Pop tab
keeps its last baked log with a red **STALE** badge instead of pretending it's current.

## What's inside

| Tab | What it is |
|---|---|
| **Vallarta View** | The plain-language front door: a one-sentence verdict for tonight, WHERE / HOW MUCH (inches) / WHEN cards, and the warning zones as live-colored circles on a real street map. |
| Science | Tectonics & monitoring — how this coast is built and watched. |
| Evacuation | Tsunami natural-warning signs + high-ground terrain map. |
| Flooding | Cuale, Pitillal & Ameca river mouths, flood-point viewer links. |
| Sediment | Ground response — why downtown shakes harder than the hills. |
| Resorts / Inland | Month-by-month climate scoring across Mexican cities. |
| Moisture (FG №06) | The meteorologist's lookbook — annual & diurnal rain rhythm, PWAT thresholds. |
| **The Afternoon Pop (FG №07)** | The daily storm check-in: a 6-term scorer that calls the night's corridor, paints a derived warning map, and feeds the Deluge Index rainfall term. |

Vallarta View and The Afternoon Pop share one state: every chip tapped (or auto-fetched) in
the Pop log re-renders the View's verdict, cards, and map circles via a `pop:update` event on
`window.__popState`.

## Live data

One Open-Meteo call per fresh day (or on the **Fetch today's model terms** button), point
20.62 N, −105.23 W, tz `America/Mexico_City`:

- `wind_*_700hPa` / `wind_*_500hPa` at 14:00 → steering chip (circular mean, binned E–ENE /
  ESE–SE / SW-onshore / ridge-light; <11 km/h ⇒ light).
- `total_column_integrated_water_vapour` at 14:00 → PWAT chip (gracefully skipped if the
  model lacks it).
- `convective_inhibition` 08 h vs 13 h + `cape` → morning-cap chip.
- `precipitation` 18:00→06:00 → Vallarta View's town total in inches, wettest stretch, and
  peak hour.

Eyeball terms stay human on purpose: wave axis (water vapor / NHC EPAC), first towers
(IR satellite vs. the Ameca valley line), and the night nowcast (lightning trend + the
outflow wind at the terrace).

## Repo layout

```
why-arta-hazard-atlas.html   ← the app (canonical, single file)
docs/afternoon-pop-model.md  ← full scoring & mapping spec
docs/CHANGELOG.md            ← version history
legacy/                      ← superseded standalones, kept for the record
```

## Dev notes (read before adding a tab)

The atlas is deliberately one hand-maintained HTML file. House rules learned the hard way:

1. **The `go()` whitelist.** Page switching iterates a hardcoded array —
   `const pages=["home","vview",…]`. A new `<div class="page" id="x">` renders blank until
   its id is added there. This is the #1 gotcha.
2. Add the matching `<button data-go="x">` in the drawer and (optionally) a `.tile` on Home;
   `[data-go]` listeners bind once at load, so markup must exist before the script block.
3. **Scope your CSS** under the page id (`#x .foo{…}`) inside the single `<style>` block;
   global classes (`.eyebrow`, `.lede`, `.note`, `.tile`, `.sub`) are shared house chrome
   (Red Hat Display/Text/Mono, light theme).
4. Per-page init hooks live inside `go()` (`if(id==="x")initX()`); Leaflet maps cache in the
   global `maps` object and call `invalidateSize()` on revisit.
5. **EN/ES toggle** is a trimmed-text-node swap over the `PAIRS` array — add `[en, es]`
   entries for any new nav labels/headers, keyed to the exact text nodes (split fragments
   around `<span>`s count separately). Untranslated strings simply stay EN.
6. Inside SVG, use literal hex colors — CSS `var()` does not resolve in presentation
   attributes.
