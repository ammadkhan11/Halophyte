import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Database,
  FileText,
  Filter,
  GitBranch,
  Loader2,
  Network,
  RefreshCw,
  Search,
  ShieldCheck,
  TableProperties,
  XCircle,
} from 'lucide-react';
import {
  getEntityDetails,
  getEvidence,
  getGraphEdges,
  getGraphOverview,
  getResearchOpportunities,
  importPhase1Csv,
  searchEntities,
  seedGraph,
  updateReviewStatus,
  type EntityDetailsResponse,
  type EvidenceEdge,
  type GraphEntity,
  type GraphFilters,
  type GraphOverview,
  type ResearchOpportunity,
} from '../lib/researchApi';

type EvidenceTab = 'overview' | 'explorer' | 'graph' | 'opportunities' | 'review';

type ResearchEvidenceProps = {
  initialSpecies?: string;
  initialMechanism?: string;
};

const EMPTY_OVERVIEW: GraphOverview = {
  papers: 0,
  nodes: 0,
  edges: 0,
  pending: 0,
};

const STATUS_OPTIONS = ['All', 'approved', 'demo_reviewed', 'dataset_import', 'pending', 'needs_source_review', 'rejected'];

function statusLabel(status: string) {
  return status.replace(/_/g, ' ');
}

function relationshipLabel(edge: EvidenceEdge) {
  return `${edge.source_name} - ${edge.relation_type.replace(/_/g, ' ')} -> ${edge.target_name}`;
}

function uniqueGraphNodes(edges: EvidenceEdge[]) {
  const nodes = new Map<number, { id: number; name: string; type: string | null }>();
  edges.forEach((edge) => {
    nodes.set(edge.source_id, { id: edge.source_id, name: edge.source_name, type: edge.source_type });
    nodes.set(edge.target_id, { id: edge.target_id, name: edge.target_name, type: edge.target_type });
  });
  return Array.from(nodes.values());
}

function EvidenceCard({ edge, focusEntityId }: { edge: EvidenceEdge; focusEntityId?: number }) {
  const linkedEntity = focusEntityId
    ? edge.source_id === focusEntityId
      ? edge.target_name
      : edge.source_name
    : `${edge.source_name} -> ${edge.target_name}`;

  return (
    <article className="evidence-card">
      <div className="evidence-card-header">
        <div>
          <p className="eyebrow">Literature evidence</p>
          <h3>{edge.relation_type.replace(/_/g, ' ')}</h3>
        </div>
        <span className={`review-badge review-badge-${edge.review_status.replace(/_/g, '-')}`}>
          {statusLabel(edge.review_status)}
        </span>
      </div>

      <dl className="evidence-metadata">
        <div>
          <dt>Linked entity</dt>
          <dd>{linkedEntity}</dd>
        </div>
        <div>
          <dt>Confidence</dt>
          <dd>{edge.confidence.toFixed(2)}</dd>
        </div>
      </dl>

      <blockquote>{edge.evidence_quote}</blockquote>

      <div className="evidence-source">
        <span>{edge.paper_title ?? 'Source record unavailable'}</span>
        {edge.paper_url ? (
          <a href={edge.paper_url} target="_blank" rel="noreferrer">
            {edge.paper_external_id ?? 'Open source'}
          </a>
        ) : (
          <span>{edge.paper_external_id ?? 'No source link'}</span>
        )}
      </div>
    </article>
  );
}

function GraphMap({ edges }: { edges: EvidenceEdge[] }) {
  const nodes = useMemo(() => uniqueGraphNodes(edges), [edges]);
  const positions = useMemo(() => {
    const radiusX = 330;
    const radiusY = 150;
    const centerX = 450;
    const centerY = 215;
    const map = new Map<number, { x: number; y: number }>();

    nodes.forEach((node, index) => {
      const angle = nodes.length <= 1 ? 0 : (2 * Math.PI * index) / nodes.length;
      map.set(node.id, {
        x: centerX + radiusX * Math.cos(angle),
        y: centerY + radiusY * Math.sin(angle),
      });
    });

    return map;
  }, [nodes]);

  if (edges.length === 0) {
    return (
      <div className="empty-state">
        <h3>No graph relationships</h3>
        <p>Seed the graph or adjust filters to show connected evidence.</p>
      </div>
    );
  }

  return (
    <div className="graph-map-shell" aria-label="Knowledge graph visualization">
      <svg viewBox="0 0 900 430" role="img">
        <title>Research evidence graph map</title>
        {edges.map((edge) => {
          const source = positions.get(edge.source_id);
          const target = positions.get(edge.target_id);
          if (!source || !target) {
            return null;
          }
          const midX = (source.x + target.x) / 2;
          const midY = (source.y + target.y) / 2;
          return (
            <g key={edge.id}>
              <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} />
              <text x={midX} y={midY - 6} textAnchor="middle">
                {edge.relation_type.replace(/_/g, ' ')}
              </text>
            </g>
          );
        })}
        {nodes.map((node) => {
          const position = positions.get(node.id);
          if (!position) {
            return null;
          }
          return (
            <g key={node.id}>
              <circle cx={position.x} cy={position.y} r="34" />
              <text x={position.x} y={position.y - 4} textAnchor="middle">
                {node.name.length > 22 ? `${node.name.slice(0, 20)}...` : node.name}
              </text>
              <text className="graph-node-type" x={position.x} y={position.y + 13} textAnchor="middle">
                {node.type}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export default function ResearchEvidence({ initialSpecies = '', initialMechanism = '' }: ResearchEvidenceProps) {
  const [activeTab, setActiveTab] = useState<EvidenceTab>('overview');
  const [overview, setOverview] = useState<GraphOverview>(EMPTY_OVERVIEW);
  const [filters, setFilters] = useState<Required<GraphFilters>>({
    species: initialSpecies,
    mechanism: initialMechanism,
    gene: '',
    application: '',
    geography: '',
    status: 'All',
  });
  const [entityQuery, setEntityQuery] = useState('');
  const [entityType, setEntityType] = useState('All');
  const [entityTypes, setEntityTypes] = useState<string[]>([]);
  const [entities, setEntities] = useState<GraphEntity[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<EntityDetailsResponse | null>(null);
  const [evidence, setEvidence] = useState<EvidenceEdge[]>([]);
  const [allEdges, setAllEdges] = useState<EvidenceEdge[]>([]);
  const [opportunities, setOpportunities] = useState<ResearchOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const pendingReview = allEdges.filter((edge) => edge.review_status === 'pending' || edge.review_status === 'needs_source_review');

  async function loadGraphData(nextFilters = filters) {
    setLoading(true);
    setError('');
    try {
      const [counts, entityResults, filteredEvidence, edges, leads] = await Promise.all([
        getGraphOverview(),
        searchEntities(entityQuery, entityType),
        getEvidence(nextFilters),
        getGraphEdges('All'),
        getResearchOpportunities(),
      ]);
      setOverview(counts);
      setEntityTypes(entityResults.entity_types);
      setEntities(entityResults.entities);
      setEvidence(filteredEvidence);
      setAllEdges(edges);
      setOpportunities(leads);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Research evidence could not be loaded.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const nextFilters = {
      species: initialSpecies,
      mechanism: initialMechanism,
      gene: '',
      application: '',
      geography: '',
      status: 'All',
    };
    setFilters(nextFilters);
    if (initialSpecies || initialMechanism) {
      setActiveTab('explorer');
    }
    loadGraphData(nextFilters);
  }, [initialSpecies, initialMechanism]);

  useEffect(() => {
    let isActive = true;

    async function runSearch() {
      try {
        const result = await searchEntities(entityQuery, entityType);
        if (isActive) {
          setEntityTypes(result.entity_types);
          setEntities(result.entities);
        }
      } catch {
        if (isActive) {
          setEntities([]);
        }
      }
    }

    runSearch();
    return () => {
      isActive = false;
    };
  }, [entityQuery, entityType]);

  async function handleFilterSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadGraphData(filters);
    setActiveTab('explorer');
  }

  async function handleSelectEntity(entityId: number) {
    setError('');
    try {
      const details = await getEntityDetails(entityId);
      setSelectedEntity(details);
      setActiveTab('explorer');
    } catch (detailsError) {
      setError(detailsError instanceof Error ? detailsError.message : 'Entity details could not be loaded.');
    }
  }

  async function handleSeed() {
    setActionLoading('seed');
    setNotice('');
    setError('');
    try {
      const counts = await seedGraph();
      setOverview(counts);
      setNotice('Demonstration graph loaded. Demo records remain labelled as demonstration/review data.');
      await loadGraphData(filters);
    } catch (seedError) {
      setError(seedError instanceof Error ? seedError.message : 'Graph seed failed.');
    } finally {
      setActionLoading('');
    }
  }

  async function handleImportPhase1() {
    setActionLoading('import');
    setNotice('');
    setError('');
    try {
      const result = await importPhase1Csv();
      setNotice(`Imported ${result.species ?? 0} species, ${result.mechanisms ?? 0} mechanisms, and ${result.thresholds ?? 0} GR50 backbone records from Phase 1.`);
      await loadGraphData(filters);
    } catch (importError) {
      setError(importError instanceof Error ? importError.message : 'Phase 1 import failed.');
    } finally {
      setActionLoading('');
    }
  }

  async function handleReview(edgeId: number, status: 'approved' | 'rejected') {
    setActionLoading(`${status}-${edgeId}`);
    setError('');
    try {
      await updateReviewStatus(edgeId, status);
      await loadGraphData(filters);
    } catch (reviewError) {
      setError(reviewError instanceof Error ? reviewError.message : 'Review update failed.');
    } finally {
      setActionLoading('');
    }
  }

  return (
    <main className="library-page research-page">
      <header className="page-hero">
        <div>
          <p className="eyebrow">Phase 4 Research Evidence</p>
          <h1>Halophyte Research Knowledge Graph</h1>
          <p className="page-subtitle">
            Citation-backed relationships between species, mechanisms, genes, applications, geography, and salinity thresholds.
          </p>
        </div>
      </header>

      <section className="safeguard-banner" aria-label="Evidence safeguards">
        <ShieldCheck aria-hidden="true" size={21} />
        <p>
          Literature relationships keep source provenance and exact supporting quotes. Demonstration records are review data, and research opportunities are research leads based on graph coverage.
        </p>
      </section>

      {error ? (
        <div className="error-message" role="alert">
          <AlertCircle aria-hidden="true" size={18} />
          {error}
        </div>
      ) : null}

      {notice ? (
        <div className="inline-status">
          <CheckCircle2 aria-hidden="true" size={18} />
          {notice}
        </div>
      ) : null}

      <div className="research-toolbar">
        <div className="mode-selector research-tabs" role="tablist" aria-label="Research evidence views">
          {[
            ['overview', 'Overview'],
            ['explorer', 'Evidence'],
            ['graph', 'Graph'],
            ['opportunities', 'Opportunities'],
            ['review', 'Review'],
          ].map(([value, label]) => (
            <button
              className={activeTab === value ? 'mode-button mode-button-active' : 'mode-button'}
              key={value}
              type="button"
              onClick={() => setActiveTab(value as EvidenceTab)}
            >
              {label}
            </button>
          ))}
        </div>
        <button className="secondary-button" type="button" onClick={() => loadGraphData(filters)} disabled={loading}>
          {loading ? <Loader2 aria-hidden="true" size={16} /> : <RefreshCw aria-hidden="true" size={16} />}
          Refresh
        </button>
      </div>

      <form className="library-controls research-filters" onSubmit={handleFilterSubmit}>
        <div className="section-heading">
          <div>
            <p className="eyebrow">Search and Filter</p>
            <h2>Find literature evidence</h2>
          </div>
          <Filter aria-hidden="true" size={21} />
        </div>
        <div className="filters-grid research-filter-grid">
          {(['species', 'mechanism', 'gene', 'application', 'geography'] as const).map((field) => (
            <label className="filter-field" key={field}>
              <span>{field}</span>
              <input
                value={filters[field]}
                placeholder={`Filter by ${field}`}
                onChange={(event) => setFilters((current) => ({ ...current, [field]: event.target.value }))}
              />
            </label>
          ))}
          <label className="filter-field">
            <span>Review status</span>
            <select value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
              {STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {statusLabel(status)}
                </option>
              ))}
            </select>
          </label>
        </div>
        <button className="primary-button" type="submit">
          <Search aria-hidden="true" size={17} />
          Apply Filters
        </button>
      </form>

      {loading ? (
        <div className="inline-status">
          <Loader2 aria-hidden="true" size={18} />
          Loading research evidence...
        </div>
      ) : null}

      {activeTab === 'overview' ? (
        <section className="research-section">
          <div className="stats-grid">
            <article className="stat-card">
              <span className="stat-icon"><FileText aria-hidden="true" size={19} /></span>
              <p>Provenance records</p>
              <strong>{overview.papers}</strong>
              <span>Literature and project dataset sources</span>
            </article>
            <article className="stat-card">
              <span className="stat-icon"><Database aria-hidden="true" size={19} /></span>
              <p>Entities</p>
              <strong>{overview.nodes}</strong>
              <span>Species, genes, mechanisms, geography, applications</span>
            </article>
            <article className="stat-card">
              <span className="stat-icon"><GitBranch aria-hidden="true" size={19} /></span>
              <p>Relationships</p>
              <strong>{overview.edges}</strong>
              <span>Every edge keeps evidence text</span>
            </article>
            <article className="stat-card">
              <span className="stat-icon"><ShieldCheck aria-hidden="true" size={19} /></span>
              <p>Pending review</p>
              <strong>{overview.pending}</strong>
              <span>Claims awaiting manual decision</span>
            </article>
          </div>

          <section className="prediction-layout">
            <div className="prediction-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Initialization</p>
                  <h2>Graph data actions</h2>
                </div>
              </div>
              <div className="research-action-row">
                <button className="secondary-button" type="button" onClick={handleSeed} disabled={actionLoading === 'seed'}>
                  {actionLoading === 'seed' ? <Loader2 aria-hidden="true" size={16} /> : <Database aria-hidden="true" size={16} />}
                  Seed Demo Graph
                </button>
                <button className="secondary-button" type="button" onClick={handleImportPhase1} disabled={actionLoading === 'import'}>
                  {actionLoading === 'import' ? <Loader2 aria-hidden="true" size={16} /> : <TableProperties aria-hidden="true" size={16} />}
                  Import Phase 1 CSV
                </button>
              </div>
              <p className="mode-helper-text">
                The seed is clearly labelled demonstration/review data. Phase 1 import adds species, mechanisms, and GR50 values as project-data backbone records.
              </p>
            </div>
            <div className="prediction-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Quality rule</p>
                  <h2>Evidence safeguards</h2>
                </div>
              </div>
              <p className="mode-helper-text">
                OpenAI extraction is optional and server-side only. Unsupported extracted claims should be rejected in the review queue, and prediction values remain separate from literature evidence.
              </p>
            </div>
          </section>
        </section>
      ) : null}

      {activeTab === 'explorer' ? (
        <section className="research-layout">
          <aside className="entity-browser">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Entities</p>
                <h2>Search graph</h2>
              </div>
            </div>
            <label className="filter-field">
              <span>Search entity</span>
              <input value={entityQuery} placeholder="Species, gene, mechanism" onChange={(event) => setEntityQuery(event.target.value)} />
            </label>
            <label className="filter-field">
              <span>Entity type</span>
              <select value={entityType} onChange={(event) => setEntityType(event.target.value)}>
                <option value="All">All</option>
                {entityTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
            </label>
            <div className="entity-list">
              {entities.length > 0 ? (
                entities.slice(0, 18).map((entity) => (
                  <button key={entity.id} type="button" onClick={() => handleSelectEntity(entity.id)}>
                    <strong>{entity.display_name}</strong>
                    <span>{entity.node_type}</span>
                  </button>
                ))
              ) : (
                <p>No matching entities.</p>
              )}
            </div>
          </aside>

          <section className="evidence-results">
            {selectedEntity ? (
              <>
                <div className="results-header">
                  <div>
                    <p className="eyebrow">Entity details</p>
                    <h2>{selectedEntity.entity.display_name}</h2>
                  </div>
                  <span className="result-count">{selectedEntity.evidence.length} evidence links</span>
                </div>
                {selectedEntity.evidence.length > 0 ? (
                  <div className="evidence-grid">
                    {selectedEntity.evidence.map((edge) => (
                      <EvidenceCard edge={edge} focusEntityId={selectedEntity.entity.id} key={edge.id} />
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <h3>No evidence links</h3>
                    <p>This entity exists in the graph but has no relationships yet.</p>
                  </div>
                )}
              </>
            ) : (
              <>
                <div className="results-header">
                  <div>
                    <p className="eyebrow">Filtered relationships</p>
                    <h2>Evidence relationship cards</h2>
                  </div>
                  <span className="result-count">{evidence.length} shown</span>
                </div>
                {evidence.length > 0 ? (
                  <div className="evidence-grid">
                    {evidence.map((edge) => (
                      <EvidenceCard edge={edge} key={edge.id} />
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">
                    <h3>No evidence found</h3>
                    <p>Adjust filters, seed the graph, or import Phase 1 CSV data.</p>
                  </div>
                )}
              </>
            )}
          </section>
        </section>
      ) : null}

      {activeTab === 'graph' ? (
        <section className="research-section">
          <div className="results-header">
            <div>
              <p className="eyebrow">Graph Visualization</p>
              <h2>Evidence network map</h2>
            </div>
            <span className="result-count">{evidence.length} filtered relationships</span>
          </div>
          <GraphMap edges={evidence.length > 0 ? evidence : allEdges} />
        </section>
      ) : null}

      {activeTab === 'opportunities' ? (
        <section className="research-section">
          <div className="results-header">
            <div>
              <p className="eyebrow">Research opportunities</p>
              <h2>Research leads based on graph coverage</h2>
            </div>
            <span className="result-count">{opportunities.length} leads</span>
          </div>
          {opportunities.length > 0 ? (
            <div className="table-shell">
              <table className="grass-table opportunities-table">
                <thead>
                  <tr>
                    <th>Lead type</th>
                    <th>Subject</th>
                    <th>Coverage score</th>
                    <th>Reason</th>
                    <th>Next validation action</th>
                  </tr>
                </thead>
                <tbody>
                  {opportunities.map((item) => (
                    <tr key={`${item.kind}-${item.subject}`}>
                      <td>{item.kind}</td>
                      <td>{item.subject}</td>
                      <td>{item.score}</td>
                      <td>{item.reason}</td>
                      <td>{item.next_step}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <h3>No coverage leads yet</h3>
              <p>Add approved, demonstration, or dataset relationships to generate transparent coverage leads.</p>
            </div>
          )}
        </section>
      ) : null}

      {activeTab === 'review' ? (
        <section className="research-section">
          <div className="results-header">
            <div>
              <p className="eyebrow">Manual review queue</p>
              <h2>Approve or reject pending claims</h2>
            </div>
            <span className="result-count">{pendingReview.length} pending</span>
          </div>
          {pendingReview.length > 0 ? (
            <div className="evidence-grid">
              {pendingReview.map((edge) => (
                <article className="evidence-card" key={edge.id}>
                  <div className="evidence-card-header">
                    <div>
                      <p className="eyebrow">Needs source review</p>
                      <h3>{relationshipLabel(edge)}</h3>
                    </div>
                    <span className={`review-badge review-badge-${edge.review_status.replace(/_/g, '-')}`}>
                      {statusLabel(edge.review_status)}
                    </span>
                  </div>
                  <blockquote>{edge.evidence_quote}</blockquote>
                  <div className="evidence-source">
                    <span>{edge.paper_title ?? 'Source record unavailable'}</span>
                    {edge.paper_url ? (
                      <a href={edge.paper_url} target="_blank" rel="noreferrer">
                        {edge.paper_external_id ?? 'Open source'}
                      </a>
                    ) : null}
                  </div>
                  <div className="review-actions">
                    <button className="secondary-button" type="button" onClick={() => handleReview(edge.id, 'approved')} disabled={actionLoading === `approved-${edge.id}`}>
                      {actionLoading === `approved-${edge.id}` ? <Loader2 aria-hidden="true" size={16} /> : <CheckCircle2 aria-hidden="true" size={16} />}
                      Approve
                    </button>
                    <button className="secondary-button" type="button" onClick={() => handleReview(edge.id, 'rejected')} disabled={actionLoading === `rejected-${edge.id}`}>
                      {actionLoading === `rejected-${edge.id}` ? <Loader2 aria-hidden="true" size={16} /> : <XCircle aria-hidden="true" size={16} />}
                      Reject
                    </button>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <h3>Review queue is clear</h3>
              <p>No pending or needs-source-review relationships are currently waiting.</p>
            </div>
          )}
        </section>
      ) : null}

      <section className="references-section">
        <h3>Evidence distinction</h3>
        <p>
          Phase 2 model output is labelled as predicted values. Phase 4 graph records are literature evidence or project-data backbone records with source provenance and review status.
        </p>
      </section>
    </main>
  );
}
