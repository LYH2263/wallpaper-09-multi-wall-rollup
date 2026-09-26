import os
import tempfile

os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="wp_batch_test_"))

import pytest

from app import seed
from app.db import connect


@pytest.fixture()
def fresh_db():
    seed.init_db()
    conn = connect()
    conn.execute("DELETE FROM calc_runs")
    conn.commit()
    conn.close()
    yield


def run_count() -> int:
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) c FROM calc_runs").fetchone()["c"]
    finally:
        conn.close()
