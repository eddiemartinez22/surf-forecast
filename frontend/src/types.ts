export type Rating = "Flat" | "Small" | "Good" | "Firing" | "Unknown";

export interface SpotStatus {
  id: string;
  name: string;
  buoy_id: string;
  rating: Rating;
  reason: string;
  height_m: number | null;
  period_sec: number | null;
  direction_deg: number | null;
  wind_speed_ms: number | null;
  wind_dir_deg: number | null;
  water_temp_c: number | null;
  reading_timestamp: string | null;
  stale: boolean;
  has_data: boolean;
}

export interface HistoryPoint {
  timestamp: string;
  height_m: number | null;
  period_sec: number | null;
  direction_deg: number | null;
}
