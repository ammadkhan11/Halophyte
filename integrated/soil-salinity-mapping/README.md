# Soil Salinity Mapping Local Streamlit App

This folder contains local app code extracted from
`mini-projects/soil-salinity-crop-zoning/Soil_Salinity_Mapping_FIXED.ipynb`.

The app writes generated files to one output folder:

`integrated/soil-salinity-mapping/output`

Generated files:

- `salinity_grid.csv`
- `pakistan_boundary.geojson`
- `target_provinces.geojson`
- `soil_salinity_map.html`

The current local generator creates a clearly labelled demo/simulation map
because the source notebook used placeholder EC labels (`np.random.uniform`).
Do not present the EC values as field-verified measurements until real EC
ground-truth data is supplied.

```powershell
cd C:\Users\Ammad Khan\Downloads\halophyte_library_data_package
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r integrated\soil-salinity-mapping\requirements.txt
python -c "import ee; print('ee ok')"
earthengine authenticate
# If earthengine.exe is not on PATH:
python -m ee.cli.eecli authenticate
$env:EARTHENGINE_PROJECT='your-google-cloud-project-id'
```

Generate local outputs directly:

```powershell
python integrated\soil-salinity-mapping\generate_soil_salinity_map.py --province "Punjab and Sindh"
```

Run the FastAPI backend used by the React page's Generate Local Map button:

```powershell
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
cd ..
npm install
npm run dev
```

To run the original Streamlit UI locally after generation:

```powershell
cd integrated\soil-salinity-mapping
streamlit run app.py --server.port 8502
```

The main React app route `/soil-salinity-mapping` is an app-style wrapper that
checks Python/Earth Engine setup and runs the local generator through the
FastAPI backend. The generated map is served from
`public/modules/soil-salinity-mapping/generated-map.html`.

Scientific notice: This mapper is a local application wrapper around
satellite/region processing. EC prediction labels are placeholders until
verified field EC measurements are supplied.
