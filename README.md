# Halophyte Grass Dictionary and ML-Based Salt Tolerance Prediction System

Final year project web application for exploring halophyte grass records, estimating missing salt tolerance or ion concentration factors, and inspecting citation-backed research evidence.

## Features

- Searchable halophyte grass dictionary.
- Filters for mechanism, salt tolerance level, GR50, and ion categories.
- Sortable table and responsive card view.
- Detailed grass profile modal.
- Unit conversion helper for salinity and ion concentration context.
- Phase 2 prediction module for GR50 and ion values.
- Phase 4 Research Evidence module with a SQLite-backed knowledge graph.
- Evidence explorer, graph visualization, research leads, and manual review queue.
- Backend API with dataset/model metadata and prediction endpoints.
- Backend graph API with seed/import/review actions.
- Model evaluation summary when notebook artifacts are available.

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

## Phase 3: Analysis Dashboard

Phase 3 keeps the project analysis layer visible through summary statistics, model evaluation metrics, and comparison context. These analysis outputs help explain the cleaned dataset and the Phase 2 regression behavior.

## Phase 4: Research Evidence

Phase 4 adds the Halophyte Research Knowledge Graph as an integrated app section named **Research Evidence**. It uses the provided SQLite graph store and demo seed data through the existing FastAPI backend.

The graph links species, mechanisms, genes, applications, geography, salinity thresholds, and source papers. Literature relationships keep provenance, exact evidence quotes, confidence, and review status. Demonstration records remain labelled as demonstration/review data. Research opportunities are described only as research leads based on graph coverage, not proven discoveries.

Phase 2 predictions and Phase 4 graph evidence are intentionally separate: model results are labelled as **Predicted values**, while graph records are labelled as **Literature evidence** or project-data backbone records.

## Tech Stack

- React
- TypeScript
- Vite
- FastAPI
- pandas
- numpy
- scikit-learn
- joblib
- SQLite

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
    graph_service.py
  ml/
    data/
    models/
    notebooks/
  docs/
  halophyte_knowledge_graph/
  archive/
```

## Start the Integrated Project

Run the backend and frontend in two terminals.

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

## Seed the Knowledge Graph

The backend safely seeds the demo graph on first startup if the SQLite graph is empty. You can also seed it from the Research Evidence overview screen or by API:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/graph/seed
```

Equivalent CLI:

```powershell
python -m halophyte_knowledge_graph.src.cli seed
```

The SQLite database is stored at `halophyte_knowledge_graph/data/halophyte_graph.sqlite`.

## Import Phase 1 CSV Data

Use the **Import Phase 1 CSV** button in Research Evidence, or call:

```powershell
Invoke-RestMethod -Method Post -ContentType "application/json" -Body "{}" http://127.0.0.1:8000/graph/import-phase1
```

By default this imports `ml/data/halophyte_grass_library.csv` as graph backbone records for species, mechanisms, and GR50 thresholds.

## Run Tests

Frontend build and type check:

```powershell
npm.cmd run build
```

Graph safeguard tests:

```powershell
cd halophyte_knowledge_graph
python -m unittest discover -s tests
```

Backend syntax check:

```powershell
python -m py_compile backend\main.py backend\graph_service.py backend\schemas.py halophyte_knowledge_graph\src\graph_store.py halophyte_knowledge_graph\src\analysis.py halophyte_knowledge_graph\src\extraction.py
```

## Dataset and Model Files

- `ml/data/halophyte_grass_library.csv` - final cleaned CSV used by the backend and notebook.
- `src/data/grassLibraryData.ts` - TypeScript dataset used by the frontend dictionary.
- `ml/notebooks/Phase2_Model_Training_and_Comparison.ipynb` - notebook for model training and comparison.
- `ml/models/best_model_bundle.joblib` - saved model bundle generated by the notebook.
- `ml/models/model_comparison_results.csv` - model evaluation table.
- `ml/models/model_metrics_summary.json` - summary of evaluation results.
- `ml/models/numeric_fields.json` - numeric fields used by Phase 2.
- `halophyte_knowledge_graph/data/demo_seed.json` - clearly labelled Phase 4 demonstration/review seed.
- `halophyte_knowledge_graph/data/halophyte_graph.sqlite` - generated persistent SQLite graph database.

## Backend API

- `GET /` - backend status.
- `GET /health` - dataset/model health status.
- `GET /metadata` - fields, mechanisms, modes, and species options.
- `GET /grasses` - grass options for frontend dropdowns.
- `GET /model-metrics` - notebook evaluation artifacts if available.
- `POST /predict` - Phase 2 prediction endpoint.
- `GET /graph/overview` - graph counts.
- `GET /graph/entities` - search graph entities.
- `GET /graph/entities/{node_id}` - entity details and evidence links.
- `GET /graph/evidence` - evidence cards filtered by species, mechanism, gene, application, geography, and status.
- `GET /graph/edges` - graph edges for visualization/review.
- `GET /graph/opportunities` - research leads based on graph coverage.
- `POST /graph/review/{edge_id}` - approve or reject a pending relationship.
- `POST /graph/import-phase1` - import the Phase 1 CSV backbone.
- `POST /graph/seed` - load demonstration graph records.

## Supervisor Note

The prediction module is regression-based estimation on a small biological dataset of 30 grasses. The system avoids false claims of exact accuracy and does not claim a separate model for each grass. The Research Evidence module adds literature context without treating predictions as published scientific facts.
