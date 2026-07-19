from __future__ import annotations

import json
import sys
import zipfile
from functools import lru_cache
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PHASE_OUTER_DIR = PROJECT_ROOT / "FYP-halophyte-No-Profit-Feature"
PHASE_DIR = PHASE_OUTER_DIR / "FYP-halophyte-No-Profit-Feature"
PHASE_SRC_DIR = PHASE_DIR / "src"
CONFIG_DIR = PHASE_DIR / "config"
MODELS_DIR = PHASE_DIR / "models"
DATASET_CANDIDATES = [
    PHASE_DIR / "data" / "raw" / "AuthenticHalophyteData.xlsx",
    PHASE_OUTER_DIR / "AuthenticHalophyteData.xlsx",
]
DATASET_GUIDE_PATH = PHASE_DIR / "data" / "raw" / "DATASET_VERIFICATION_GUIDE.md"
MODEL_PATH = MODELS_DIR / "surrogate_model.pkl"
ENCODER_PATH = MODELS_DIR / "species_encoder.pkl"
METADATA_PATH = MODELS_DIR / "model_metadata.json"


class BiosalineSetupError(RuntimeError):
    """Raised when the phase files or dependencies are not ready."""


def _ensure_phase_import_path() -> None:
    phase_path = str(PHASE_DIR)
    if phase_path not in sys.path:
        sys.path.insert(0, phase_path)


def _load_phase_modules() -> tuple[Any, Any]:
    if not PHASE_DIR.exists():
        raise BiosalineSetupError(f"Crop salinity phase folder was not found at {PHASE_DIR}.")

    _ensure_phase_import_path()
    try:
        from src.salinity_model import maas_hoffman
        from src.surrogate import predict
    except ModuleNotFoundError as exc:
        if exc.name == "yaml":
            raise BiosalineSetupError(
                "PyYAML is required for Crop Salinity Screening. Install backend requirements first."
            ) from exc
        raise BiosalineSetupError(f"Could not import Crop Salinity Screening modules: {exc}") from exc

    return maas_hoffman, predict


def _dataset_path() -> Path | None:
    return next((path for path in DATASET_CANDIDATES if path.exists()), None)


def _load_model_metadata() -> dict[str, Any] | None:
    if not METADATA_PATH.exists():
        return None
    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _column_index(cell_reference: str) -> int:
    letters = "".join(character for character in cell_reference if character.isalpha())
    index = 0
    for character in letters:
        index = index * 26 + (ord(character.upper()) - ord("A") + 1)
    return max(0, index - 1)


def _cell_text(cell: ElementTree.Element, shared_strings: list[str], namespace: dict[str, str]) -> str:
    value = cell.find("main:v", namespace)
    if cell.get("t") == "inlineStr":
        inline = cell.find("main:is/main:t", namespace)
        return inline.text if inline is not None and inline.text is not None else ""
    if value is None or value.text is None:
        return ""
    if cell.get("t") == "s":
        try:
            return shared_strings[int(value.text)]
        except (ValueError, IndexError):
            return ""
    return value.text


def _read_xlsx_records(path: Path) -> list[dict[str, str]]:
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("main:si", namespace):
                text_parts = [
                    text.text or ""
                    for text in item.findall(".//main:t", namespace)
                ]
                shared_strings.append("".join(text_parts))

        sheet_name = "xl/worksheets/sheet1.xml"
        if sheet_name not in archive.namelist():
            sheet_name = next(
                name for name in archive.namelist() if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
            )
        sheet_root = ElementTree.fromstring(archive.read(sheet_name))

    rows: list[list[str]] = []
    for row in sheet_root.findall(".//main:sheetData/main:row", namespace):
        values: list[str] = []
        for cell in row.findall("main:c", namespace):
            index = _column_index(cell.get("r", "A1"))
            while len(values) <= index:
                values.append("")
            values[index] = _cell_text(cell, shared_strings, namespace)
        rows.append(values)

    if not rows:
        return []

    headers = [header.strip() for header in rows[0]]
    records = []
    for values in rows[1:]:
        record = {
            header: values[index].strip() if index < len(values) else ""
            for index, header in enumerate(headers)
            if header
        }
        if any(record.values()):
            records.append(record)
    return records


def _dataset_summary_from_records(path: Path, records: list[dict[str, Any]], message: str) -> dict[str, Any]:
    columns = list(records[0].keys()) if records else []
    summary: dict[str, Any] = {
        "available": True,
        "path": str(path),
        "rows": len(records),
        "columns": columns,
        "verification_guide": str(DATASET_GUIDE_PATH) if DATASET_GUIDE_PATH.exists() else None,
        "message": message,
    }

    if "species_id" in columns:
        species = sorted({str(record["species_id"]) for record in records if record.get("species_id")})
        summary["species_count"] = len(species)
        summary["species"] = species
    if "source_reference" in columns:
        summary["source_papers"] = len({record["source_reference"] for record in records if record.get("source_reference")})
    if "ec_soil_dS_m" in columns:
        ec_values = []
        for record in records:
            try:
                ec_values.append(float(record["ec_soil_dS_m"]))
            except (TypeError, ValueError):
                continue
        if ec_values:
            summary["ec_range"] = [min(ec_values), max(ec_values)]

    return summary


@lru_cache(maxsize=1)
def _dataset_summary() -> dict[str, Any]:
    path = _dataset_path()
    if path is None:
        return {
            "available": False,
            "path": None,
            "message": "AuthenticHalophyteData.xlsx was not found in the phase data locations.",
        }

    try:
        df = pd.read_excel(path)
        records = df.to_dict(orient="records")
        return _dataset_summary_from_records(path, records, "Dataset loaded for provenance/status reporting.")
    except Exception as exc:
        try:
            records = _read_xlsx_records(path)
            return _dataset_summary_from_records(
                path,
                records,
                f"Dataset summarized with the built-in XLSX reader after pandas Excel loading was unavailable: {exc}",
            )
        except Exception as fallback_exc:
            return {
                "available": True,
                "path": str(path),
                "message": f"Dataset exists, but could not be summarized: {fallback_exc}",
            }


def _crop_record(crop_id: str, params: dict[str, Any]) -> dict[str, Any]:
    return {
        "crop_id": crop_id,
        "name": params.get("name", crop_id),
        "scientific_name": params.get("scientific_name", ""),
        "ec_threshold": params.get("ec_threshold"),
        "gr50": params.get("gr50"),
        "slope": params.get("slope"),
        "max_potential_yield": params.get("max_potential_yield"),
        "source": params.get("source", ""),
        "dataset_points": int(params.get("dataset_points", 0) or 0),
        "ec_range_tested": params.get("ec_range_tested"),
        "note": params.get("note", ""),
    }


def _model_status(predict_module: Any | None = None) -> dict[str, Any]:
    metadata = _load_model_metadata()
    trained = MODEL_PATH.exists() and ENCODER_PATH.exists()
    if predict_module is not None:
        try:
            trained = bool(predict_module.is_model_trained())
        except Exception:
            trained = MODEL_PATH.exists() and ENCODER_PATH.exists()

    train_command = (
        "cd FYP-halophyte-No-Profit-Feature\\FYP-halophyte-No-Profit-Feature "
        "&& python -m src.surrogate.train"
    )
    if trained:
        message = "Trained surrogate model files are available."
    elif metadata:
        message = "Model metadata exists, but surrogate_model.pkl/species_encoder.pkl are missing. Using Maas-Hoffman fallback."
    else:
        message = "No trained surrogate model files found. Using Maas-Hoffman fallback."

    return {
        "trained": trained,
        "model_path": str(MODEL_PATH),
        "encoder_path": str(ENCODER_PATH),
        "metadata": metadata,
        "message": message,
        "train_command": train_command,
    }


def biosaline_status() -> dict[str, Any]:
    setup_error = ""
    crop_count = 0
    primary_crop_count = 0
    predict_module = None

    try:
        maas_hoffman, predict_module = _load_phase_modules()
        crop_count = len(maas_hoffman.get_all_crops())
        primary_crop_count = len(maas_hoffman.get_primary_crops())
    except BiosalineSetupError as exc:
        setup_error = str(exc)

    return {
        "available": setup_error == "",
        "module_name": "Crop Salinity Screening",
        "route": "/crop-salinity-screening",
        "phase_root": str(PHASE_DIR),
        "config_loaded": setup_error == "",
        "setup_error": setup_error,
        "crop_count": crop_count,
        "primary_crop_count": primary_crop_count,
        "dataset": _dataset_summary(),
        "model": _model_status(predict_module),
        "no_profit_feature": True,
        "scientific_note": (
            "Outputs are model-based screening estimates from published Pakistani salinity-yield data "
            "and crop salinity parameters. They are not field-ready recommendations."
        ),
    }


def biosaline_crops() -> dict[str, Any]:
    maas_hoffman, predict_module = _load_phase_modules()
    all_crops = maas_hoffman.get_all_crops()
    primary_crops = maas_hoffman.get_primary_crops()
    return {
        "primary_crops": [_crop_record(crop_id, params) for crop_id, params in primary_crops.items()],
        "all_crops": [_crop_record(crop_id, params) for crop_id, params in all_crops.items()],
        "model": _model_status(predict_module),
        "dataset": _dataset_summary(),
    }


def biosaline_predict(request: dict[str, Any]) -> dict[str, Any]:
    maas_hoffman, predict_module = _load_phase_modules()

    crop_id = str(request.get("crop_id") or "").strip()
    if not crop_id:
        raise ValueError("Select a crop before running the salinity screening.")

    try:
        ec_soil = float(request.get("ec_soil"))
        temperature = float(request.get("temperature"))
        rainfall_mm = float(request.get("rainfall_mm"))
    except (TypeError, ValueError) as exc:
        raise ValueError("ECe, temperature, and rainfall must be numeric values.") from exc

    if ec_soil < 0:
        raise ValueError("Soil salinity cannot be negative.")

    result = predict_module.predict_yield(
        crop_id=crop_id,
        ec_soil=ec_soil,
        temperature=temperature,
        rainfall_mm=rainfall_mm,
    )
    crop_params = maas_hoffman.get_crop_params(crop_id)

    warnings: list[str] = []
    tested_range = crop_params.get("ec_range_tested")
    if tested_range and len(tested_range) == 2:
        low, high = float(tested_range[0]), float(tested_range[1])
        if ec_soil < low or ec_soil > high:
            warnings.append(
                f"ECe {ec_soil:g} dS/m is outside the local dataset range for this crop ({low:g}-{high:g} dS/m)."
            )
    if not predict_module.is_model_trained():
        warnings.append("Trained surrogate model files are missing; this run used the Maas-Hoffman formula fallback.")
    if result.get("confidence") == "low":
        warnings.append("Input conditions are mostly outside the training-data envelope, so confidence is low.")

    curve = []
    for step in range(0, 101):
        ec = step * 0.5
        try:
            curve_result = predict_module.predict_yield(crop_id, ec, temperature, rainfall_mm)
            relative_yield = curve_result["relative_yield_pct"]
        except Exception:
            relative_yield = maas_hoffman.calculate_relative_yield(
                ec, crop_params["ec_threshold"], crop_params["slope"]
            )
        curve.append({"ec_soil": ec, "relative_yield_pct": relative_yield})

    comparisons = predict_module.predict_multiple_crops(
        list(maas_hoffman.get_primary_crops().keys()),
        ec_soil=ec_soil,
        temperature=temperature,
        rainfall_mm=rainfall_mm,
    )

    return {
        "inputs": {
            "crop_id": crop_id,
            "ec_soil": ec_soil,
            "temperature": temperature,
            "rainfall_mm": rainfall_mm,
            "salinity_basis": "soil ECe / EC",
        },
        "crop": _crop_record(crop_id, crop_params),
        "prediction": result,
        "yield_curve": curve,
        "crop_comparisons": comparisons[:6],
        "model": _model_status(predict_module),
        "dataset": _dataset_summary(),
        "warnings": warnings,
        "no_profit_feature": True,
        "scientific_note": (
            "Screening estimates only. Validate with local soil tests, irrigation-water EC, cultivar response, "
            "and agronomist review before field decisions."
        ),
    }
