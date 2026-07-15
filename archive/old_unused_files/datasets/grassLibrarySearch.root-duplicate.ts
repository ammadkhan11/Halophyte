import { grassLibraryData, GrassLibraryRecord } from './grassLibraryData';

export type GrassSearchFilters = {
  query?: string;
  mechanism?: 'Salt-Secreting' | 'Non-Secreting' | 'All';
  toleranceLevel?: 'Low' | 'Moderate' | 'High' | 'Very High' | 'All';
  gr50Min?: number;
  gr50Max?: number;
  ionField?: keyof Pick<
    GrassLibraryRecord,
    'na_shoot_level' | 'na_root_level' | 'cl_shoot_level' | 'cl_root_level' | 'k_shoot_level' | 'k_root_level'
  >;
  ionLevel?: 'Low' | 'Moderate' | 'High' | 'All';
};

export function searchGrassLibrary(filters: GrassSearchFilters): GrassLibraryRecord[] {
  const query = (filters.query || '').trim().toLowerCase();

  return grassLibraryData.filter((grass) => {
    const matchesQuery = !query || grass.search_text.includes(query);
    const matchesMechanism = !filters.mechanism || filters.mechanism === 'All' || grass.mechanism === filters.mechanism;
    const matchesTolerance = !filters.toleranceLevel || filters.toleranceLevel === 'All' || grass.salt_tolerance_level === filters.toleranceLevel;
    const matchesGr50Min = filters.gr50Min == null || grass.gr50_avg_ds_m >= filters.gr50Min;
    const matchesGr50Max = filters.gr50Max == null || grass.gr50_avg_ds_m <= filters.gr50Max;

    let matchesIon = true;
    if (filters.ionField && filters.ionLevel && filters.ionLevel !== 'All') {
      matchesIon = grass[filters.ionField] === filters.ionLevel;
    }

    return matchesQuery && matchesMechanism && matchesTolerance && matchesGr50Min && matchesGr50Max && matchesIon;
  });
}

export function getGrassById(id: string): GrassLibraryRecord | undefined {
  return grassLibraryData.find((grass) => grass.id === id);
}
