import pytest
from fastapi import HTTPException

from app import seed
from app.db import connect
from app.modules.order_batch import run_batch_estimate
from app.repositories import history
from app.services import estimate_service


@pytest.fixture()
def fresh_db(tmp_path, monkeypatch):
    monkeypatch.setattr("app.db.DB_PATH", tmp_path / "test.db")
    seed.init_db()
    return tmp_path / "test.db"


def _run_count():
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    finally:
        conn.close()


def test_batch_totals_equal_sum_of_singles(fresh_db):
    out = run_batch_estimate([1, 2], 1, False, "")
    assert [i["wall_id"] for i in out["items"]] == [1, 2]
    assert out["items"][0]["rolls"] == 11  # 主卧一圈：31 条 / 3 条每卷
    assert out["items"][1]["rolls"] == 13  # 大花匹配：38 条 / 3 条每卷
    assert out["rolls"] == 24
    assert out["drops"] == out["items"][0]["drops"] + out["items"][1]["drops"]
    assert out["run_id"] is None


def test_single_wall_batch_equals_single_estimate(fresh_db):
    batch = run_batch_estimate([2], 2, False, "")
    single = estimate_service.run_estimate(2, 2, False, "")
    assert len(batch["items"]) == 1
    assert batch["rolls"] == single["rolls"]
    assert batch["items"][0]["drops"] == single["drops"]
    assert batch["items"][0]["drop_len_m"] == single["drop_len_m"]


def test_empty_wall_list_fails_and_adds_no_row(fresh_db):
    before = _run_count()
    with pytest.raises(HTTPException) as exc:
        run_batch_estimate([], 1, True, "")
    assert exc.value.status_code == 422
    assert _run_count() == before


def test_dirty_wall_fails_and_adds_no_row(fresh_db):
    before = _run_count()
    with pytest.raises(HTTPException) as exc:
        run_batch_estimate([1, 3], 1, True, "")  # wall 3 为 dirty 种子
    assert exc.value.status_code == 422
    assert _run_count() == before


def test_dirty_roll_fails_and_adds_no_row(fresh_db):
    before = _run_count()
    with pytest.raises(HTTPException) as exc:
        run_batch_estimate([1, 2], 3, True, "")  # roll 3 为 dirty 种子
    assert exc.value.status_code == 422
    assert _run_count() == before


def test_unknown_wall_fails_and_adds_no_row(fresh_db):
    before = _run_count()
    with pytest.raises(HTTPException) as exc:
        run_batch_estimate([1, 999], 1, True, "")
    assert exc.value.status_code == 404
    assert _run_count() == before


def test_trial_does_not_persist(fresh_db):
    before = _run_count()
    out = run_batch_estimate([1, 2], 1, False, "")
    assert out["run_id"] is None
    assert _run_count() == before


def test_save_inserts_exactly_one_run_with_breakdown(fresh_db):
    before = _run_count()
    out = run_batch_estimate([1, 2], 1, True, "合并订卷")
    assert out["run_id"] is not None
    assert _run_count() == before + 1

    runs = history.list_runs()
    run = next(r for r in runs if r["id"] == out["run_id"])
    assert run["note"] == "合并订卷"
    result = run["result"]
    assert result["kind"] == "order_batch"
    assert result["rolls"] == 24
    assert [i["wall_id"] for i in result["items"]] == [1, 2]
    assert result["items"][0]["rolls"] == 11
    assert result["items"][1]["rolls"] == 13


def test_saved_breakdown_not_recomputed_after_wall_change(fresh_db):
    out = run_batch_estimate([1, 2], 1, True, "")
    saved = next(r for r in history.list_runs() if r["id"] == out["run_id"])
    snapshot = [dict(i) for i in saved["result"]["items"]]

    conn = connect()
    try:
        conn.execute("UPDATE walls SET perimeter=99.0 WHERE id=1")
        conn.commit()
    finally:
        conn.close()

    reread = next(r for r in history.list_runs() if r["id"] == out["run_id"])
    assert reread["result"]["items"] == snapshot
    assert reread["result"]["rolls"] == 24


def test_api_batch_endpoint(fresh_db):
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        ok = client.post(
            "/api/estimate/batch",
            json={"wall_ids": [1, 2], "roll_id": 1, "save": True, "note": "n"},
        )
        assert ok.status_code == 200
        body = ok.json()
        assert body["rolls"] == 24
        assert len(body["items"]) == 2
        assert body["run_id"] is not None

        empty = client.post("/api/estimate/batch", json={"wall_ids": [], "roll_id": 1, "save": True})
        assert empty.status_code == 422

        dirty = client.post("/api/estimate/batch", json={"wall_ids": [1, 3], "roll_id": 1, "save": True})
        assert dirty.status_code == 422

        runs = client.get("/api/runs").json()["items"]
        batch_runs = [r for r in runs if r["result"].get("kind") == "order_batch"]
        assert len(batch_runs) == 1  # 只有成功的那一次落库，失败不增行
