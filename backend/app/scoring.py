"""Turns a raw buoy reading + a spot's configured swell window into a rating.

Design principle from the project brief: period and direction match matter
more than raw height. A long-period, well-aligned 3ft swell often surfs
better than a short-period, misaligned 5ft windswell, so a size band is
only the *starting point* — it gets downgraded when the period is short
(wind chop, not real swell) or the direction is outside the spot's window,
and can only reach the top rating when both line up.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Rating = Literal["Flat", "Small", "Good", "Firing", "Unknown"]

RATING_ORDER: list[Rating] = ["Flat", "Small", "Good", "Firing"]


@dataclass(frozen=True)
class SpotConfig:
    id: str
    name: str
    buoy_id: str
    optimal_direction_deg: tuple[float, float]
    min_period_sec: float
    optimal_period_sec: tuple[float, float]
    size_thresholds_m: dict[str, float]

    @staticmethod
    def from_dict(d: dict) -> "SpotConfig":
        return SpotConfig(
            id=d["id"],
            name=d["name"],
            buoy_id=d["buoy_id"],
            optimal_direction_deg=tuple(d["optimal_direction_deg"]),
            min_period_sec=d["min_period_sec"],
            optimal_period_sec=tuple(d["optimal_period_sec"]),
            size_thresholds_m=d["size_thresholds_m"],
        )


@dataclass(frozen=True)
class ScoreInput:
    """The subset of a BuoyReading the scoring engine needs, decoupled from
    the ORM model so scoring logic is trivially unit-testable."""

    height_m: float | None
    period_sec: float | None
    direction_deg: float | None


@dataclass(frozen=True)
class ScoreResult:
    rating: Rating
    height_m: float | None
    period_sec: float | None
    direction_deg: float | None
    direction_match: bool | None
    period_tier: Literal["poor", "fair", "optimal"] | None
    reason: str


def _direction_in_range(direction: float, lo: float, hi: float) -> bool:
    """Handles a window that wraps past 360 (e.g. 350-40)."""
    direction = direction % 360
    lo = lo % 360
    hi = hi % 360
    if lo <= hi:
        return lo <= direction <= hi
    return direction >= lo or direction <= hi


def _period_tier(period: float, config: SpotConfig) -> Literal["poor", "fair", "optimal"]:
    lo, hi = config.optimal_period_sec
    if period < config.min_period_sec:
        return "poor"
    if period < lo:
        return "fair"
    return "optimal"  # anything >= lo counts as optimal; long-period swell is never penalized


def _size_tier(height: float, thresholds: dict[str, float]) -> Rating:
    if height >= thresholds["firing"]:
        return "Firing"
    if height >= thresholds["good"]:
        return "Good"
    if height >= thresholds["small"]:
        return "Small"
    return "Flat"


def _downgrade(rating: Rating) -> Rating:
    idx = RATING_ORDER.index(rating)
    return RATING_ORDER[max(idx - 1, 0)]


def score_reading(reading: ScoreInput, config: SpotConfig) -> ScoreResult:
    if reading.height_m is None or reading.period_sec is None:
        return ScoreResult(
            rating="Unknown",
            height_m=reading.height_m,
            period_sec=reading.period_sec,
            direction_deg=reading.direction_deg,
            direction_match=None,
            period_tier=None,
            reason="Missing height or period data from buoy",
        )

    size_tier = _size_tier(reading.height_m, config.size_thresholds_m)
    period_tier = _period_tier(reading.period_sec, config)
    direction_match = (
        _direction_in_range(reading.direction_deg, *config.optimal_direction_deg)
        if reading.direction_deg is not None
        else None
    )

    rating = size_tier
    reasons = []

    if period_tier == "poor":
        rating = _downgrade(rating)
        reasons.append(f"period {reading.period_sec:.0f}s is short-period wind chop, not real swell")
    elif period_tier == "fair":
        reasons.append(f"period {reading.period_sec:.0f}s is below this spot's optimal window")

    if direction_match is False:
        rating = _downgrade(rating)
        reasons.append(f"direction {reading.direction_deg:.0f}° is outside this spot's swell window")
    elif direction_match is None:
        reasons.append("direction unavailable, assuming best case")

    if period_tier == "optimal" and direction_match is not False and size_tier in ("Good", "Firing"):
        reasons.append("period and direction well-aligned")

    reason = "; ".join(reasons) if reasons else "on the money"
    return ScoreResult(
        rating=rating,
        height_m=reading.height_m,
        period_sec=reading.period_sec,
        direction_deg=reading.direction_deg,
        direction_match=direction_match,
        period_tier=period_tier,
        reason=reason,
    )


def score_from_buoy_reading(reading, config: SpotConfig) -> ScoreResult:
    """Prefer the .spec swell partition (SwH/SwP/SwD) over the raw combined
    sea state (WVHT/DPD/MWD) when available, since it isolates true swell
    from local wind chop rather than blending them."""
    height = reading.swh if reading.swh is not None else reading.wvht
    period = reading.swp if reading.swp is not None else reading.dpd
    direction = reading.swd if reading.swd is not None else reading.mwd
    return score_reading(ScoreInput(height_m=height, period_sec=period, direction_deg=direction), config)
