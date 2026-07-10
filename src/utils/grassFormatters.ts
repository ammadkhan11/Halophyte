export function formatNumber(value: number): string {
  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}

export function formatRange(min: number, max: number, unit = 'dS/m'): string {
  return `${formatNumber(min)}-${formatNumber(max)} ${unit}`;
}

export function formatIonValue(value: number, level: string): string {
  return `${formatIonNumeric(value)} (${cleanDisplayText(level)})`;
}

export function formatIonNumeric(value: number): string {
  return `${formatNumber(value)} mmol/kg DW`;
}

export function formatIonCategory(shootLevel: string, rootLevel: string): string {
  return `Shoot: ${cleanDisplayText(shootLevel)} / Root: ${cleanDisplayText(rootLevel)}`;
}

export function cleanDisplayText(value: string): string {
  return value
    .replace(/â€“/g, '-')
    .replace(/â€™/g, "'")
    .replace(/âˆ’/g, '-')
    .replace(/Ã¢â‚¬â€œ/g, '-')
    .replace(/Ã¢â‚¬â„¢/g, "'")
    .replace(/Ã¢Ë†â€™/g, '-');
}
