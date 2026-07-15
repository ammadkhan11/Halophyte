# Backend API

FastAPI backend for Phase 2 salt tolerance prediction and Phase 4 research evidence graph APIs.

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

## Endpoints

- `GET /`
- `GET /health`
- `GET /metadata`
- `GET /grasses`
- `GET /model-metrics`
- `POST /predict`
- `GET /graph/overview`
- `GET /graph/entities`
- `GET /graph/entities/{node_id}`
- `GET /graph/evidence`
- `GET /graph/edges`
- `GET /graph/opportunities`
- `POST /graph/review/{edge_id}`
- `POST /graph/import-phase1`
- `POST /graph/seed`

## Prediction Methods

Grass-based prediction uses species-anchored regression. Mechanism-based prediction uses KNN weighted estimation from the selected mechanism group.

All file loading uses project-relative paths through `model_loader.py`.

## Research Evidence Graph

The Phase 4 graph uses the SQLite store in `halophyte_knowledge_graph/src/graph_store.py`. On first backend startup, an empty graph is seeded with the clearly labelled demonstration data from `halophyte_knowledge_graph/data/demo_seed.json`.

Import the Phase 1 CSV backbone from the default `ml/data/halophyte_grass_library.csv`:

```powershell
Invoke-RestMethod -Method Post -ContentType "application/json" -Body "{}" http://127.0.0.1:8000/graph/import-phase1
```

Review decisions are persisted in `halophyte_knowledge_graph/data/halophyte_graph.sqlite`.
