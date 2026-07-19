const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export interface SoilSalinityAsset {
  name: string;
  exists: boolean;
  path: string;
}

export interface EarthEngineStatus {
  python_api_installed: boolean;
  authenticated: boolean;
  project: string;
  message: string;
}

export interface SoilSalinityStatus {
  module_name: string;
  scientific_notice: string;
  earth_engine: EarthEngineStatus;
  required_assets: SoilSalinityAsset[];
  assets_ready: boolean;
  map_ready: boolean;
  generation_state: 'not_generated_yet' | 'assets_generated' | 'map_generated';
  can_generate_demo: boolean;
  map_url: string | null;
  local_app_path: string;
  generator_script_path: string;
  output_dir: string;
  python_executable: string;
  notebook_path: string;
  public_notebook_path: string;
  setup_commands: string[];
}

export interface SoilSalinityMapResult {
  status: string;
  mode: string;
  province: string;
  selected_provinces: string[];
  points_rendered: number;
  total_points: number;
  map_url: string;
  generation_state: string;
  output_dir: string;
  python_executable: string;
  scientific_notice: string;
  outputs: Record<string, string>;
}

async function requestJson<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const errorBody = await response.json();
      message = errorBody.detail ?? message;
    } catch {
      // Keep the default message when the backend does not return JSON.
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export function getSoilSalinityStatus() {
  return requestJson<SoilSalinityStatus>('/soil-salinity/status');
}

export function generateSoilSalinityMap(province: string) {
  return requestJson<SoilSalinityMapResult>('/soil-salinity/generate-map', {
    method: 'POST',
    body: JSON.stringify({ province }),
  });
}
