# Soil Salinity Mapping & Crop Zoning

Satellite-driven soil salinity prediction and halophyte/salt-tolerant crop recommendation system for Pakistan (Punjab & Sindh).

> This is a self-contained mini-project inside the larger **Halophyte** repository. It does not modify or depend on the main React/FastAPI application in `src/` or `backend/` — it is a separate Google Colab notebook + Streamlit app that can be run independently.

---

## What is this project?

A tool that predicts soil salinity (Electrical Conductivity, EC, in dS/m) from **free satellite imagery** and automatically recommends which crop — including salt-tolerant halophyte crops — is agronomically viable at any point in Punjab or Sindh, Pakistan.

You click a location on a map. The app returns:
- The place name (reverse-geocoded)
- Predicted soil salinity (EC, dS/m)
- A salinity severity status (Normal / Moderate / Severe)
- A recommended crop for that salinity level
- An estimated gypsum requirement if the soil needs remediation

---

## Why does this need to exist? (The problem)

Farmers and agricultural planners in coastal, arid, and irrigation-heavy regions need to know where soil salinity is a problem and which crops will actually grow there. But ground-truth soil testing (EC measurement) is expensive, sparse, and slow to scale across large regions.

Meanwhile, satellite imagery covering these regions (Sentinel-2, via Google Earth Engine) is free, high-resolution, and updated every few days.

Existing salinity research largely stops at "here is a map of predicted EC." It doesn't connect that prediction to a decision a farmer can act on: *what should I actually plant here?* This project closes that gap by chaining a satellite-based prediction model to a crop-recommendation layer.

## Use case

- **Agricultural planners / extension officers** — quickly screen a district for salinity hotspots before recommending crop rotations or soil remediation (gypsum application).
- **Researchers / students** — a working, reproducible example of remote-sensing-based soil property prediction using open data and free compute.
- **Portfolio / academic deliverable** — demonstrates an end-to-end applied ML + geospatial pipeline: data acquisition → feature engineering → model training → spatial inference → interactive delivery.

## Relevance to the broader Halophyte project

The main Halophyte app (this repo) is a grass dictionary and salt-tolerance prediction system for halophyte species. This mini-project is a natural companion: where the main app tells you *how salt-tolerant a given grass/crop is*, this tool tells you *how salty a given piece of land actually is* — the two combine into a full "is this land salty → what should I plant" workflow. A future integration could pull crop/grass salt-tolerance thresholds directly from the Halophyte grass dictionary instead of the hardcoded lookup table currently used here.

---

## How it works (pipeline)

1. **Area of interest** — Real Punjab/Sindh province boundaries pulled from Earth Engine's `geoBoundaries` dataset (not hand-drawn rectangles).
2. **Satellite data** — Sentinel-2 (10m resolution) imagery pulled via Google Earth Engine, cloud-filtered, median composite for 2023.
3. **Spectral indices** — NDVI (vegetation vigor), NDSI (salinity index), DVI, SAVI computed per pixel.
4. **Ground-truth extraction** — Satellite features batch-extracted at ground-truth point locations (currently placeholder/synthetic points — see Limitations below).
5. **Model training** — Random Forest Regressor (scikit-learn) trained to predict EC from the spectral indices.
6. **Prediction grid** — The trained model is run across a dense grid of points covering Punjab + Sindh, and results are cached to `salinity_grid.csv`.
7. **Crop recommendation** — A rule-based lookup table maps predicted EC to a salinity tolerance class and recommended crop (from standard crops like wheat/cotton up to halophytes like Salicornia and quinoa for severe salinity).
8. **Delivery** — A Streamlit + Folium web app lets a user click anywhere in Punjab/Sindh and get an instant prediction, with the map masked/restricted to Pakistan and Punjab/Sindh highlighted as the only "active" (data-covered) provinces.

---

## Tech stack

| Layer | Technology |
|---|---|
| Satellite data & processing | Google Earth Engine (Python API) |
| ML / data | Python, pandas, numpy, scikit-learn (Random Forest), shapely, joblib |
| Backend + Frontend (combined) | Streamlit (Python) — the app is server-rendered Python, not a separate JS frontend |
| Mapping | Folium (Leaflet.js under the hood), `streamlit-folium` |
| Geolocation | `geopy` (OpenStreetMap Nominatim reverse geocoding) |
| Compute / hosting | Google Colab (free tier) — no paid infrastructure required |
| Public URL / tunnel | Cloudflare Tunnel (`cloudflared`) |

**Note on architecture:** unlike the main Halophyte app (React frontend + FastAPI backend as two separate services), this mini-project uses **Streamlit**, where the "backend" (model inference, data loading) and "frontend" (UI rendering) are the same Python process. There is no separate REST API or JS build step — it's a single script (`app.py`) that Streamlit turns into a web app.

---

## Folder contents

```
mini-projects/soil-salinity-crop-zoning/
  README.md                                    <- this file
  Soil_Salinity_Mapping_FIXED.ipynb             <- the full pipeline: GEE setup -> training -> app.py -> launch
  docs/
    Project2_SoilSalinity_Mapping_CropZoning.pdf     <- original project brief (problem, methodology, deliverables)
    Zero_Cost_Salinity_Mapping_Project_Guide.pdf     <- zero-cost tool stack / step-by-step execution guide
```

## How to run it

This runs entirely in **Google Colab** (free tier), not locally.

1. Open [Google Colab](https://colab.research.google.com), upload `Soil_Salinity_Mapping_FIXED.ipynb`.
2. Run all cells top to bottom. You'll be prompted once to authenticate a Google Earth Engine account (free, sign up at [earthengine.google.com](https://earthengine.google.com) if you haven't).
3. The final cell prints a public `https://*.trycloudflare.com` URL — open it to use the app.

No local Python environment, no paid API keys, no GPU required.

## Current limitations (read before treating outputs as real predictions)

- **Ground-truth EC values are placeholders**, not real field measurements (`np.random.uniform`). No public, structured (lat/lon + EC) dataset for Punjab/Sindh was found during this project — only non-digitized survey reports. Real satellite features are correctly extracted; the model just doesn't yet have real salinity labels to learn from.
- **Balochistan and KPK are not covered.** They're visible on the map for geographic context but return "no data" if clicked — same reasoning as above, extended to those provinces.
- Before using this for any real agricultural decision, swap the placeholder ground-truth in the notebook for a real EC dataset (see `docs/Project2_SoilSalinity_Mapping_CropZoning.pdf`, Section 4, for candidate sources: Zenodo, Dryad, FAO/ISRIC).

## Credits

Based on the original project brief and zero-cost execution guide included in `docs/`.
