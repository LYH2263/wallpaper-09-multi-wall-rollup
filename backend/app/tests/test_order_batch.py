"""Tests for the multi-wall order batch: aggregation, validation, persistence."""

import json

import pytest
from fastapi import HTTPException

from app.db import connect
from app.engines.wallpaper_math import roll_count
from app.modules.order_batch import aggregate
from app.repositories import history
from app.services import order_batch_service
from app.services.estimate_service import run_estimate


def run_count() -> int:
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    finally:
        conn.close()

ROLL_PLAIN = {"id": 1, "name": "素色53", "width": 0.53, "length": 10.0, "pattern_cm": 0}
WALL_1 = {"id": 1, "name": "主卧一圈", "perimeter": 16.0, "height": 2.7}
WALL_2 = {"id": 2, "name": "大花匹配", "perimeter": 20.0, "height": 2.8}


# ---------- pure aggregation module ----------

def test_aggregate_single_matches_engine():
    batch = aggregate([WALL_1], ROLL_PLAIN)
    solo = roll_count(16.0, 2.7, 0.53, 10.0, 0)
    assert batch["items"][0]["drops"] == solo["drops"]
    assert batch["items"][0]["rolls"] == solo["rolls"]
    assert batch["totals"] == {"wall_count": 1, "drops": solo["drops"], "rolls": solo["rolls"]}


def test_aggregate_multi_totals_are_sum_of_per_wall_rolls():
    batch = aggregate([WALL_1, WALL_2], ROLL_PLAIN)
    assert [i["wall_id"] for i in batch["items"]] == [1, 2]
    assert batch["items"][0]["rolls"] == 11
    assert batch["items"][1]["rolls"] == 13
    assert batch["totals"]["rolls"] == 24
    assert batch["totals"]["drops"] == 31 + 38


# ---------- service: single-wall parity ----------

def test_single_wall_batch_equals_solo_estimate(fresh_db):
    batch = order_batch_service.run_batch([1], 1, save=False, note="")
    solo = run_estimate(1, 1, save=False, note="")
    assert batch["totals"]["rolls"] == solo["rolls"]
    assert batch["totals"]["drops"] == solo["drops"]
    assert batch["items"][0]["rolls"] == solo["rolls"]
    assert batch["run_id"] is None
    assert run_count() == 0


# ---------- service: validation never writes ----------

def test_empty_wall_list_rejected_without_row(fresh_db):
    with pytest.raises(HTTPException) as ei:
        order_batch_service.run_batch([], 1, save=True, note="")
    assert ei.value.status_code == 422
    assert run_count() == 0


def test_dirty_wall_rejected_without_row(fresh_db):
    with pytest.raises(HTTPException) as ei:
        order_batch_service.run_batch([1, 3], 1, save=True, note="")
    assert ei.value.status_code == 422
    assert run_count() == 0


def test_dirty_roll_rejected_without_row(fresh_db):
    with pytest.raises(HTTPException) as ei:
        order_batch_service.run_batch([1, 2], 3, save=True, note="")
    assert ei.value.status_code == 422
    assert run_count() == 0


def test_missing_wall_or_roll_rejected_without_row(fresh_db):
    with pytest.raises(HTTPException) as ei:
        order_batch_service.run_batch([999], 1, save=True, note="")
    assert ei.value.status_code == 404
    with pytest.raises(HTTPException) as ei:
        order_batch_service.run_batch([1], 999, save=True, note="")
    assert ei.value.status_code == 404
    assert run_count() == 0


def test_duplicate_wall_ids_counted_once(fresh_db):
    batch = order_batch_service.run_batch([1, 1], 1, save=False, note="")
    assert batch["totals"]["wall_count"] == 1
    assert run_count() == 0


# ---------- persistence: exactly one run, snapshot immutable ----------

def test_save_inserts_one_batch_run(fresh_db):
    out = order_batch_service.run_batch([1, 2], 1, save=True, note="合并下单")
    assert out["run_id"] is not None
    assert run_count() == 1

    rows = history.list_runs()
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == out["run_id"]
    assert row["wall_id"] is None  # one run for the whole batch
    result = row["result"]
    assert result["kind"] == "order_batch"
    assert len(result["items"]) == 2
    assert result["totals"]["rolls"] == 24
    assert result["items"][0]["perimeter"] == 16.0


def test_saved_batch_not_recomputed_after_perimeter_change(fresh_db):
    out = order_batch_service.run_batch([1, 2], 1, save=True, note="合并下单")
    saved_id = out["run_id"]

    # Edit wall 1's perimeter afterwards.
    conn = connect()
    conn.execute("UPDATE walls SET perimeter=? WHERE id=1", (10.0,))
    conn.commit()
    conn.close()

    saved = history.list_runs()[0]
    assert saved["id"] == saved_id
    first = saved["result"]["items"][0]
    assert first["perimeter"] == 16.0  # snapshot kept
    assert first["rolls"] == 11
    assert saved["result"]["totals"]["rolls"] == 24

    # A fresh estimate reflects the edit, proving the stored row wasn't recomputed.
    fresh = order_batch_service.run_batch([1, 2], 1, save=False, note="")
    assert fresh["items"][0]["perimeter"] == 10.0
    assert fresh["totals"]["rolls"] != 24
    assert run_count() == 1  # no extra rows from reads
