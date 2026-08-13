from pathlib import Path

from app.ndbc.parser import parse_met_file, parse_met_txt, parse_spec_path

FIXTURES = Path(__file__).parent / "fixtures"


def test_parses_real_met_sample():
    readings = parse_met_file(FIXTURES / "41112_sample.txt")
    assert len(readings) == 28
    latest = readings[0]
    assert latest.wvht == 0.4
    assert latest.dpd == 3.0
    assert latest.apd == 2.9
    assert latest.mwd == 233
    # WDIR/WSPD/GST/PRES/ATMP/DEWP/VIS/PTDY/TIDE are all "MM" on this row
    assert latest.wdir is None
    assert latest.wspd is None
    assert latest.pres is None
    assert latest.tide is None
    # WTMP does report on this row
    assert latest.wtmp == 27.8


def test_parses_real_offshore_sample_with_partial_mm():
    readings = parse_met_file(FIXTURES / "41009_sample.txt")
    assert len(readings) == 13
    row = next(r for r in readings if r.wvht == 0.4 and r.dpd == 8.0)
    assert row.wdir == 200
    assert row.wspd == 5.0
    assert row.apd == 5.6
    assert row.mwd == 95
    assert row.wtmp is None  # MM on this row
    assert row.ptdy is None  # MM on this row


def test_mm_never_parsed_as_zero():
    text = (
        "#YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS PTDY  TIDE\n"
        "#yr  mo dy hr mn degT m/s  m/s     m   sec   sec degT   hPa  degC  degC  degC  nmi  hPa    ft\n"
        "2026 08 12 23 56  MM   MM   MM    MM    MM    MM  MM     MM    MM    MM    MM   MM   MM    MM\n"
    )
    [reading] = parse_met_txt(text)
    for field in ("wdir", "wspd", "gst", "wvht", "dpd", "apd", "mwd", "pres", "atmp", "wtmp", "dewp", "vis", "ptdy", "tide"):
        value = getattr(reading, field)
        assert value is None, f"{field} should be None, not {value!r}"


def test_skips_garbage_and_all_missing_rows_but_keeps_valid_row():
    readings = parse_met_file(FIXTURES / "malformed_sample.txt")
    assert len(readings) == 2
    valid = [r for r in readings if r.wvht is not None]
    assert len(valid) == 1
    assert valid[0].wvht == 0.9
    assert valid[0].dpd == 10.0
    assert valid[0].wtmp == 28.1


def test_parses_real_spec_sample_with_compass_directions():
    readings = parse_spec_path(FIXTURES / "41112_sample.spec")
    assert len(readings) == 28
    latest = readings[0]
    assert latest.wvht == 0.4
    assert latest.swh == 0.1
    assert latest.swp == 13.3
    assert latest.wwh == 0.4
    assert latest.wwp == 2.6
    assert latest.swd == 112.5  # ESE
    assert latest.wwd == 225.0  # SW
    assert latest.apd == 2.9
    assert latest.mwd == 233
    # STEEPNESS is N/A on this row -> should be None, not the string "N/A"
    assert latest.steepness is None


def test_readings_are_newest_first_and_timestamps_parse():
    readings = parse_met_file(FIXTURES / "41112_sample.txt")
    assert readings[0].timestamp > readings[1].timestamp
    assert readings[0].timestamp.year == 2026
