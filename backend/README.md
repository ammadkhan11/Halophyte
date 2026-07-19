# Backend API

FastAPI backend for Phase 2 salt tolerance prediction APIs.

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

## Prediction Methods

Grass-based prediction uses species-anchored regression. Mechanism-based prediction uses KNN weighted estimation from the selected mechanism group.

All file loading uses project-relative paths through `model_loader.py`.
