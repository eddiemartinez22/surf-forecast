import type { SpotStatus } from "../types";
import { toCompass } from "../compass";
import { formatRelativeTime, metersToFeet } from "../format";
import { TrendChart } from "./TrendChart";

const RATING_CLASS: Record<SpotStatus["rating"], string> = {
  Flat: "rating-flat",
  Small: "rating-small",
  Good: "rating-good",
  Firing: "rating-firing",
  Unknown: "rating-unknown",
};

export function SpotCard({ spot }: { spot: SpotStatus }) {
  return (
    <div className={`spot-card ${spot.stale ? "spot-card--stale" : ""}`}>
      <div className="spot-card__header">
        <h2>{spot.name}</h2>
        <span className={`rating-badge ${RATING_CLASS[spot.rating]}`}>{spot.rating}</span>
      </div>

      {spot.stale && (
        <div className="stale-banner">
          {spot.has_data ? "Buoy data is stale — last reading is over 2.5 hours old" : "No data yet"}
        </div>
      )}

      <div className="spot-card__stats">
        <div className="stat">
          <span className="stat__label">Height</span>
          <span className="stat__value">
            {spot.height_m !== null ? `${metersToFeet(spot.height_m).toFixed(1)} ft` : "—"}
          </span>
          {spot.height_m !== null && <span className="stat__sub">{spot.height_m.toFixed(1)} m</span>}
        </div>
        <div className="stat">
          <span className="stat__label">Period</span>
          <span className="stat__value">{spot.period_sec !== null ? `${spot.period_sec.toFixed(0)}s` : "—"}</span>
        </div>
        <div className="stat">
          <span className="stat__label">Direction</span>
          <span className="stat__value">
            {spot.direction_deg !== null ? toCompass(spot.direction_deg) : "—"}
          </span>
          {spot.direction_deg !== null && <span className="stat__sub">{spot.direction_deg.toFixed(0)}°</span>}
        </div>
        <div className="stat">
          <span className="stat__label">Wind</span>
          <span className="stat__value">
            {spot.wind_speed_ms !== null ? `${(spot.wind_speed_ms * 2.237).toFixed(0)} mph` : "—"}
          </span>
          {spot.wind_dir_deg !== null && <span className="stat__sub">{toCompass(spot.wind_dir_deg)}</span>}
        </div>
      </div>

      <p className="spot-card__reason">{spot.reason}</p>

      <TrendChart spotId={spot.id} />

      <div className="spot-card__footer">
        {spot.reading_timestamp ? `Updated ${formatRelativeTime(spot.reading_timestamp)}` : "No readings yet"}
        <span className="buoy-id"> · Buoy {spot.buoy_id}</span>
      </div>
    </div>
  );
}
