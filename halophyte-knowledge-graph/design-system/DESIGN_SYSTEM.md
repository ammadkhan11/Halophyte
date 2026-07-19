# Field Match design system

This documents the visual language used in `halophyte_field_match.html`, so
you can lift it — palette, type, components — into another project rather
than starting from a template look.

Files in this folder:
- `tokens.css` — colors, fonts, and the two base type roles. Drop this in on
  its own if you just want the palette/typography for something new.
- `components.css` — the full component set (panel, chips, cards, gauge,
  buttons) copied straight from the app. Depends on the variables in
  `tokens.css`.

---

## 1. The brief this was designed for

A scientific reference tool: 1,581 species, filtered down to a shortlist by
numeric criteria (salinity tolerance) plus tag-based criteria (site type,
use, strategy). The design had one job: make dense, technical data feel
navigable and trustworthy — like a well-kept field guide, not a spreadsheet
and not a generic SaaS dashboard.

That brief is *why* the choices below look the way they do. If you reuse
this system for a different subject, keep the token names and structural
patterns, but reconsider the specific colors and copy — see §5.

## 2. Color — 6 named values, each with one job

| Token | Hex | Job |
|---|---|---|
| `--salt` | `#eef0ea` | Page background. Pale mineral grey-green, not the generic warm cream — chosen because the subject (salt flats, salinized ground) is literally pale and mineral. |
| `--card` | `#f7f8f3` | Panel/card surface, one step lighter than the page so content areas read as "raised." |
| `--ink` | `#242923` | Primary text. A near-black with a green cast, not pure black — softer, fits the earthy palette. |
| `--ink-soft` | `#5b6259` | Secondary text — captions, meta lines, labels. |
| `--brack` / `--brack-deep` | `#3f6b63` / `#264c46` | "Brackish" teal — the *primary* interactive color: active chips, gauge fill, links, focus states. |
| `--clay` / `--clay-deep` | `#b9793e` / `#8f5a2b` | Secondary accent — used only for "use" tags (forage, timber, ornamental), so use-related info reads as a distinct category from site/eco info. |
| `--mustard` | `#d4a83e` | Reserved for exactly one thing: the gauge marker showing "your input." Spent in one place on purpose — see the frontend-design principle of spending boldness once. |
| `--danger` | `#a34a3c` | Warnings only (e.g. invasive-species flag). Never used decoratively. |

**Rule for reuse:** pick a palette the same way — ground every color in
something true about the new subject, not an aesthetic default. Don't
reuse these exact hexes for an unrelated subject; reuse the *method* (a
muted ground, one soft-black ink, one primary accent with a light/deep
pair, one secondary accent, one single-use highlight, one danger color).

## 3. Type — three roles, not two

- **Display — Fraunces** (serif, variable optical size): headings and
  scientific names. Its natural, slightly organic italic is what gives the
  page its "field guide" feel rather than a tech-product feel. Used
  sparingly — one heading, one italic emphasis word, never body paragraphs.
- **Body — IBM Plex Sans**: all UI copy, filter labels, descriptions.
  Neutral and highly legible; does not compete with the display face.
- **Data — IBM Plex Mono**: every number, count, measurement, and
  coordinate. This is the signature typographic move: putting numbers in
  mono instantly signals "this is measured data" and separates it from
  narrative text, without needing icons or extra labels.

**Rule for reuse:** keep the three-role split (display / body / data) even
if you swap the actual typefaces for a new brief's personality — a
finance tool might want a slab serif and a technical mono; the *pattern*
of "numbers get their own typeface" is the transferable idea.

## 4. Components — anatomy and where to steal from

All classes are prefixed `hal-` (for "halophyte") in `components.css`.
Rename the prefix per project; keep the internal structure.

- **`.hal-panel` / `.hal-row` / `.hal-field`** — the filter bar. A bordered
  card containing label+input pairs in a wrapping flex row. Reusable for
  any filter/search UI.
- **`.hal-chip`** — toggleable pill filters (`.on` state = solid teal fill).
  Good for any multi-select tag filter.
- **`.hal-sal-row` + `.hal-unit-toggle`** — a slider paired with a live
  mono-font value readout and a two-way unit toggle. Reusable pattern for
  any "numeric input with alternate units" control (currency, weight,
  temperature).
- **`.hal-card`** — the result card: a left accent border (`border-left`)
  that changes color by category (`.hal-unknown` = grey, `.hal-invasive` =
  red) — a fast, glanceable status signal without needing a badge/icon in
  the corner.
- **`.hal-gauge`** — the signature element: a horizontal gradient bar (0
  to max) with a filled "salt-crust" textured portion up to the record's
  own value, plus a mustard tick mark for the user's input value. This is
  the one place the design "spends its boldness" (per the frontend-design
  principle) — everything else stays quiet so this reads clearly. Reusable
  any time you need to show "this record's value vs. your target" —
  price-vs-budget, score-vs-threshold, etc.
- **`.hal-detail` (inside `.hal-card.open`)** — progressive disclosure:
  secondary detail hidden until a text-link toggle is clicked, keeping the
  scan-list dense by default.
- **`.hal-empty`** — dashed-border empty state with plain-language guidance
  ("try lowering X or clearing Y"), not just "no results."

## 5. Adapting this for a different project or subject

1. Re-run the grounding step: name the new subject, its audience, and the
   page's one job — don't reuse this palette/copy by default.
2. Keep: the three-role type system, the token structure (ground / ink /
   one primary accent pair / one secondary accent / one single-use
   highlight / one danger color), the left-border-as-status-signal card
   pattern, and progressive disclosure for secondary detail.
3. Change: the actual hex values, the display typeface pairing, and the
   signature element (the gauge is specific to "value vs. target" data —
   a different subject may call for a different one memorable element
   instead, not this one reused verbatim).
4. Re-run the self-critique pass: does the new palette/type still look
   like the "AI-generated defaults" (warm cream + terracotta serif;
   near-black + acid green; broadsheet hairline grid)? If yes, that axis
   hasn't actually been chosen for the new brief yet — revise it.

---

## Addendum: extension for the Knowledge Graph project

The knowledge-graph app reuses every token and component pattern above
as-is, and adds one thing: a color-per-node-kind scheme for the graph
visualization, since a graph needs to distinguish 6 entity types at a
glance (Species, Gene, Mechanism, Geography, Application, Paper).

| Kind | Color | Reasoning |
|---|---|---|
| Species | `--brack-deep` (teal) | The graph's main subject — reuses the primary accent. |
| Gene | `--clay-deep` (clay) | Reuses the existing secondary accent. |
| Mechanism | new `--mech` / `--mech-deep` (slate blue) | New hue for the new "engineering/how-it-works" layer that Field Match didn't need. |
| Geography | new `--geo` / `--geo-deep` (sage green) | New hue, grounded in "this is about place." |
| Application | `--mustard` | Reused, deliberately — an application is the single valuable endpoint of a research thread, matching mustard's original "spend it once, on the one thing that matters" role. |
| Paper | new `--paper` (neutral grey) | Provenance nodes are numerous and shouldn't visually compete with the entities they support — kept deliberately quiet. |

This is the pattern to follow for a third project: keep the ground/ink/type
system fixed, and add exactly as many new hues as new *categories* the new
subject introduces — not one per data field.
