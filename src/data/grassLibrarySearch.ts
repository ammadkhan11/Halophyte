import {
  grassLibraryData,
  GrassLibraryRecord,
  Mechanism,
  SaltToleranceLevel,
} from './grassLibraryData';

export type IonLevelFilter = 'Low' | 'Moderate' | 'High' | 'All';

export type GrassSortOption =
  | 'species-asc'
  | 'species-desc'
  | 'gr50-desc'
  | 'gr50-asc'
  | 'salt-secreting-first'
  | 'non-secreting-first'
  | 'na-shoot-desc'
  | 'na-root-desc'
  | 'cl-shoot-desc'
  | 'cl-root-desc'
  | 'k-shoot-desc'
  | 'k-root-desc';

export type GrassSearchFilters = {
  query?: string;
  mechanism?: Mechanism | 'All';
  toleranceLevel?: SaltToleranceLevel | 'All';
  gr50Min?: number;
  gr50Max?: number;
  naLevel?: IonLevelFilter;
  clLevel?: IonLevelFilter;
  kLevel?: IonLevelFilter;
};

export const defaultGrassSearchFilters: GrassSearchFilters = {
  query: '',
  mechanism: 'All',
  toleranceLevel: 'All',
  gr50Min: undefined,
  gr50Max: undefined,
  naLevel: 'All',
  clLevel: 'All',
  kLevel: 'All',
};

export const defaultGrassSortOption: GrassSortOption = 'species-asc';

export function searchGrassLibrary(filters: GrassSearchFilters): GrassLibraryRecord[] {
  const queryTokens = normalise(filters.query)
    .split(/\s+/)
    .filter(Boolean);

  return grassLibraryData.filter((grass) => {
    const searchBlob = buildSpeciesSearchBlob(grass);
    const matchesQuery = queryTokens.length === 0 || queryTokens.every((token) => searchBlob.includes(token));
    const matchesMechanism = !filters.mechanism || filters.mechanism === 'All' || grass.mechanism === filters.mechanism;
    const matchesTolerance = !filters.toleranceLevel || filters.toleranceLevel === 'All' || grass.salt_tolerance_level === filters.toleranceLevel;
    const matchesGr50Min = filters.gr50Min == null || grass.gr50_avg_ds_m >= filters.gr50Min;
    const matchesGr50Max = filters.gr50Max == null || grass.gr50_avg_ds_m <= filters.gr50Max;
    const matchesNa = matchesIonLevel(grass.na_shoot_level, grass.na_root_level, filters.naLevel);
    const matchesCl = matchesIonLevel(grass.cl_shoot_level, grass.cl_root_level, filters.clLevel);
    const matchesK = matchesIonLevel(grass.k_shoot_level, grass.k_root_level, filters.kLevel);

    return matchesQuery && matchesMechanism && matchesTolerance && matchesGr50Min && matchesGr50Max && matchesNa && matchesCl && matchesK;
  });
}

export function getGrassById(id: string): GrassLibraryRecord | undefined {
  return grassLibraryData.find((grass) => grass.id === id);
}

export function sortGrassLibrary(records: GrassLibraryRecord[], sortOption: GrassSortOption): GrassLibraryRecord[] {
  return [...records].sort((left, right) => {
    switch (sortOption) {
      case 'species-desc':
        return compareSpecies(right, left);
      case 'gr50-desc':
        return compareNumber(right.gr50_avg_ds_m, left.gr50_avg_ds_m) || compareSpecies(left, right);
      case 'gr50-asc':
        return compareNumber(left.gr50_avg_ds_m, right.gr50_avg_ds_m) || compareSpecies(left, right);
      case 'salt-secreting-first':
        return compareNumber(Number(right.is_salt_secreting), Number(left.is_salt_secreting)) || compareSpecies(left, right);
      case 'non-secreting-first':
        return compareNumber(Number(left.is_salt_secreting), Number(right.is_salt_secreting)) || compareSpecies(left, right);
      case 'na-shoot-desc':
        return compareNumber(right.na_shoot_mmol_kg_dw, left.na_shoot_mmol_kg_dw) || compareSpecies(left, right);
      case 'na-root-desc':
        return compareNumber(right.na_root_mmol_kg_dw, left.na_root_mmol_kg_dw) || compareSpecies(left, right);
      case 'cl-shoot-desc':
        return compareNumber(right.cl_shoot_mmol_kg_dw, left.cl_shoot_mmol_kg_dw) || compareSpecies(left, right);
      case 'cl-root-desc':
        return compareNumber(right.cl_root_mmol_kg_dw, left.cl_root_mmol_kg_dw) || compareSpecies(left, right);
      case 'k-shoot-desc':
        return compareNumber(right.k_shoot_mmol_kg_dw, left.k_shoot_mmol_kg_dw) || compareSpecies(left, right);
      case 'k-root-desc':
        return compareNumber(right.k_root_mmol_kg_dw, left.k_root_mmol_kg_dw) || compareSpecies(left, right);
      case 'species-asc':
      default:
        return compareSpecies(left, right);
    }
  });
}

function buildSpeciesSearchBlob(grass: GrassLibraryRecord): string {
  const searchableValues = [
    grass.species_full_name,
    grass.scientific_name,
    grass.common_name,
    grass.common_name_aliases.join(' '),
  ];

  return searchableValues.map(normalise).join(' ');
}

function matchesIonLevel(shootLevel: string, rootLevel: string, selectedLevel?: IonLevelFilter): boolean {
  if (!selectedLevel || selectedLevel === 'All') {
    return true;
  }

  const selected = selectedLevel.toLowerCase();
  return shootLevel.toLowerCase().includes(selected) || rootLevel.toLowerCase().includes(selected);
}

function normalise(value: unknown): string {
  return String(value ?? '').toLowerCase();
}

function compareSpecies(left: GrassLibraryRecord, right: GrassLibraryRecord): number {
  return left.scientific_name.localeCompare(right.scientific_name, undefined, { sensitivity: 'base' });
}

function compareNumber(left: number, right: number): number {
  return left - right;
}
