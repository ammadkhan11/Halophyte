const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export interface GraphOverview {
  papers: number;
  nodes: number;
  edges: number;
  pending: number;
}

export interface GraphEntity {
  id: number;
  node_type: string;
  display_name: string;
  canonical_name: string;
  attributes: Record<string, unknown>;
}

export interface EvidenceEdge {
  id: number;
  source_id: number;
  source_name: string;
  source_type: string | null;
  target_id: number;
  target_name: string;
  target_type: string | null;
  relation_type: string;
  numeric_value: number | null;
  unit: string | null;
  evidence_quote: string;
  confidence: number;
  review_status: string;
  paper_external_id: string | null;
  paper_title: string | null;
  paper_url: string | null;
  has_literature_provenance: boolean;
}

export interface EntitySearchResponse {
  entity_types: string[];
  entities: GraphEntity[];
}

export interface EntityDetailsResponse {
  entity: GraphEntity;
  evidence: EvidenceEdge[];
}

export interface ResearchOpportunity {
  kind: string;
  subject: string;
  score: number;
  reason: string;
  next_step: string;
}

export interface GraphFilters {
  species?: string;
  mechanism?: string;
  gene?: string;
  application?: string;
  geography?: string;
  status?: string;
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

function toQueryString(params: Array<[string, string | undefined]>) {
  const search = new URLSearchParams();
  params.forEach(([key, value]) => {
    if (value && value.trim()) {
      search.set(key, value.trim());
    }
  });
  const query = search.toString();
  return query ? `?${query}` : '';
}

export function getGraphOverview() {
  return requestJson<GraphOverview>('/graph/overview');
}

export function seedGraph() {
  return requestJson<GraphOverview>('/graph/seed', { method: 'POST' });
}

export function importPhase1Csv() {
  return requestJson<Record<string, number>>('/graph/import-phase1', {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

export function searchEntities(query: string, nodeType: string) {
  return requestJson<EntitySearchResponse>(`/graph/entities${toQueryString([['query', query], ['node_type', nodeType]])}`);
}

export function getEntityDetails(id: number) {
  return requestJson<EntityDetailsResponse>(`/graph/entities/${id}`);
}

export function getEvidence(filters: GraphFilters) {
  return requestJson<EvidenceEdge[]>(`/graph/evidence${toQueryString([
    ['species', filters.species],
    ['mechanism', filters.mechanism],
    ['gene', filters.gene],
    ['application', filters.application],
    ['geography', filters.geography],
    ['status', filters.status],
  ])}`);
}

export function getGraphEdges(status = 'All') {
  return requestJson<EvidenceEdge[]>(`/graph/edges${toQueryString([['status', status]])}`);
}

export function getResearchOpportunities() {
  return requestJson<ResearchOpportunity[]>('/graph/opportunities');
}

export function updateReviewStatus(edgeId: number, status: 'approved' | 'rejected' | 'pending' | 'needs_source_review') {
  return requestJson<EvidenceEdge>(`/graph/review/${edgeId}`, {
    method: 'POST',
    body: JSON.stringify({ status }),
  });
}
