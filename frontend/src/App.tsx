import { useEffect, useState } from "react";
import { fetchSpots } from "./api";
import type { SpotStatus } from "./types";
import { SpotCard } from "./components/SpotCard";
import "./App.css";

const REFRESH_MS = 5 * 60 * 1000;

function App() {
  const [spots, setSpots] = useState<SpotStatus[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = () => {
      fetchSpots()
        .then((data) => {
          if (!cancelled) {
            setSpots(data);
            setError(null);
          }
        })
        .catch(() => {
          if (!cancelled) setError("Can't reach the surf-forecast backend. Is it running?");
        });
    };

    load();
    const interval = setInterval(load, REFRESH_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="app">
      <header className="app__header">
        <h1>Surf Forecast</h1>
        <p className="app__subtitle">Live NDBC buoy readings, translated into surf conditions</p>
      </header>

      {error && <div className="error-banner">{error}</div>}
      {!error && spots === null && <div className="loading">Loading spots…</div>}

      <main className="spot-grid">
        {spots?.map((spot) => (
          <SpotCard key={spot.id} spot={spot} />
        ))}
      </main>
    </div>
  );
}

export default App;
