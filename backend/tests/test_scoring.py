import pytest

from app.scoring import ScoreInput, SpotConfig, score_reading

CONFIG = SpotConfig(
    id="test-spot",
    name="Test Spot",
    buoy_id="00000",
    optimal_direction_deg=(60, 120),
    min_period_sec=6,
    optimal_period_sec=(8, 14),
    size_thresholds_m={"small": 0.3, "good": 0.6, "firing": 1.2},
)


def test_missing_data_is_unknown():
    result = score_reading(ScoreInput(height_m=None, period_sec=None, direction_deg=None), CONFIG)
    assert result.rating == "Unknown"


def test_flat_seas():
    result = score_reading(ScoreInput(height_m=0.1, period_sec=10, direction_deg=90), CONFIG)
    assert result.rating == "Flat"


def test_good_size_optimal_period_and_direction_is_good():
    result = score_reading(ScoreInput(height_m=0.8, period_sec=12, direction_deg=90), CONFIG)
    assert result.rating == "Good"
    assert result.direction_match is True
    assert result.period_tier == "optimal"


def test_firing_size_with_optimal_period_and_direction():
    result = score_reading(ScoreInput(height_m=1.5, period_sec=13, direction_deg=100), CONFIG)
    assert result.rating == "Firing"


def test_short_period_windswell_downgrades_from_size_alone():
    # 1.5m would be "Firing" by size, but 4s period is wind chop -> downgraded
    result = score_reading(ScoreInput(height_m=1.5, period_sec=4, direction_deg=90), CONFIG)
    assert result.rating == "Good"
    assert result.period_tier == "poor"
    assert "wind chop" in result.reason


def test_wrong_direction_downgrades_even_with_good_period():
    # Good size + optimal period, but direction way outside window
    result = score_reading(ScoreInput(height_m=0.8, period_sec=12, direction_deg=250), CONFIG)
    assert result.rating == "Small"
    assert result.direction_match is False


def test_bad_period_and_bad_direction_downgrades_twice_but_floors_at_flat():
    result = score_reading(ScoreInput(height_m=0.4, period_sec=4, direction_deg=250), CONFIG)
    assert result.rating == "Flat"


def test_direction_window_handles_wraparound():
    wrap_config = SpotConfig(
        id="wrap-spot",
        name="Wrap Spot",
        buoy_id="00000",
        optimal_direction_deg=(350, 40),
        min_period_sec=6,
        optimal_period_sec=(8, 14),
        size_thresholds_m={"small": 0.3, "good": 0.6, "firing": 1.2},
    )
    in_window = score_reading(ScoreInput(height_m=0.8, period_sec=12, direction_deg=10), wrap_config)
    assert in_window.direction_match is True
    out_of_window = score_reading(ScoreInput(height_m=0.8, period_sec=12, direction_deg=180), wrap_config)
    assert out_of_window.direction_match is False


def test_direction_none_treated_as_best_case_but_noted():
    result = score_reading(ScoreInput(height_m=0.8, period_sec=12, direction_deg=None), CONFIG)
    assert result.direction_match is None
    assert result.rating == "Good"
    assert "unavailable" in result.reason
