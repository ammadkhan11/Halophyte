# Halophyte Grass Dictionary and ML-Based Salt Tolerance Prediction System

Final year project web application for exploring halophyte grass records and estimating missing salt tolerance or ion concentration factors.

## Features

- Searchable halophyte grass dictionary.
- Filters for mechanism, salt tolerance level, GR50, and ion categories.
- Sortable table and responsive card view.
- Detailed grass profile modal.
- Unit conversion helper for salinity and ion concentration context.
- Phase 2 prediction module for GR50 and ion values.
- Integrated navigation for internal modules and side-project materials.
- Embedded Halophyte Knowledge Graph module served unchanged from its standalone HTML frontend.
- Embedded Halophyte Field Match module served unchanged from its standalone HTML frontend.
- Pakistan Soil Salinity Mapper route with local setup/status checks and generated-map support.
- Crop Salinity Screening route for the biosaline agriculture phase, converted from Streamlit to the main React/FastAPI app.
- Backend API with dataset/model metadata and prediction endpoints.

## Phase 1: Grass Dictionary

Phase 1 provides the cleaned grass library interface. It includes search, filtering, sorting, summary statistics, table/card display, detail modal, and the unit conversion helper.

## Phase 2: Prediction Model

Phase 2 adds estimated prediction for these numeric fields:

- `gr50_avg`
- `na_shoot`
- `na_root`
- `cl_shoot`
- `cl_root`
- `k_shoot`
- `k_root`

Grass-Based Prediction uses species-anchored regression. The selected grass is used as the base profile, and the entered known value is compared with the stored dataset value. The difference is used to adjust remaining values using regression slopes learned from the dataset.

Mechanism-Based Prediction uses KNN weighted estimation within the selected mechanism group and returns similar grasses used for context.

Each grass has one available record, so separate per-species models are not statistically valid. Predictions are estimates for academic learning and comparison, not final biological measurements.

## Integrated Routes

The main React app uses path-based navigation so direct refresh works in Vite dev/preview:

- `/` - main Halophyte grass library.
- `/prediction` - salt tolerance prediction model.
- `/crop-salinity-screening` - biosaline crop salinity risk screening, without profit or economics.
- `/knowledge-graph` - embedded Halophyte Knowledge Graph standalone HTML app.
- `/field-match` - embedded Halophyte Field Match standalone HTML app.
- `/soil-salinity-mapping` - Pakistan Soil Salinity Mapper app page.
- `/mini-projects` - redirects to the Soil Salinity Mapper route.

Static integrated module files are served from:

- `public/modules/knowledge-graph/index.html`
- `public/modules/field-match/index.html`
- `public/modules/mini-projects/` for notebook provenance/reference material
- `public/modules/soil-salinity-mapping/generated-map.html` after local map generation

The local Streamlit app extracted from the soil salinity notebook is available at:

- `integrated/soil-salinity-mapping/app.py`

The biosaline agriculture phase source still includes its original Streamlit app for reference, but the integrated local route is:

- `/crop-salinity-screening`

## Tech Stack

- React
- TypeScript
- Vite
- FastAPI
- pandas
- numpy
- scikit-learn
- joblib
- PyYAML
- openpyxl

## Folder Structure

```text
project-root/
  README.md
  package.json
  package-lock.json
  vite.config.ts
  tsconfig.json
  index.html
  .gitignore
  public/
    modules/
      knowledge-graph/
      field-match/
      mini-projects/
  integrated/
    soil-salinity-mapping/
  FYP-halophyte-No-Profit-Feature/
  src/
    components/
    data/
    lib/
    pages/
    utils/
    App.tsx
    main.tsx
    index.css
  backend/
    main.py
    model_loader.py
    prediction_service.py
    schemas.py
  ml/
    data/
    models/
    notebooks/
  docs/
  archive/
```

## Start the Integrated Project

Run the backend and frontend in two terminals.

For the usual local workflow on Windows, this helper starts the backend and frontend together:

```powershell
npm.cmd run dev:all
```

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend health and API documentation:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/docs
```

If pandas or scikit-learn installation fails on Python 3.14, use Python 3.11 or 3.12.

### Frontend

```powershell
npm.cmd install
npm.cmd run dev
```

Open the Vite URL shown in the terminal, usually:

```text
http://127.0.0.1:5173/
```

PowerShell may block the `npm` shim on some Windows machines. Use `npm.cmd` as shown above.

## Run Tests

Frontend build and type check:

```powershell
npm.cmd run build
```

Backend syntax check:

```powershell
python -m py_compile backend\main.py backend\model_loader.py backend\prediction_service.py backend\schemas.py
```

## Dataset and Model Files

- `ml/data/halophyte_grass_library.csv` - final cleaned CSV used by the backend and notebook.
- `src/data/grassLibraryData.ts` - TypeScript dataset used by the frontend dictionary.
- `ml/notebooks/Phase2_Model_Training_and_Comparison.ipynb` - notebook for model training and comparison.
- `ml/models/best_model_bundle.joblib` - saved model bundle generated by the notebook.
- `ml/models/model_comparison_results.csv` - model evaluation table.
- `ml/models/model_metrics_summary.json` - summary of evaluation results.
- `ml/models/numeric_fields.json` - numeric fields used by Phase 2.

## Backend API

- `GET /` - backend status.
- `GET /health` - dataset/model health status.
- `GET /metadata` - fields, mechanisms, modes, and species options.
- `GET /grasses` - grass options for frontend dropdowns.
- `GET /model-metrics` - notebook evaluation artifacts if available.
- `POST /predict` - Phase 2 prediction endpoint.
- `GET /biosaline-crop-screening/status` - Crop Salinity Screening setup, dataset, and model status.
- `GET /biosaline-crop-screening/crops` - crop options loaded from the biosaline phase config.
- `POST /biosaline-crop-screening/predict` - Maas-Hoffman/surrogate crop salinity screening endpoint.

## Supervisor Note

The prediction module is regression-based estimation on a small biological dataset of 30 grasses. The system avoids false claims of exact accuracy and does not claim a separate model for each grass.
