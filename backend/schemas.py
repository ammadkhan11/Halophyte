from typing import Literal

from pydantic import BaseModel, Field


PredictionMode = Literal["grass_based", "mechanism_based"]


class PredictionRequest(BaseModel):
    mode: PredictionMode
    species: str | None = None
    mechanism: str | None = None
    known_field: str
    known_value: float = Field(..., description="Known numeric value entered by the student.")


class SimilarGrass(BaseModel):
    species: str
    common_name: str
    mechanism: str
    similarity_note: str


class KnownValueComparison(BaseModel):
    dataset_known_value: float
    user_known_value: float
    difference: float
    difference_percent: float | None


class CalculationBasis(BaseModel):
    base_species_profile: bool
    regression_scope: str
    method: str


class PredictionResponse(BaseModel):
    mode: str
    species: str | None
    mechanism: str
    known_field: str
    known_value: float
    dataset_known_value: float | None = None
    difference: float | None = None
    difference_percent: float | None = None
    known_value_comparison: KnownValueComparison | None = None
    calculation_basis: CalculationBasis | None = None
    predictions: dict[str, float]
    similar_grasses: list[SimilarGrass]
    model_used: str
    note: str


class Phase1ImportRequest(BaseModel):
    csv_path: str | None = Field(
        default=None,
        description="Optional server-side CSV path. Defaults to ml/data/halophyte_grass_library.csv.",
    )


class ReviewStatusRequest(BaseModel):
    status: Literal["approved", "rejected", "pending", "needs_source_review"]
