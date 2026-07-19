from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = PROJECT_ROOT / "integrated" / "soil-salinity-mapping"
OUTPUT_DIR = MODULE_DIR / "output"
PUBLIC_OUTPUT_DIR = PROJECT_ROOT / "public" / "modules" / "soil-salinity-mapping"
GENERATED_MAP_PATH = PUBLIC_OUTPUT_DIR / "generated-map.html"
GENERATOR_SCRIPT = MODULE_DIR / "generate_soil_salinity_map.py"
NOTEBOOK_PATH = PROJECT_ROOT / "mini-projects" / "soil-salinity-crop-zoning" / "Soil_Salinity_Mapping_FIXED.ipynb"
PUBLIC_NOTEBOOK_PATH = (
    PROJECT_ROOT
    / "public"
    / "modules"
    / "mini-projects"
    / "soil-salinity-crop-zoning"
    / "Soil_Salinity_Mapping_FIXED.ipynb"
)

REQUIRED_ASSETS = {
    "salinity_grid.csv": OUTPUT_DIR / "salinity_grid.csv",
    "pakistan_boundary.geojson": OUTPUT_DIR / "pakistan_boundary.geojson",
    "target_provinces.geojson": OUTPUT_DIR / "target_provinces.geojson",
    "soil_salinity_map.html": OUTPUT_DIR / "soil_salinity_map.html",
}

SCIENTIFIC_NOTICE = (
    "This mapper is a local application wrapper around satellite/region processing. "
    "EC prediction labels are placeholders until verified field EC measurements are supplied."
)


def _candidate_pythons() -> list[Path]:
    candidates: list[Path] = []
    env_python = os.environ.get("SOIL_SALINITY_PYTHON", "").strip()
    if env_python:
        candidates.append(Path(env_python))

    candidates.extend(
        [
            PROJECT_ROOT / ".venv" / "Scripts" / "python.exe",
            Path(sys.executable),
        ]
    )

    path_python = shutil.which("python")
    if path_python:
        candidates.append(Path(path_python))

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        key = str(resolved).lower()
        if key not in seen and resolved.exists():
            unique.append(resolved)
            seen.add(key)
    return unique


def _python_has_packages(python_executable: Path, packages: list[str]) -> bool:
    code = "import " + ", ".join(packages)
    result = subprocess.run(
        [str(python_executable), "-c", code],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    return result.returncode == 0


def _generator_python() -> Path:
    for python_executable in _candidate_pythons():
        if _python_has_packages(python_executable, ["folium", "numpy", "pandas"]):
            return python_executable
    return Path(sys.executable)


def _asset_status() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "exists": path.exists(),
            "path": str(path),
        }
        for name, path in REQUIRED_ASSETS.items()
    ]


def _earth_engine_status() -> dict[str, Any]:
    project = os.environ.get("EARTHENGINE_PROJECT", "").strip()
    python_executable = _generator_python()
    result = subprocess.run(
        [str(python_executable), "-c", "import importlib.util; raise SystemExit(0 if importlib.util.find_spec('ee') else 1)"],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if result.returncode != 0:
        return {
            "python_api_installed": False,
            "authenticated": False,
            "project": project,
            "python_executable": str(python_executable),
            "message": "Earth Engine Python API is not installed. Run python -m pip install -r integrated\\soil-salinity-mapping\\requirements.txt.",
        }

    credential_candidates = [
        Path.home() / ".config" / "earthengine" / "credentials",
    ]
    appdata = os.environ.get("APPDATA")
    if appdata:
        credential_candidates.append(Path(appdata) / "earthengine" / "credentials")

    if not any(path.exists() for path in credential_candidates):
        return {
            "python_api_installed": True,
            "authenticated": False,
            "project": project,
            "python_executable": str(python_executable),
            "message": "Earth Engine API is installed, but local credentials were not found. Run earthengine authenticate.",
        }

    init_code = (
        "import ee, os\n"
        "project = os.environ.get('EARTHENGINE_PROJECT', '').strip()\n"
        "ee.Initialize(project=project) if project else ee.Initialize()\n"
    )
    init_result = subprocess.run(
        [str(python_executable), "-c", init_code],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=os.environ.copy(),
    )
    if init_result.returncode != 0:
        error_text = init_result.stderr.strip() or init_result.stdout.strip()
        return {
            "python_api_installed": True,
            "authenticated": False,
            "project": project,
            "python_executable": str(python_executable),
            "message": f"Earth Engine is not authenticated or initialized: {error_text}",
        }

    return {
        "python_api_installed": True,
        "authenticated": True,
        "project": project,
        "python_executable": str(python_executable),
        "message": "Earth Engine initialized successfully.",
    }


def _generation_state(assets_ready: bool, map_ready: bool) -> str:
    if map_ready and assets_ready:
        return "map_generated"
    if assets_ready:
        return "assets_generated"
    return "not_generated_yet"


def soil_salinity_status() -> dict[str, Any]:
    assets = _asset_status()
    assets_ready = all(asset["exists"] for asset in assets)
    map_ready = GENERATED_MAP_PATH.exists()
    return {
        "module_name": "Pakistan Soil Salinity Mapper",
        "scientific_notice": SCIENTIFIC_NOTICE,
        "earth_engine": _earth_engine_status(),
        "required_assets": assets,
        "assets_ready": assets_ready,
        "map_ready": map_ready,
        "generation_state": _generation_state(assets_ready, map_ready),
        "can_generate_demo": GENERATOR_SCRIPT.exists(),
        "map_url": "/modules/soil-salinity-mapping/generated-map.html" if map_ready else None,
        "local_app_path": str(MODULE_DIR / "app.py"),
        "generator_script_path": str(GENERATOR_SCRIPT),
        "output_dir": str(OUTPUT_DIR),
        "python_executable": sys.executable,
        "generator_python_executable": str(_generator_python()),
        "notebook_path": str(NOTEBOOK_PATH),
        "public_notebook_path": str(PUBLIC_NOTEBOOK_PATH),
        "setup_commands": [
            "cd C:\\Users\\Ammad Khan\\Downloads\\halophyte_library_data_package",
            "python -m venv .venv",
            ".venv\\Scripts\\activate",
            "python -m pip install -r integrated\\soil-salinity-mapping\\requirements.txt",
            "python -c \"import ee; print('ee ok')\"",
            "earthengine authenticate",
            "python -m ee.cli.eecli authenticate",
            "$env:EARTHENGINE_PROJECT='your-google-cloud-project-id'",
            "cd backend",
            "python -m uvicorn main:app --host 127.0.0.1 --port 8000",
            "cd ..",
            "npm install",
            "npm run dev",
        ],
    }


def generate_soil_salinity_map(province: str = "Punjab and Sindh") -> dict[str, Any]:
    if not GENERATOR_SCRIPT.exists():
        raise FileNotFoundError(f"Soil salinity generator script was not found: {GENERATOR_SCRIPT}")

    python_executable = _generator_python()
    command = [
        str(python_executable),
        str(GENERATOR_SCRIPT),
        "--province",
        province,
    ]
    result = subprocess.run(
        command,
        cwd=str(MODULE_DIR),
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )

    if result.returncode != 0:
        error_text = result.stderr.strip() or result.stdout.strip() or f"Generator exited with code {result.returncode}."
        raise RuntimeError(error_text)

    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Generator completed but did not return JSON metadata. Output: {result.stdout}") from exc

    metadata["map_url"] = "/modules/soil-salinity-mapping/generated-map.html"
    metadata["generation_state"] = "map_generated"
    metadata["output_dir"] = str(OUTPUT_DIR)
    metadata["python_executable"] = str(python_executable)
    return metadata
