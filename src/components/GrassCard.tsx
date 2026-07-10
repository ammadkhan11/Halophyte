import { Info } from 'lucide-react';
import type { GrassLibraryRecord } from '../data/grassLibraryData';
import {
  cleanDisplayText,
  formatIonCategory,
  formatIonNumeric,
  formatNumber,
  formatRange,
} from '../utils/grassFormatters';

type GrassCardProps = {
  grass: GrassLibraryRecord;
  onSelect: (grass: GrassLibraryRecord) => void;
};

export default function GrassCard({ grass, onSelect }: GrassCardProps) {
  return (
    <article className="grass-card">
      <div className="grass-card-heading">
        <div>
          <p className="source-number">Record {grass.source_no}</p>
          <h3>{cleanDisplayText(grass.common_name)}</h3>
          <p className="scientific-name">{cleanDisplayText(grass.scientific_name)}</p>
        </div>
        <span className={`status-pill ${grass.is_salt_secreting ? 'status-pill-secreting' : 'status-pill-nonsecreting'}`}>
          {grass.mechanism}
        </span>
      </div>

      <div className="grass-card-sections">
        <section>
          <h4>Species Information</h4>
          <dl className="grass-card-metrics">
            <div>
              <dt>Species</dt>
              <dd>{cleanDisplayText(grass.scientific_name)}</dd>
            </div>
            <div>
              <dt>Common Name</dt>
              <dd>{cleanDisplayText(grass.common_name)}</dd>
            </div>
            <div>
              <dt>Mechanism</dt>
              <dd>{grass.mechanism}</dd>
            </div>
            <div>
              <dt>Salt Tolerance</dt>
              <dd>{grass.salt_tolerance_level}</dd>
            </div>
          </dl>
        </section>

        <section>
          <h4>GR50</h4>
          <dl className="grass-card-metrics">
            <div>
              <dt>Average</dt>
              <dd>{formatNumber(grass.gr50_avg_ds_m)} dS/m</dd>
            </div>
            <div>
              <dt>Range</dt>
              <dd>{formatRange(grass.gr50_min_ds_m, grass.gr50_max_ds_m)}</dd>
            </div>
          </dl>
        </section>

        <section>
          <h4>Na+</h4>
          <dl className="grass-card-metrics">
            <div>
              <dt>Shoot numeric</dt>
              <dd>{formatIonNumeric(grass.na_shoot_mmol_kg_dw)}</dd>
            </div>
            <div>
              <dt>Root numeric</dt>
              <dd>{formatIonNumeric(grass.na_root_mmol_kg_dw)}</dd>
            </div>
            <div>
              <dt>Category</dt>
              <dd>{formatIonCategory(grass.na_shoot_level, grass.na_root_level)}</dd>
            </div>
          </dl>
        </section>

        <section>
          <h4>Cl-</h4>
          <dl className="grass-card-metrics">
            <div>
              <dt>Shoot numeric</dt>
              <dd>{formatIonNumeric(grass.cl_shoot_mmol_kg_dw)}</dd>
            </div>
            <div>
              <dt>Root numeric</dt>
              <dd>{formatIonNumeric(grass.cl_root_mmol_kg_dw)}</dd>
            </div>
            <div>
              <dt>Category</dt>
              <dd>{formatIonCategory(grass.cl_shoot_level, grass.cl_root_level)}</dd>
            </div>
          </dl>
        </section>

        <section>
          <h4>K+</h4>
          <dl className="grass-card-metrics">
            <div>
              <dt>Shoot numeric</dt>
              <dd>{formatIonNumeric(grass.k_shoot_mmol_kg_dw)}</dd>
            </div>
            <div>
              <dt>Root numeric</dt>
              <dd>{formatIonNumeric(grass.k_root_mmol_kg_dw)}</dd>
            </div>
            <div>
              <dt>Category</dt>
              <dd>{formatIonCategory(grass.k_shoot_level, grass.k_root_level)}</dd>
            </div>
          </dl>
        </section>
      </div>

      <button className="details-button" type="button" onClick={() => onSelect(grass)}>
        <Info aria-hidden="true" size={16} />
        View details
      </button>
    </article>
  );
}
