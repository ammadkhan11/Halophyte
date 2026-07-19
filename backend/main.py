from __future__ import annotations

import json

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from model_loader import (
    MODEL_COMPARISON_PATH,
    MODEL_METRICS_PATH,
    NUMERIC_FIELDS,
    resources,
)
from prediction_service import predict
from schemas import PredictionRequest, PredictionResponse
from biosaline_service import (
    BiosalineSetupError,
    biosaline_crops,
    biosaline_predict,
    biosaline_status,
)
from soil_salinity_service import generate_soil_salinity_map, soil_salinity_status


app = FastAPI(
    title="Halophyte Grass Dictionary Phase 2 API",
    description="Regression-based salt tolerance and ion concentration estimation API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "running",
        "message": "Halophyte Grass Dictionary backend is running with Phase 2 prediction APIs.",
    }


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "dataset_loaded": resources.dataset_loaded,
        "model_loaded": resources.model_loaded,
        "number_of_records": int(len(resources.dataset)),
    }


@app.get("/metadata")
def metadata() -> dict[str, object]:
    species = (
        resources.dataset[["species", "common_name", "mechanism"]]
        .sort_values("species")
        .to_dict(orient="records")
    )
    return {
        "numeric_fields": NUMERIC_FIELDS,
        "mechanism_options": sorted(resources.dataset["mechanism"].dropna().unique().tolist()),
        "prediction_modes": ["grass_based", "mechanism_based"],
        "available_species": species,
    }


@app.get("/grasses")
def grasses() -> list[dict[str, str]]:
    return (
        resources.dataset[["species", "common_name", "mechanism"]]
        .sort_values("species")
        .to_dict(orient="records")
    )


@app.get("/model-metrics")
def model_metrics() -> dict[str, object]:
    if not MODEL_COMPARISON_PATH.exists() or not MODEL_METRICS_PATH.exists():
        return {"message": "Model metrics are not available yet. Run the Phase 2 notebook first."}

    comparison = pd.read_csv(MODEL_COMPARISON_PATH).to_dict(orient="records")
    with open(MODEL_METRICS_PATH, "r", encoding="utf-8") as file:
        summary = json.load(file)

    return {
        "comparison_results": comparison,
        "metrics_summary": summary,
    }


@app.post("/predict", response_model=PredictionResponse)
def predict_values(request: PredictionRequest) -> dict[str, object]:
    try:
        return predict(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {exc}") from exc


@app.get("/soil-salinity/status")
def soil_salinity_mapper_status() -> dict[str, object]:
    return soil_salinity_status()


@app.post("/soil-salinity/generate-map")
def soil_salinity_mapper_generate_map(request: dict[str, object] | None = None) -> dict[str, object]:
    province = str((request or {}).get("province") or "Punjab and Sindh")
    try:
        return generate_soil_salinity_map(province=province)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Soil salinity map generation failed: {exc}") from exc


@app.get("/biosaline-crop-screening/status")
def biosaline_crop_screening_status() -> dict[str, object]:
    return biosaline_status()


@app.get("/biosaline-crop-screening/crops")
def biosaline_crop_screening_crops() -> dict[str, object]:
    try:
        return biosaline_crops()
    except BiosalineSetupError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Crop salinity crop metadata failed: {exc}") from exc


@app.post("/biosaline-crop-screening/predict")
def biosaline_crop_screening_predict(request: dict[str, object]) -> dict[str, object]:
    try:
        return biosaline_predict(request)
    except BiosalineSetupError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Crop salinity screening failed: {exc}") from exc
