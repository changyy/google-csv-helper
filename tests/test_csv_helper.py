"""Merge/dedup behavior on duplicate dates.

Guards two related regressions:
  * `merge_ordered` without an `on=` key retained rows that differed only in
    float precision — admob's monthly total doubled when `latest-day.csv`
    overlapped `latest-year-day-YYYY.csv`.
  * On the same code path, mixed dtypes across older TSVs and newer CSVs
    (e.g. CTR stored as "5.34%" string vs float) made `merge_ordered` raise,
    after which the fallback `concat` left duplicates untouched.

The fix uses `concat + sort_values` plus a key-only "keep larger value"
loop so that, on overlap, the later/larger reading wins (latest-day reports
are partial snapshots that grow during the day).
"""

import os
import time

import pandas as pd
import pytest

from google_csv_helper.csv_helper import CSVHelper


@pytest.fixture(autouse=True)
def _reset_csvhelper_class_state():
    # CSVHelper declares raw_csv_files_output / pandas_dataframe_output at
    # class level, so without this reset they accumulate across tests.
    CSVHelper.raw_csv_files_output = {}
    CSVHelper.pandas_dataframe_output = {}
    yield


@pytest.fixture
def helper():
    return CSVHelper([], [])


def _frame(rows, columns=("Date", "Estimated earnings (USD)", "Impression RPM (USD)")):
    return pd.DataFrame(rows, columns=list(columns))


def test_identical_rows_merge_to_one(helper):
    df_a = _frame([("2026-05-01", 100.0, 2.5), ("2026-05-02", 110.0, 2.6)])
    df_b = _frame([("2026-05-01", 100.0, 2.5), ("2026-05-02", 110.0, 2.6)])

    out = helper.handleDataFrameMerge(df_a, df_b, "Date", "Estimated earnings (USD)")

    assert list(out["Date"]) == ["2026-05-01", "2026-05-02"]
    assert out["Estimated earnings (USD)"].sum() == pytest.approx(210.0)


def test_float_precision_diff_dedups_by_date(helper):
    # The exact pair seen in production: same earnings, IMPRESSION_RPM
    # differs only in trailing decimals from two API exports.
    df_a = _frame([("2026-05-01", 138.498969, 2.667853939701946)])
    df_b = _frame([("2026-05-01", 138.498969, 2.6678539397019434)])

    out = helper.handleDataFrameMerge(df_a, df_b, "Date", "Estimated earnings (USD)")

    assert len(out) == 1
    assert out["Estimated earnings (USD)"].iloc[0] == pytest.approx(138.498969)


def test_partial_day_keeps_larger_value(helper):
    df_partial = _frame([("2026-05-29", 50.0, 2.4)])
    df_complete = _frame([("2026-05-29", 80.0, 2.7)])

    out = helper.handleDataFrameMerge(df_partial, df_complete, "Date", "Estimated earnings (USD)")

    assert len(out) == 1
    assert out["Estimated earnings (USD)"].iloc[0] == pytest.approx(80.0)


def test_dtype_mismatch_does_not_crash(helper):
    df_old = pd.DataFrame(
        [("2026-05-01", 100.0, "5.34%"), ("2026-05-02", 110.0, "5.40%")],
        columns=["Date", "Estimated earnings (USD)", "CTR"],
    )
    df_new = pd.DataFrame(
        [("2026-05-01", 100.0, 0.0534), ("2026-05-02", 110.0, 0.0540)],
        columns=["Date", "Estimated earnings (USD)", "CTR"],
    )

    out = helper.handleDataFrameMerge(df_old, df_new, "Date", "Estimated earnings (USD)")

    assert list(out["Date"]) == ["2026-05-01", "2026-05-02"]
    assert out["Estimated earnings (USD)"].sum() == pytest.approx(210.0)


def test_non_overlapping_ranges_preserve_all(helper):
    df_jan = _frame([("2026-01-30", 100.0, 2.5), ("2026-01-31", 105.0, 2.6)])
    df_feb = _frame([("2026-02-01", 110.0, 2.7), ("2026-02-02", 115.0, 2.8)])

    out = helper.handleDataFrameMerge(df_jan, df_feb, "Date", "Estimated earnings (USD)")

    assert list(out["Date"]) == [
        "2026-01-30", "2026-01-31", "2026-02-01", "2026-02-02",
    ]
    assert out["Estimated earnings (USD)"].sum() == pytest.approx(430.0)


ADMOB_HEADER = (
    "DATE,ESTIMATED_EARNINGS,CLICKS,AD_REQUESTS,IMPRESSIONS,"
    "IMPRESSION_CTR,IMPRESSION_RPM,SHOW_RATE"
)


def test_end_to_end_overlap_yields_unique_dates(tmp_path):
    csv_dir = tmp_path / "csv" / "admob" / "hk"
    csv_dir.mkdir(parents=True)

    day_csv = csv_dir / "latest-day.csv"
    year_csv = csv_dir / "latest-year-day-2026.csv"

    day_csv.write_text(
        ADMOB_HEADER + "\n"
        "2026-05-03,150.0,4000,100000,50000,0.08,3.0,0.6\n"
        "2026-05-02,120.0,3500,90000,45000,0.077,2.6678539397019434,0.59\n"
        "2026-05-01,100.0,3000,80000,40000,0.075,2.5,0.58\n"
    )
    # Year file overlaps 05-01/05-02; on 05-02 the RPM precision differs
    # and earnings are higher (later, more-complete reading).
    year_csv.write_text(
        ADMOB_HEADER + "\n"
        "2026-05-02,130.0,3500,90000,45000,0.077,2.667853939701946,0.59\n"
        "2026-05-01,100.0,3000,80000,40000,0.075,2.5,0.58\n"
        "2026-04-30,90.0,2800,75000,38000,0.073,2.4,0.57\n"
    )

    # Day file processed first (older mtime) — mirrors production order.
    now = time.time()
    os.utime(day_csv, (now - 60, now - 60))
    os.utime(year_csv, (now, now))

    h = CSVHelper(str(csv_dir), filename_pattern=[])
    h.readAllCSVRawFile()
    result = h.getResultViaPandasDataFrame(str(csv_dir))

    assert result is not None
    df = result["Date"]
    assert df["Date"].is_unique
    assert sorted(df["Date"].tolist()) == [
        "2026-04-30", "2026-05-01", "2026-05-02", "2026-05-03",
    ]
    # 90 (04-30) + 100 (05-01) + 130 (05-02 larger wins) + 150 (05-03) = 470
    assert df["Estimated earnings (USD)"].sum() == pytest.approx(470.0)
