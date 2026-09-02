"""Behavioural tests for the ingestion process.

Each test uses its own temporary database and data file so it is self-contained
and independent of execution order.
"""

import datetime
from pathlib import Path

import duckdb
import pytest

from equalexperts_dataeng_exercise import db
from equalexperts_dataeng_exercise.ingest import ingest

SAMPLE_FILE = str(Path(__file__).parent / "test-resources" / "samples-votes.jsonl")


@pytest.fixture
def con(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    connection = db.connect(str(tmp_path / "test.db"))
    yield connection
    connection.close()


def _rows(con: duckdb.DuckDBPyConnection) -> list[tuple]:
    return con.execute(
        f"SELECT Id, PostId, VoteTypeId, CreationDate FROM {db.VOTES_TABLE} ORDER BY Id"
    ).fetchall()


def test_ingest_creates_schema_and_table(con: duckdb.DuckDBPyConnection) -> None:
    ingest(SAMPLE_FILE, con)
    exists = con.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'blog_analysis' AND table_name = 'votes'"
    ).fetchall()
    assert exists == [(1,)]


def test_ingest_loads_all_sample_rows(con: duckdb.DuckDBPyConnection) -> None:
    total = ingest(SAMPLE_FILE, con)
    assert total == 16


def test_ingest_is_idempotent(con: duckdb.DuckDBPyConnection) -> None:
    first = ingest(SAMPLE_FILE, con)
    second = ingest(SAMPLE_FILE, con)
    assert first == second == 16


def test_ingest_updates_changed_record(tmp_path: Path, con: duckdb.DuckDBPyConnection) -> None:
    original = tmp_path / "v1.jsonl"
    original.write_text('{"Id":"1","PostId":"1","VoteTypeId":"2","CreationDate":"2022-01-02T00:00:00.000"}\n')
    ingest(str(original), con)

    updated = tmp_path / "v2.jsonl"
    updated.write_text('{"Id":"1","PostId":"99","VoteTypeId":"3","CreationDate":"2022-05-01T00:00:00.000"}\n')
    total = ingest(str(updated), con)

    assert total == 1  # updated in place, not inserted as a new row
    assert _rows(con) == [(1, 99, 3, datetime.datetime(2022, 5, 1))]


def test_ingest_deduplicates_within_a_file(tmp_path: Path, con: duckdb.DuckDBPyConnection) -> None:
    data = tmp_path / "dupes.jsonl"
    data.write_text(
        '{"Id":"1","PostId":"1","VoteTypeId":"2","CreationDate":"2022-01-02T00:00:00.000"}\n'
        '{"Id":"1","PostId":"1","VoteTypeId":"2","CreationDate":"2022-06-02T00:00:00.000"}\n'
    )
    total = ingest(str(data), con)

    assert total == 1  # the later CreationDate wins
    assert _rows(con) == [(1, 1, 2, datetime.datetime(2022, 6, 2))]


def test_ingest_missing_file_raises(tmp_path: Path, con: duckdb.DuckDBPyConnection) -> None:
    missing = str(tmp_path / "does-not-exist.jsonl")
    with pytest.raises(FileNotFoundError):
        ingest(missing, con)
