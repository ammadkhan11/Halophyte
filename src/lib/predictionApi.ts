export type PredictionMode = 'grass_based' | 'mechanism_based';

export interface GrassOption {
  species: string;
  common_name: string;
  mechanism: string;
}

export interface PredictionMetadata {
  numeric_fields: string[];
  mechanism_options: string[];
  prediction_modes: PredictionMode[];
  available_species: GrassOption[];
}

export interface PredictionRequest {
  mode: PredictionMode;
  species: string | null;
  mechanism: string | null;
  known_field: string;
  known_value: number;
}

export interface SimilarGrass {
  species: string;
  common_name: string;
  mechanism: string;
  similarity_note: string;
}

export interface PredictionResponse {
  mode: PredictionMode;
  species: string | null;
  mechanism: string;
  known_field: string;
  known_value: number;
  dataset_known_value: number | null;
  difference: number | null;
  difference_percent: number | null;
  known_value_comparison: {
    dataset_known_value: number;
    user_known_value: number;
    difference: number;
    difference_percent: number | null;
  } | null;
  calculation_basis: {
    base_species_profile: boolean;
    regression_scope: string;
    method: string;
  } | null;
  predictions: Record<string, number>;
  similar_grasses: SimilarGrass[];
  model_used: string;
  note: string;
}

export interface ModelMetricRow {
  known_input_field: string;
  model_name: string;
  target_fields: string;
  average_mae: number;
  average_rmse: number;
  average_r2: number;
}

export interface ModelMetricsResponse {
  message?: string;
  comparison_results?: ModelMetricRow[];
  metrics_summary?: {
    overall_model_ranking?: Array<{
      model_name: string;
      average_mae: number;
      average_rmse: number;
      average_r2: number;
    }>;
    selected_model_per_known_input_for_app?: Array<{
      known_input_field: string;
      metric_best_model: string;
      selected_model_for_app: string;
      selected_model_rmse: number;
    }>;
  };
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

export function getPredictionMetadata() {
  return requestJson<PredictionMetadata>('/metadata');
}

export function getGrassOptions() {
  return requestJson<GrassOption[]>('/grasses');
}

export function predictValues(payload: PredictionRequest) {
  return requestJson<PredictionResponse>('/predict', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function getModelMetrics() {
  return requestJson<ModelMetricsResponse>('/model-metrics');
}
