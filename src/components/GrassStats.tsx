import { BarChart3, Leaf, TrendingUp } from 'lucide-react';
import type { GrassLibraryRecord } from '../data/grassLibraryData';
import { formatNumber } from '../utils/grassFormatters';

type GrassStatsProps = {
  records: GrassLibraryRecord[];
};

export default function GrassStats({ records }: GrassStatsProps) {
  const saltSecretingCount = records.filter((grass) => grass.is_salt_secreting).length;
  const nonSecretingCount = records.length - saltSecretingCount;
  const highestGr50Grass = records.reduce((highest, grass) => (
    grass.gr50_avg_ds_m > highest.gr50_avg_ds_m ? grass : highest
  ), records[0]);

  const stats = [
    {
      label: 'Total grasses',
      value: records.length,
      detail: 'dictionary records',
      icon: Leaf,
    },
    {
      label: 'Salt-Secreting grasses',
      value: saltSecretingCount,
      detail: 'with secretion marker',
      icon: BarChart3,
    },
    {
      label: 'Non-Secreting grasses',
      value: nonSecretingCount,
      detail: 'without secretion marker',
      icon: BarChart3,
    },
    {
      label: 'Highest GR50 grass',
      value: `${formatNumber(highestGr50Grass.gr50_avg_ds_m)} dS/m`,
      detail: highestGr50Grass.common_name,
      icon: TrendingUp,
    },
  ];

  return (
    <section className="stats-grid" aria-label="Grass library statistics">
      {stats.map(({ label, value, detail, icon: Icon }) => (
        <article className="stat-card" key={label}>
          <div className="stat-icon" aria-hidden="true">
            <Icon size={20} />
          </div>
          <p>{label}</p>
          <strong>{value}</strong>
          <span>{detail}</span>
        </article>
      ))}
    </section>
  );
}
