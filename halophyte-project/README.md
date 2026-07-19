# Halophyte Field Match — export

Everything needed to run this standalone or fold it into another project.

```
halophyte-project/
├── app/
│   └── halophyte_field_match.html   ← the working app (self-contained, open in any browser)
├── data/
│   ├── plants_source.csv            ← original uploaded CSV, untouched
│   └── plants_cleaned.json          ← cleaned/parsed data the app reads
├── scripts/
│   └── clean_data.py                ← regenerates plants_cleaned.json from the CSV
└── design-system/
    ├── DESIGN_SYSTEM.md             ← full write-up of the palette/type/component choices
    ├── tokens.css                   ← just the colors + fonts, standalone
    └── components.css               ← full component styles (panel, chips, cards, gauge)
```

## Running it as-is

`app/halophyte_field_match.html` is fully self-contained — the cleaned
data is embedded directly in the file as a `<script>` block, so it opens
and works from a double-click with no server, build step, or network
calls (aside from loading the two Google Fonts used).

## Integrating into an existing project

- **As a standalone page/route:** copy `app/halophyte_field_match.html` in
  as-is and link to it, or lift the `<script>` (filter logic + render
  functions starting at `const PLANTS = ...`) into a component in your
  existing framework — it's plain DOM/JS with no dependencies, so it
  drops into a React/Vue wrapper as an effect-driven render function with
  minimal changes.
- **As a data source:** `data/plants_cleaned.json` is a flat array of
  1,581 objects (see the field key inside `scripts/clean_data.py`'s
  docstring / column mapping) — use it directly if you want to build your
  own UI around the same data instead of this one.
- **If the source CSV changes:** re-run
  `python3 scripts/clean_data.py data/plants_source.csv data/plants_cleaned.json`
  to regenerate the cleaned JSON, then re-embed it in the HTML (or point
  your own app at the JSON file instead of embedding it).

## Reusing the UI design elsewhere

See `design-system/DESIGN_SYSTEM.md` — it explains not just the hex
values and fonts but *why* each choice was made, plus a component-by-
component breakdown of what's reusable as-is vs. what should change per
project. `tokens.css` + `components.css` are copy-pasteable starting
points.

## Data field reference (plants_cleaned.json)

| Key | Meaning |
|---|---|
| `id` | Original sequence number from the source CSV |
| `grp` | Ferns / Gymnosperms / Angiosperms |
| `fam`, `gen` | Family, genus (English) |
| `name`, `sci` | English plant name, scientific name |
| `dist`, `hab` | Distribution and habitat, free text |
| `life`, `ht` | Life form, height |
| `halo` | Salt-tolerance strategy (excluder / secretor / euhalophyte / neo-halophyte) |
| `eco` | Array of site-character tags (Xerophytic, Aquatic, Psammophytic, etc.) |
| `sal` | Max salinity tolerance in mM (numeric, `null` if not on record) |
| `salEst` | `true` if that value is an estimate rather than lab-measured |
| `path` | Photosynthetic pathway (C3 / C4 / CAM) |
| `uses` | Array of normalized use categories |
| `inv` | `true` if flagged as invasive/naturalized/weed in the source |
