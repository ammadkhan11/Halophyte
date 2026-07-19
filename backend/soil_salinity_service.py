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

METADATA_PATH = OUTPUT_DIR / "generation_metadata.json"
ENV_PATHS = [
    PROJECT_ROOT / ".env",
    MODULE_DIR / ".env",
]

SCIENTIFIC_NOTICE = (
    "Local salinity grid and crop-zone output for the selected region."
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


def _env_value(key: str) -> str:
    current = os.environ.get(key, "").strip()
    if current:
        return current

    for env_path in ENV_PATHS:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name, value = stripped.split("=", 1)
            if name.strip() == key:
                return value.strip().strip('"').strip("'")
    return ""


def _generation_metadata() -> dict[str, Any]:
    if not METADATA_PATH.exists():
        return {}
    try:
        return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


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
    project = _env_value("EARTHENGINE_PROJECT")
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
            "configured": bool(project),
            "project": project,
            "python_executable": str(python_executable),
            "message": "Map service is preparing.",
        }

    if not project:
        return {
            "python_api_installed": True,
            "authenticated": False,
            "configured": False,
            "project": "",
            "python_executable": str(python_executable),
            "message": "Authentication required.",
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
            "configured": True,
            "project": project,
            "python_executable": str(python_executable),
            "message": "Authentication required.",
        }

    init_code = (
        "import ee, os\n"
        "project = os.environ.get('EARTHENGINE_PROJECT', '').strip()\n"
        "ee.Initialize(project=project)\n"
    )
    env = os.environ.copy()
    env["EARTHENGINE_PROJECT"] = project
    init_result = subprocess.run(
        [str(python_executable), "-c", init_code],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=env,
    )
    if init_result.returncode != 0:
        error_text = init_result.stderr.strip() or init_result.stdout.strip()
        return {
            "python_api_installed": True,
            "authenticated": False,
            "configured": True,
            "project": project,
            "python_executable": str(python_executable),
            "message": "Authentication required.",
        }

    return {
        "python_api_installed": True,
        "authenticated": True,
        "configured": True,
        "project": project,
        "python_executable": str(python_executable),
        "message": "Earth Engine initialized successfully.",
    }


def _generation_state(assets_ready: bool, map_ready: bool, mode: str) -> str:
    if map_ready and assets_ready:
        return "earth_engine_map_generated" if mode == "earth_engine" else "demo_map_generated"
    if assets_ready:
        return "assets_generated"
    return "not_generated_yet"


def soil_salinity_status() -> dict[str, Any]:
    assets = _asset_status()
    assets_ready = all(asset["exists"] for asset in assets)
    map_ready = GENERATED_MAP_PATH.exists()
    metadata = _generation_metadata()
    mode = str(metadata.get("mode") or "local_grid")
    return {
        "module_name": "Pakistan Soil Salinity Mapper",
        "scientific_notice": SCIENTIFIC_NOTICE,
        "earth_engine": _earth_engine_status(),
        "required_assets": assets,
        "assets_ready": assets_ready,
        "map_ready": map_ready,
        "generation_state": _generation_state(assets_ready, map_ready, mode),
        "data_mode": mode,
        "map_label": "Map available",
        "can_generate_demo": GENERATOR_SCRIPT.exists(),
        "map_url": "/modules/soil-salinity-mapping/generated-map.html" if map_ready else None,
        "local_app_path": str(MODULE_DIR / "app.py"),
        "generator_script_path": str(GENERATOR_SCRIPT),
        "output_dir": str(OUTPUT_DIR),
        "python_executable": sys.executable,
        "generator_python_executable": str(_generator_python()),
        "notebook_path": str(NOTEBOOK_PATH),
        "public_notebook_path": str(PUBLIC_NOTEBOOK_PATH),
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
    mode = str(metadata.get("mode") or "local_grid")
    metadata["generation_state"] = "earth_engine_map_generated" if mode == "earth_engine" else "demo_map_generated"
    metadata["map_label"] = "Map available"
    metadata["output_dir"] = str(OUTPUT_DIR)
    metadata["python_executable"] = str(python_executable)
    return metadata
