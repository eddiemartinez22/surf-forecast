import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchSpotHistory } from "../api";
import type { HistoryPoint } from "../types";
import { metersToFeet } from "../format";

const REFRESH_MS = 5 * 60 * 1000;

interface Props {
  spotId: string;
}

interface ChartPoint {
  time: string;
  heightFt: number | null;
  periodSec: number | null;
}

export function TrendChart({ spotId }: Props) {
  const [points, setPoints] = useState<ChartPoint[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = () => {
      fetchSpotHistory(spotId, 72)
        .then((history: HistoryPoint[]) => {
          if (cancelled) return;
          setPoints(
            history.map((h) => ({
              time: new Date(h.timestamp.endsWith("Z") ? h.timestamp : `${h.timestamp}Z`).toLocaleString(
                undefined,
                { weekday: "short", hour: "numeric" }
              ),
              heightFt: h.height_m !== null ? Math.round(metersToFeet(h.height_m) * 10) / 10 : null,
              periodSec: h.period_sec,
            }))
          );
          setError(false);
        })
        .catch(() => !cancelled && setError(true));
    };

    load();
    const interval = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [spotId]);

  if (error) return <div className="trend-empty">Trend unavailable</div>;
  if (!points) return <div className="trend-empty">Loading trend…</div>;
  if (points.length < 2) return <div className="trend-empty">Not enough history yet</div>;

  return (
    <ResponsiveContainer width="100%" height={140}>
      <LineChart data={points} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
        <XAxis dataKey="time" tick={{ fontSize: 10, fill: "var(--chart-axis)" }} minTickGap={30} />
        <YAxis yAxisId="height" tick={{ fontSize: 10, fill: "var(--chart-axis)" }} width={30} />
        <YAxis yAxisId="period" orientation="right" tick={{ fontSize: 10, fill: "var(--chart-axis)" }} width={28} />
        <Tooltip
          contentStyle={{ background: "var(--card-bg)", border: "1px solid var(--border)", fontSize: 12 }}
          formatter={(value, name) =>
            name === "heightFt" ? [`${value} ft`, "Height"] : [`${value} s`, "Period"]
          }
        />
        <Line yAxisId="height" type="monotone" dataKey="heightFt" stroke="var(--accent-height)" dot={false} strokeWidth={2} connectNulls />
        <Line yAxisId="period" type="monotone" dataKey="periodSec" stroke="var(--accent-period)" dot={false} strokeWidth={2} connectNulls />
      </LineChart>
    </ResponsiveContainer>
  );
}
