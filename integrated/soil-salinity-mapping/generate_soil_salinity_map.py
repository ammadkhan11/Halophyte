from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import folium
import numpy as np
import pandas as pd


MODULE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = MODULE_DIR / "output"
PUBLIC_OUTPUT_DIR = MODULE_DIR.parents[1] / "public" / "modules" / "soil-salinity-mapping"

SCIENTIFIC_NOTICE = (
    "This mapper is a local application wrapper around satellite/region processing. "
    "EC prediction labels are placeholders until verified field EC measurements are supplied."
)

PAKISTAN_BOUNDARY = [
    [60.85, 23.45],
    [77.1, 23.45],
    [77.1, 37.15],
    [60.85, 37.15],
    [60.85, 23.45],
]

PROVINCES = {
    "Punjab": {
        "center": [31.0, 72.2],
        "bounds": [27.7, 69.3, 34.2, 75.4],
        "polygon": [
            [69.3, 27.7],
            [74.9, 28.2],
            [75.4, 32.0],
            [73.7, 34.2],
            [70.2, 33.7],
            [69.3, 27.7],
        ],
    },
    "Sindh": {
        "center": [26.1, 68.9],
        "bounds": [23.6, 66.4, 28.8, 71.1],
        "polygon": [
            [66.4, 23.6],
            [69.1, 23.8],
            [71.1, 26.4],
            [70.2, 28.8],
            [67.7, 28.3],
            [66.4, 23.6],
        ],
    },
}


def polygon_feature(name: str, coordinates: list[list[float]]) -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {"shapeName": name},
        "geometry": {"type": "Polygon", "coordinates": [coordinates]},
    }


def build_geojson(province: str) -> tuple[dict[str, object], dict[str, object], list[str]]:
    selected = ["Punjab", "Sindh"] if province == "Punjab and Sindh" else [province]
    selected = [name for name in selected if name in PROVINCES]
    if not selected:
        selected = ["Punjab", "Sindh"]

    pakistan = polygon_feature("Pakistan demo boundary", PAKISTAN_BOUNDARY)
    target = {
        "type": "FeatureCollection",
        "features": [polygon_feature(name, PROVINCES[name]["polygon"]) for name in selected],
    }
    return pakistan, target, selected


def synthetic_ec(lat: float, lon: float, province_name: str) -> float:
    coastal_pressure = max(0.0, 27.5 - lat) * 0.72 if province_name == "Sindh" else 0.0
    irrigation_pressure = max(0.0, 73.8 - lon) * 0.34
    aridity_wave = (math.sin(lat * 1.7) + math.cos(lon * 1.2)) * 0.55
    province_offset = 2.8 if province_name == "Sindh" else 1.5
    return max(0.4, round(province_offset + coastal_pressure + irrigation_pressure + aridity_wave, 3))


def generate_grid(selected: list[str], points_per_province: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for province_name in selected:
        min_lat, min_lon, max_lat, max_lon = PROVINCES[province_name]["bounds"]
        for _ in range(points_per_province):
            lat = float(rng.uniform(min_lat, max_lat))
            lon = float(rng.uniform(min_lon, max_lon))
            rows.append(
                {
                    "Province": province_name,
                    "Latitude": round(lat, 6),
                    "Longitude": round(lon, 6),
                    "Predicted_EC": synthetic_ec(lat, lon, province_name),
                    "Label_Source": "demo_simulation_placeholder",
                }
            )
    return pd.DataFrame(rows)


def ec_color(value: float) -> str:
    if value < 4:
        return "#2e7d32"
    if value < 8:
        return "#d4a83e"
    return "#a34a3c"


def create_map(grid_df: pd.DataFrame, pakistan_geojson: dict[str, object], provinces_geojson: dict[str, object]) -> folium.Map:
    center_lat = float(grid_df["Latitude"].mean()) if not grid_df.empty else 30.0
    center_lon = float(grid_df["Longitude"].mean()) if not grid_df.empty else 69.5
    salinity_map = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles="CartoDB positron")

    folium.GeoJson(
        pakistan_geojson,
        name="Pakistan demo boundary",
        style_function=lambda feature: {"fillOpacity": 0, "color": "#333333", "weight": 1.5},
    ).add_to(salinity_map)

    folium.GeoJson(
        provinces_geojson,
        name="Active provinces",
        style_function=lambda feature: {
            "fillColor": "#2e7d32",
            "color": "#1b5e20",
            "weight": 2,
            "fillOpacity": 0.12,
        },
        tooltip=folium.GeoJsonTooltip(fields=["shapeName"], aliases=["Province:"]),
    ).add_to(salinity_map)

    for row in grid_df.itertuples(index=False):
        ec_value = float(getattr(row, "Predicted_EC"))
        province = str(getattr(row, "Province"))
        folium.CircleMarker(
            location=[float(getattr(row, "Latitude")), float(getattr(row, "Longitude"))],
            radius=4,
            color=ec_color(ec_value),
            fill=True,
            fill_color=ec_color(ec_value),
            fill_opacity=0.74,
            weight=0,
            popup=(
                f"Province: {province}<br>"
                f"Demo EC label: {ec_value:.2f} dS/m<br>"
                f"{SCIENTIFIC_NOTICE}"
            ),
        ).add_to(salinity_map)

    folium.LayerControl().add_to(salinity_map)
    notice_html = f"""
    <div style="position: fixed; left: 16px; right: 16px; bottom: 16px; z-index: 9999;
      padding: 10px 12px; background: #fff7ed; border: 1px solid #d4a83e;
      color: #242923; font: 13px system-ui, sans-serif; border-radius: 6px;">
      <strong>Demo/simulation map:</strong> {SCIENTIFIC_NOTICE}
      Province outlines are local demo geometries for offline use; regenerate with Earth Engine assets
      before using this for research claims.
    </div>
    """
    salinity_map.get_root().html.add_child(folium.Element(notice_html))
    return salinity_map


def write_outputs(province: str, points_per_province: int, seed: int) -> dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pakistan_geojson, provinces_geojson, selected = build_geojson(province)
    grid_df = generate_grid(selected=selected, points_per_province=points_per_province, seed=seed)

    salinity_grid_path = OUTPUT_DIR / "salinity_grid.csv"
    pakistan_path = OUTPUT_DIR / "pakistan_boundary.geojson"
    provinces_path = OUTPUT_DIR / "target_provinces.geojson"
    output_map_path = OUTPUT_DIR / "soil_salinity_map.html"
    public_map_path = PUBLIC_OUTPUT_DIR / "generated-map.html"

    grid_df.to_csv(salinity_grid_path, index=False)
    pakistan_path.write_text(json.dumps(pakistan_geojson, indent=2), encoding="utf-8")
    provinces_path.write_text(json.dumps(provinces_geojson, indent=2), encoding="utf-8")

    salinity_map = create_map(grid_df, pakistan_geojson, provinces_geojson)
    salinity_map.save(output_map_path)
    salinity_map.save(public_map_path)

    metadata = {
        "status": "generated",
        "mode": "demo_simulation",
        "province": province,
        "selected_provinces": selected,
        "points_rendered": int(len(grid_df)),
        "total_points": int(len(grid_df)),
        "scientific_notice": SCIENTIFIC_NOTICE,
        "outputs": {
            "salinity_grid_csv": str(salinity_grid_path),
            "pakistan_boundary_geojson": str(pakistan_path),
            "target_provinces_geojson": str(provinces_path),
            "soil_salinity_map_html": str(output_map_path),
            "public_map_html": str(public_map_path),
        },
    }
    (OUTPUT_DIR / "generation_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate local Pakistan soil salinity demo map assets.")
    parser.add_argument("--province", default="Punjab and Sindh", choices=["Punjab and Sindh", "Punjab", "Sindh"])
    parser.add_argument("--points-per-province", type=int, default=360)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    metadata = write_outputs(args.province, args.points_per_province, args.seed)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
