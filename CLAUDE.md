# ha-vigia

Home Assistant custom integration (domain `vigia`) for wildfire watch in Northern Portugal. Installed via HACS. Serves its own Lovelace cards.

## Layout

- `custom_components/vigia/`
  - `coordinator.py`: fetching, caching, alerts
  - `sources.py`: feed parsers (IPMA, fogos.pt, FIRMS, EFFIS, Open-Meteo)
  - `water.py`: OSM waterways via Overpass
  - `const.py`: `VERSION`, `BURNT_SEASONS` and other constants
  - `frontend/vigia-card.js`: tile card, map, map card
  - `blueprints/fire_alert.yaml`
- `tests/`: pytest-homeassistant-custom-component

## Tests

Don't install the test deps in a session; it pulls all of Home Assistant and costs a lot of tokens. The `tests` job in `.github/workflows/validate.yaml` runs pytest on every push. Push, then check the run with the GitHub MCP tools (`actions_list` / `get_job_logs`).

Only if CI can't answer the question (e.g. debugging one test interactively), set up locally with uv, since system pip can't build PyRIC:

```
uv venv
uv pip install pytest-homeassistant-custom-component
.venv/bin/pytest
```

## Release

1. Bump the version in all three places: `VERSION` in `const.py`, `manifest.json`, and `frontend/vigia-card.js`.
2. Push and confirm the Validate workflow is green.
3. Merge to `main`. No tags or GitHub releases (cloud sessions get 403); HACS tracks commits on `main`.
4. In Home Assistant: HACS update information + download for repo id `1411579568`, then restart HA.

The integration registers its card resource as `/vigia_static/vigia-card.js?v=<version>`. Never edit that resource by hand; the version bump is what makes phones and the tablet load the new card. After a restart the HA connection is often down for a few minutes; polling `/vigia_static/vigia-card.js` shows when it is back.

## Sources and rules

- IPMA fire risk (set by the `ipma_concelho` option) and weather warnings.
- fogos.pt incidents. Terms: show "Source: Fogos.pt", no monetisation, never the sole source for an alert. Send `User-Agent: Vigia/<version> (https://github.com/eyeofeska/ha-vigia)`. Anonymous use gets rate-limited (429); with a key Vigia polls every 10 min, without one every 15 min with back-off.
- NASA FIRMS VIIRS hotspots, only when a map key is set.
- EFFIS burnt areas: WFS layer `ms:modis.ba.poly`, `outputformat=geojson`. EFFIS returns lat,lon order; Vigia swaps it. `BURNT_SEASONS = 3` keeps this year plus the two before, each area tagged with `year`.
- Open-Meteo wind grid; wind at home from the HA weather entity.
- API keys (FIRMS, fogos.pt) are entered only in the integration's Configure dialog. Never put a key in code, tests, fixtures, docs or commits. The store keeps only a 12-character SHA-256 fingerprint of the fogos.pt key; a new or removed key clears fogos.pt back-off.
- Changing home, radius or concelho clears the cached data.

## Alerts

- Event `vigia_alert`, one per fire. Repeats only on a higher tier or when the fire is 1 km+ closer.
- The blueprint builds the notify service name from the phone's device name, and its notify call has `continue_on_error`. A re-registered phone makes alerts fail silently, so check automation traces after any phone change.

## Map

- Keyless Esri tiles: `Canvas/World_Light_Gray_Base` tinted sage green by a CSS filter, `Elevation/World_Hillshade` multiplied, `Canvas/World_Light_Gray_Reference` labels. CARTO now needs an API key; a topo base was judged too busy.
- Waterways: drawn in blue on a canvas in pane "water" (z 330, under burnt areas and labels), fetched once via websocket `vigia/water`. Stored thinned and delta-encoded (1e-4° integers) in its own store, refreshed every 30 days (retry after 6 h on failure). Overpass: overpass-api.de, kumi mirror as fallback.
- Burnt seasons: chips top-right toggle each season, remembered per device in localStorage `vigia:burnt-seasons` (offsets from this year, default this year only). Newest darkest, older drawn underneath.
- Fire footprints: each VIIRS detection adds a Gaussian bump sized to its real pixel (FIRMS scan/track); outline is the half-height contour (marching squares on a 40 m grid, Chaikin smoothing), detections within 1.2 km group into one fire, a world-anchored noise warp roughens the edge, age bands nest like growth rings. Terrain is deliberately not used (it would be a spread guess).

## Previewing the card headless

- Playwright with Chromium. Serve the page from a routed fake origin (e.g. `http://vigia.test/`) so localStorage works, and route the cdnjs Leaflet URLs to an npm copy of `leaflet@1.9.4`.
- Test touch at phone size with CDP `Input.dispatchTouchEvent`. A past bug: a hidden layer whose `display:flex` overrode `[hidden]` covered the map and ate touches.

## Writing

README, UI strings and commit messages: no em dashes, no "it's not X, it's Y" phrasing, no unhedged superlatives.
