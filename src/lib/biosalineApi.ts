export interface BiosalineCrop {
  crop_id: string;
  name: string;
  scientific_name: string;
  ec_threshold: number;
  gr50: number;
  slope: number;
  max_potential_yield: number;
  source: string;
  dataset_points: number;
  ec_range_tested: [number, number] | null;
  note: string;
}

export interface BiosalineDatasetStatus {
  available: boolean;
  path: string | null;
  rows?: number;
  columns?: string[];
  verification_guide?: string | null;
  species_count?: number;
  species?: string[];
  source_papers?: number;
  ec_range?: [number, number];
  message: string;
}

export interface BiosalineModelMetadata {
  model_type?: string;
  strategy?: string;
  overall_mean_r2?: number;
  test_r2?: number;
  total_data_points?: number;
  target_met?: boolean;
  species_metrics?: Record<
    string,
    {
      model_type?: string;
      r2?: number;
      mae_pct?: number;
      n_samples?: number;
    }
  >;
}

export interface BiosalineModelStatus {
  trained: boolean;
  model_path: string;
  encoder_path: string;
  metadata: BiosalineModelMetadata | null;
  message: string;
  train_command: string;
}

export interface BiosalineStatus {
  available: boolean;
  module_name: string;
  route: string;
  phase_root: string;
  config_loaded: boolean;
  setup_error: string;
  crop_count: number;
  primary_crop_count: number;
  dataset: BiosalineDatasetStatus;
  model: BiosalineModelStatus;
  no_profit_feature: boolean;
  scientific_note: string;
}

export interface BiosalineCropsResponse {
  primary_crops: BiosalineCrop[];
  all_crops: BiosalineCrop[];
  model: BiosalineModelStatus;
  dataset: BiosalineDatasetStatus;
}

export interface BiosalinePredictionRequest {
  crop_id: string;
  ec_soil: number;
  temperature: number;
  rainfall_mm: number;
}

export interface BiosalineAlternativeCrop {
  crop_id: string;
  name: string;
  scientific_name: string;
  gr50: number;
  ec_threshold: number;
  note: string;
}

export interface BiosalinePredictionValues {
  expected_yield_t_ha: number;
  relative_yield_pct: number;
  risk_level: 'Low' | 'Medium' | 'High' | string;
  recommended_irrigation: string;
  alternative_halophytes: BiosalineAlternativeCrop[];
  crop_name: string;
  max_potential_yield_kg_ha: number;
  model_used: string;
  model_r2: number | null;
  confidence: 'high' | 'medium' | 'low' | string;
}

export interface BiosalinePredictionResponse {
  inputs: BiosalinePredictionRequest & { salinity_basis: string };
  crop: BiosalineCrop;
  prediction: BiosalinePredictionValues;
  yield_curve: Array<{ ec_soil: number; relative_yield_pct: number }>;
  crop_comparisons: BiosalinePredictionValues[];
  model: BiosalineModelStatus;
  dataset: BiosalineDatasetStatus;
  warnings: string[];
  no_profit_feature: boolean;
  scientific_note: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

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

export function getBiosalineStatus() {
  return requestJson<BiosalineStatus>('/biosaline-crop-screening/status');
}

export function getBiosalineCrops() {
  return requestJson<BiosalineCropsResponse>('/biosaline-crop-screening/crops');
}

export function screenCropSalinity(payload: BiosalinePredictionRequest) {
  return requestJson<BiosalinePredictionResponse>('/biosaline-crop-screening/predict', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
