import type { HistoryPoint, SpotStatus } from "./types";

const API_BASE = "http://localhost:8001/api";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`${path} failed: HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function fetchSpots(): Promise<SpotStatus[]> {
  return getJson<SpotStatus[]>("/spots");
}

export function fetchSpotHistory(spotId: string, hours = 72): Promise<HistoryPoint[]> {
  return getJson<HistoryPoint[]>(`/spots/${spotId}/history?hours=${hours}`);
}
