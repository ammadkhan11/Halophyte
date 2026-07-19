"""
Cleans China_Salt_Alkali_Tolerant_Plants_English.csv into a flat JSON
array consumed by app/halophyte_field_match.html.

Usage:
    python3 clean_data.py path/to/source.csv path/to/output.json

What it does:
- Parses the free-text "Maximum Salinity" field into a numeric mM value
  (handles mM, dS/m, and mg/L strings; takes the highest value found;
  flags entries where the source text says "estimated" or "unknown").
- Splits the messy "Uses" column into a normalized lowercase list and
  pulls "invasive" / "naturalized invasive" / "weed" out into its own
  boolean flag instead of leaving it mixed in with real uses.
- Splits "Ecological Type" (e.g. "Xerophytic; psammophytic") into a
  clean, title-cased list of tags.
- Strips the "I./II./III." numbering prefix off "Main Plant Group".
- Drops the long free-text "Morphology" and "English Alias" columns,
  which aren't used by the app and roughly double file size.

Re-run this any time the source CSV is updated, or adapt the parsing
functions if you add more source columns.
"""
import pandas as pd
import re
import json
import sys


def parse_salinity(s):
    s = str(s)
    if not s.strip():
        return None, False
    estimated = "estimated" in s.lower() or "unknown" in s.lower()
    mm_vals = [float(x) for x in re.findall(r'([\d.]+)\s*mM', s)]
    if mm_vals:
        return max(mm_vals), estimated
    ds_vals = [float(x) for x in re.findall(r'([\d.]+)\s*dS/m', s)]
    if ds_vals:
        # rough conversion: 1 dS/m ~ 10 mM NaCl-equivalent
        return max(ds_vals) * 10, estimated
    return None, estimated


def norm_uses(s):
    if not s:
        return [], False
    parts = re.split(r'[,;]', s)
    out, seen, invasive = [], set(), False
    for p in parts:
        key = p.strip().lower()
        if not key:
            continue
        if "invasive" in key or key == "weed":
            invasive = True
            continue
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out, invasive


def norm_halotype(s):
    s = s.strip()
    if not s:
        return "Unclassified"
    return s.replace("？", "?").replace(" ?", "").replace("?", "").strip()


def norm_eco(s):
    s = s.strip()
    if not s:
        return []
    parts = re.split(r';|,| or ', s)
    tags = set()
    for p in parts:
        p = p.strip().rstrip(".").replace("(two dwelling)", "").strip()
        if p:
            tags.add(p[0].upper() + p[1:])
    return sorted(tags)


def clean(csv_path, json_path):
    df = pd.read_csv(csv_path).fillna("")
    records = []
    for _, row in df.iterrows():
        max_mm, est = parse_salinity(row["Maximum Salinity"])
        uses, invasive = norm_uses(row["Uses"])
        records.append({
            "id": int(row["Sequence Number"]),
            "grp": row["Main Plant Group"].replace("I. ", "").replace("II. ", "").replace("III. ", ""),
            "fam": row["Family Name (English)"],
            "gen": row["Genus Name (English)"],
            "name": row["English Plant Name"],
            "sci": row["Scientific Name"],
            "dist": row["Distribution"],
            "hab": row["Habitat"],
            "life": row["Life Form"],
            "ht": row["Height"].replace("Plant height ", "").strip(),
            "halo": norm_halotype(row["Halophyte Type"]),
            "eco": norm_eco(row["Ecological Type"]),
            "sal": max_mm,
            "salEst": est,
            "path": row["Photosynthetic Pathway"] or "Unknown",
            "uses": uses,
            "inv": invasive,
        })
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, separators=(",", ":"))
    print(f"Wrote {len(records)} records to {json_path}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "../data/plants_source.csv"
    dst = sys.argv[2] if len(sys.argv) > 2 else "../data/plants_cleaned.json"
    clean(src, dst)
