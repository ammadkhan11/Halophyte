from __future__ import annotations

import json

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import graph_service
from model_loader import (
    MODEL_COMPARISON_PATH,
    MODEL_METRICS_PATH,
    NUMERIC_FIELDS,
    resources,
)
from prediction_service import predict
from schemas import Phase1ImportRequest, PredictionRequest, PredictionResponse, ReviewStatusRequest


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


@app.on_event("startup")
def initialize_graph() -> None:
    graph_service.ensure_graph_initialized()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "running",
        "message": "Halophyte Grass Dictionary backend is running with Phase 2 prediction and Phase 4 research evidence APIs.",
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


@app.get("/graph/overview")
def graph_overview() -> dict[str, int]:
    return graph_service.graph_overview()


@app.post("/graph/seed")
def seed_graph() -> dict[str, int]:
    try:
        return graph_service.seed_demo_graph()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Graph seed failed: {exc}") from exc


@app.post("/graph/import-phase1")
def import_phase1_dataset(request: Phase1ImportRequest | None = None) -> dict[str, int]:
    try:
        return graph_service.import_phase1_csv(request.csv_path if request else None)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Phase 1 import failed: {exc}") from exc


@app.get("/graph/entities")
def search_graph_entities(
    query: str = "",
    node_type: str | None = Query(default="All"),
) -> dict[str, object]:
    try:
        return graph_service.search_entities(query=query, node_type=node_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/graph/entities/{node_id}")
def graph_entity_details(node_id: int) -> dict[str, object]:
    try:
        return graph_service.entity_details(node_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/graph/evidence")
def graph_evidence(
    species: str = "",
    mechanism: str = "",
    gene: str = "",
    application: str = "",
    geography: str = "",
    status: str | None = Query(default="All"),
) -> list[dict[str, object]]:
    return graph_service.graph_evidence(
        species=species,
        mechanism=mechanism,
        gene=gene,
        application=application,
        geography=geography,
        status=status,
    )


@app.get("/graph/edges")
def graph_edges(status: str | None = Query(default="All")) -> list[dict[str, object]]:
    return graph_service.graph_edges(status=status)


@app.get("/graph/opportunities")
def graph_opportunities() -> list[dict[str, object]]:
    return graph_service.opportunities()


@app.post("/graph/review/{edge_id}")
def update_graph_review(edge_id: int, request: ReviewStatusRequest) -> dict[str, object]:
    try:
        return graph_service.update_review_status(edge_id, request.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
