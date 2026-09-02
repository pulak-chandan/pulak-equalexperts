"""Behavioural tests for the outlier-week calculation.

Uses the sample dataset from the README as the correctness oracle.
"""

from pathlib import Path

import duckdb
import pytest

from equalexperts_dataeng_exercise import db
from equalexperts_dataeng_exercise.ingest import ingest
from equalexperts_dataeng_exercise.outliers import OUTLIER_VIEW, create_view

SAMPLE_FILE = str(Path(__file__).parent / "test-resources" / "samples-votes.jsonl")

# Expected output from the README example.
EXPECTED_OUTLIERS = [
    (2022, 0, 1),
    (2022, 1, 3),
    (2022, 2, 3),
    (2022, 5, 1),
    (2022, 6, 1),
    (2022, 8, 1),
]


@pytest.fixture
def con(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    connection = db.connect(str(tmp_path / "test.db"))
    yield connection
    connection.close()


def test_outlier_weeks_matches_sample(con: duckdb.DuckDBPyConnection) -> None:
    ingest(SAMPLE_FILE, con)
    create_view(con)
    result = con.execute(f"SELECT Year, WeekNumber, VoteCount FROM {OUTLIER_VIEW}").fetchall()
    assert result == EXPECTED_OUTLIERS


def test_outlier_view_is_a_view(con: duckdb.DuckDBPyConnection) -> None:
    ingest(SAMPLE_FILE, con)
    create_view(con)
    kind = con.execute(
        "SELECT table_type FROM information_schema.tables "
        "WHERE table_schema = 'blog_analysis' AND table_name = 'outlier_weeks'"
    ).fetchall()
    assert kind == [("VIEW",)]


def test_outlier_view_is_ordered(con: duckdb.DuckDBPyConnection) -> None:
    ingest(SAMPLE_FILE, con)
    create_view(con)
    result = con.execute(f"SELECT Year, WeekNumber FROM {OUTLIER_VIEW}").fetchall()
    assert result == sorted(result)
