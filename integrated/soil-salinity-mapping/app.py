import json
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import streamlit as st
from geopy.geocoders import Nominatim
from scipy.spatial import cKDTree
from shapely.geometry import Point, box, mapping, shape
from shapely.ops import unary_union
from streamlit_folium import st_folium


st.set_page_config(page_title="Pakistan Soil Tool", layout="wide")

ASSET_DIR = Path(__file__).resolve().parent / "output"


@st.cache_resource
def load_assets():
    grid_df = pd.read_csv(ASSET_DIR / "salinity_grid.csv")
    tree = cKDTree(grid_df[["Latitude", "Longitude"]].values)

    SIMPLIFY_TOL = 0.01

    with open(ASSET_DIR / "pakistan_boundary.geojson", encoding="utf-8") as file:
        pak_gj = json.load(file)
    pakistan_shape = shape(pak_gj["geometry"]).simplify(SIMPLIFY_TOL, preserve_topology=True)

    with open(ASSET_DIR / "target_provinces.geojson", encoding="utf-8") as file:
        raw_prov_gj = json.load(file)

    simplified_features = []
    province_shapes = {}
    for feat in raw_prov_gj["features"]:
        name = feat["properties"].get("shapeName", "Unknown")
        simp = shape(feat["geometry"]).simplify(SIMPLIFY_TOL, preserve_topology=True)
        province_shapes[name] = simp
        simplified_features.append(
            {
                "type": "Feature",
                "properties": {"shapeName": name},
                "geometry": mapping(simp),
            }
        )
    prov_gj = {"type": "FeatureCollection", "features": simplified_features}

    active_shape = unary_union(list(province_shapes.values()))
    world = box(-180, -90, 180, 90)
    mask_shape = world.difference(pakistan_shape)

    return grid_df, tree, pakistan_shape, prov_gj, active_shape, mask_shape


def get_recommendation(ec_value):
    if ec_value < 4.0:
        return {"status": "Normal / Slight Salinity", "crops": ["wheat", "cotton", "rice"]}
    if ec_value < 8.0:
        return {"status": "Moderate Salinity", "crops": ["sunflower", "sugarcane"]}
    return {"status": "Severe Salinity", "crops": ["fodder crops", "olive", "quinoa", "Salicornia"]}


def calculate_gypsum(ec_value):
    if ec_value <= 4.0:
        return 0.0, 0.0
    tons = (ec_value - 4.0) * 0.4
    return round(tons, 2), round(tons * 22500, 2)


@st.cache_data(show_spinner=False)
def reverse_geocode(lat, lon):
    try:
        geolocator = Nominatim(user_agent="pak_salinity_mapper")
        location = geolocator.reverse(f"{lat}, {lon}", zoom=10, timeout=5)
        return location.address if location else "Unknown location"
    except Exception:
        return "Location name unavailable"


def main():
    if "target_lat" not in st.session_state:
        st.session_state.target_lat = None
        st.session_state.target_lon = None

    try:
        grid_df, tree, pakistan_shape, prov_gj, active_shape, mask_shape = load_assets()
    except Exception as exc:
        st.error(f"Could not load required files: {exc}")
        return

    st.title("Pakistan Spatial Soil Mapping")
    st.caption(
        "Click anywhere in Punjab or Sindh for a salinity prediction and crop guidance. "
        "(Balochistan / KPK are shown for context but have no data yet.)"
    )
    col1, col2 = st.columns([1.5, 1.2])

    with col1:
        pak_minx, pak_miny, pak_maxx, pak_maxy = pakistan_shape.bounds
        m = folium.Map(
            location=[30.0, 69.5],
            zoom_start=6,
            tiles="CartoDB positron",
            max_bounds=True,
            min_lat=pak_miny - 1,
            max_lat=pak_maxy + 1,
            min_lon=pak_minx - 1,
            max_lon=pak_maxx + 1,
            max_bounds_viscosity=1.0,
        )
        m.fit_bounds([[pak_miny, pak_minx], [pak_maxy, pak_maxx]])

        folium.GeoJson(
            mapping(mask_shape),
            style_function=lambda feature: {
                "fillColor": "#1a1a1a",
                "color": "#1a1a1a",
                "fillOpacity": 0.55,
                "weight": 0,
            },
            interactive=False,
        ).add_to(m)

        folium.GeoJson(
            mapping(pakistan_shape),
            style_function=lambda feature: {"fillOpacity": 0, "color": "#333333", "weight": 1.5},
            interactive=False,
        ).add_to(m)

        folium.GeoJson(
            prov_gj,
            style_function=lambda feature: {
                "fillColor": "#2e7d32",
                "color": "#1b5e20",
                "weight": 2,
                "fillOpacity": 0.12,
            },
            tooltip=folium.GeoJsonTooltip(fields=["shapeName"], aliases=["Province:"]),
            interactive=False,
        ).add_to(m)

        if st.session_state.target_lat:
            folium.Marker(
                [st.session_state.target_lat, st.session_state.target_lon],
                icon=folium.Icon(color="darkblue"),
            ).add_to(m)

        map_data = st_folium(m, height=550, width=650)
        if map_data.get("last_clicked"):
            new_lat, new_lon = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
            if (new_lat, new_lon) != (st.session_state.target_lat, st.session_state.target_lon):
                st.session_state.target_lat, st.session_state.target_lon = new_lat, new_lon
                st.rerun()

    with col2:
        lat, lon = st.session_state.target_lat, st.session_state.target_lon
        if lat is None:
            st.info("Click a point on the map to get a prediction.")
        elif not pakistan_shape.contains(Point(lon, lat)):
            st.warning("That point is outside Pakistan. Click within the country border.")
        elif not active_shape.contains(Point(lon, lat)):
            st.warning("No data available for this region yet — only Punjab and Sindh are covered so far.")
            place_name = reverse_geocode(lat, lon)
            st.markdown(f"**Location:** {place_name}")
        else:
            place_name = reverse_geocode(lat, lon)
            dist, idx = tree.query([lat, lon])
            row = grid_df.iloc[idx]
            predicted_ec = row["Predicted_EC"]
            rec = get_recommendation(predicted_ec)

            st.markdown(f"### Location: {place_name}")
            st.markdown(f"**Coordinates:** {lat:.4f}, {lon:.4f}")
            st.markdown(f"### Predicted Salinity: {predicted_ec:.2f} dS/m")
            st.markdown(f"### Status: {rec['status']}")
            st.markdown(f"**Recommended crops:** {', '.join(rec['crops'])}")

            tons, pkr_cost = calculate_gypsum(predicted_ec)
            if tons > 0:
                st.error(f"Gypsum Required: {tons} Tons/Acre (Rs. {pkr_cost:,.0f})")

            report_data = pd.DataFrame(
                [
                    {
                        "Location": place_name,
                        "Lat": lat,
                        "Lon": lon,
                        "Predicted_EC": predicted_ec,
                        "Status": rec["status"],
                    }
                ]
            )
            st.download_button("Download Report", report_data.to_csv(index=False), "report.csv", "text/csv")


if __name__ == "__main__":
    main()
