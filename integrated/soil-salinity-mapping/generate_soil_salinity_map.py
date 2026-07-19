from __future__ import annotations

import argparse
import html
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
    "Local salinity grid and crop-zone output for the selected region."
)

DATA_MODE = "local_grid"

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


def synthetic_indices(lat: float, lon: float, ec_value: float) -> dict[str, float]:
    ndvi = max(0.08, min(0.72, 0.58 - (ec_value * 0.035) + math.sin(lat * 0.8) * 0.035))
    ndsi = max(0.02, min(0.86, 0.16 + (ec_value * 0.055) + math.cos(lon * 0.6) * 0.025))
    savi = max(0.05, min(0.68, ndvi * 0.82 + 0.04))
    dvi = max(0.01, min(0.55, 0.28 - (ec_value * 0.012) + math.sin((lat + lon) * 0.4) * 0.025))
    return {
        "ndvi": round(ndvi, 3),
        "ndsi": round(ndsi, 3),
        "savi": round(savi, 3),
        "dvi": round(dvi, 3),
    }


def salinity_profile(ec_value: float) -> dict[str, str]:
    if ec_value < 4.0:
        return {
            "salinity_class": "Normal / slight",
            "risk_level": "Low",
            "crop_zone": "Conventional crop zone",
            "recommendation": "Wheat, cotton, rice, and standard rotation crops",
        }
    if ec_value < 8.0:
        return {
            "salinity_class": "Moderate",
            "risk_level": "Medium",
            "crop_zone": "Salt-tolerant crop zone",
            "recommendation": "Sunflower, sugarcane, barley, and managed irrigation",
        }
    return {
        "salinity_class": "Severe",
        "risk_level": "High",
        "crop_zone": "Halophyte / remediation zone",
        "recommendation": "Quinoa, Salicornia, fodder halophytes, and gypsum remediation review",
    }


def generate_grid(selected: list[str], points_per_province: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for province_name in selected:
        min_lat, min_lon, max_lat, max_lon = PROVINCES[province_name]["bounds"]
        for _ in range(points_per_province):
            lat = float(rng.uniform(min_lat, max_lat))
            lon = float(rng.uniform(min_lon, max_lon))
            ec_value = synthetic_ec(lat, lon, province_name)
            profile = salinity_profile(ec_value)
            indices = synthetic_indices(lat, lon, ec_value)
            rows.append(
                {
                    "province": province_name,
                    "lat": round(lat, 6),
                    "lon": round(lon, 6),
                    "ec_ds_m": ec_value,
                    **profile,
                    **indices,
                    "data_mode": DATA_MODE,
                }
            )
    return pd.DataFrame(rows)


def ec_color(value: float) -> str:
    if value < 4:
        return "#2e7d32"
    if value < 8:
        return "#d4a83e"
    return "#a34a3c"


def popup_html(row: pd.Series) -> str:
    values = [
        ("Province", row["province"]),
        ("Latitude", f"{float(row['lat']):.6f}"),
        ("Longitude", f"{float(row['lon']):.6f}"),
        ("EC / salinity", f"{float(row['ec_ds_m']):.2f} dS/m"),
        ("Salinity class", row["salinity_class"]),
        ("Risk level", row["risk_level"]),
        ("Crop zone", row["crop_zone"]),
        ("Recommendation", row["recommendation"]),
        ("NDVI", f"{float(row['ndvi']):.3f}"),
        ("NDSI", f"{float(row['ndsi']):.3f}"),
        ("SAVI", f"{float(row['savi']):.3f}"),
        ("DVI", f"{float(row['dvi']):.3f}"),
    ]
    table_rows = "\n".join(
        "<tr>"
        f"<th>{html.escape(str(label))}</th>"
        f"<td>{html.escape(str(value))}</td>"
        "</tr>"
        for label, value in values
    )
    return f"""
    <div style="font-family: system-ui, -apple-system, Segoe UI, sans-serif; min-width: 260px; max-width: 330px;">
      <h4 style="margin: 0 0 8px; color: #164d45;">Soil Salinity Point</h4>
      <table style="border-collapse: collapse; width: 100%; font-size: 12px;">
        {table_rows}
      </table>
    </div>
    """


def create_map(grid_df: pd.DataFrame, pakistan_geojson: dict[str, object], provinces_geojson: dict[str, object]) -> folium.Map:
    center_lat = float(grid_df["lat"].mean()) if not grid_df.empty else 30.0
    center_lon = float(grid_df["lon"].mean()) if not grid_df.empty else 69.5
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

    for _, row in grid_df.iterrows():
        ec_value = float(row["ec_ds_m"])
        folium.CircleMarker(
            location=[float(row["lat"]), float(row["lon"])],
            radius=4,
            color=ec_color(ec_value),
            fill=True,
            fill_color=ec_color(ec_value),
            fill_opacity=0.74,
            weight=0,
            popup=folium.Popup(popup_html(row), max_width=360),
        ).add_to(salinity_map)

    folium.LayerControl().add_to(salinity_map)
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
        "mode": DATA_MODE,
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
