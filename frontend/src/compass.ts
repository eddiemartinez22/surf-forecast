const POINTS = [
  "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
];

export function toCompass(deg: number): string {
  const idx = Math.round((deg % 360) / 22.5) % 16;
  return POINTS[idx];
}
