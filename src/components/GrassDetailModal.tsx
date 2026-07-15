import { useEffect } from 'react';
import { FileSearch, X } from 'lucide-react';
import type { GrassLibraryRecord } from '../data/grassLibraryData';
import { cleanDisplayText, formatIonValue, formatNumber, formatRange } from '../utils/grassFormatters';

type GrassDetailModalProps = {
  grass: GrassLibraryRecord;
  onClose: () => void;
  onViewResearchEvidence: (grass: GrassLibraryRecord) => void;
};

export default function GrassDetailModal({ grass, onClose, onViewResearchEvidence }: GrassDetailModalProps) {
  useEffect(() => {
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleEscape);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener('keydown', handleEscape);
    };
  }, [onClose]);

  const details = [
    ['Grass Species', cleanDisplayText(grass.species_full_name)],
    ['Common Name', cleanDisplayText(grass.common_name)],
    ['Mechanism', grass.mechanism],
    ['GR50 Min', `${formatNumber(grass.gr50_min_ds_m)} dS/m`],
    ['GR50 Max', `${formatNumber(grass.gr50_max_ds_m)} dS/m`],
    ['GR50 Average', `${formatNumber(grass.gr50_avg_ds_m)} dS/m`],
    ['Na+ Shoot', formatIonValue(grass.na_shoot_mmol_kg_dw, grass.na_shoot_level)],
    ['Na+ Root', formatIonValue(grass.na_root_mmol_kg_dw, grass.na_root_level)],
    ['Cl- Shoot', formatIonValue(grass.cl_shoot_mmol_kg_dw, grass.cl_shoot_level)],
    ['Cl- Root', formatIonValue(grass.cl_root_mmol_kg_dw, grass.cl_root_level)],
    ['K+ Shoot', formatIonValue(grass.k_shoot_mmol_kg_dw, grass.k_shoot_level)],
    ['K+ Root', formatIonValue(grass.k_root_mmol_kg_dw, grass.k_root_level)],
    ['Salt tolerance level', grass.salt_tolerance_level],
  ];

  const references = [
    ['Primary references', grass.primary_references],
    ['Empirical references', grass.empirical_references],
  ].filter(([, value]) => value.trim().length > 0);

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="grass-detail-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <p className="source-number">Record {grass.source_no}</p>
            <h2 id="grass-detail-title">{cleanDisplayText(grass.common_name)}</h2>
            <p className="scientific-name">{cleanDisplayText(grass.scientific_name)}</p>
          </div>
          <button className="icon-button" type="button" aria-label="Close details" onClick={onClose}>
            <X aria-hidden="true" size={20} />
          </button>
        </div>

        <div className="modal-summary">
          <span className={`status-pill ${grass.is_salt_secreting ? 'status-pill-secreting' : 'status-pill-nonsecreting'}`}>
            {grass.mechanism}
          </span>
          <span>{grass.salt_tolerance_level} tolerance</span>
          <span>{formatRange(grass.gr50_min_ds_m, grass.gr50_max_ds_m)}</span>
        </div>

        <section className="research-link-panel" aria-label="Research evidence shortcut">
          <div>
            <p className="eyebrow">Phase 4</p>
            <h3>Research evidence</h3>
            <p>Open literature-backed graph evidence filtered to this species and mechanism.</p>
          </div>
          <button className="secondary-button" type="button" onClick={() => onViewResearchEvidence(grass)}>
            <FileSearch aria-hidden="true" size={16} />
            View research evidence
          </button>
        </section>

        <dl className="detail-grid">
          {details.map(([label, value]) => (
            <div className="detail-row" key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>

        {references.length > 0 && (
          <section className="references-section" aria-label="References">
            <h3>References</h3>
            {references.map(([label, value]) => (
              <div key={label}>
                <h4>{label}</h4>
                <p>{cleanDisplayText(value)}</p>
              </div>
            ))}
          </section>
        )}
      </section>
    </div>
  );
}
