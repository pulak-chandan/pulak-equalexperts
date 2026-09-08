"""Behavioural tests for the ingestion (MERGE/upsert) logic.

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
def con(tmp_path: Path):
    connection = db.connect(str(tmp_path / "test.db"))
    db.ensure_schema(connection)
    yield connection
    connection.close()


def _count(con: duckdb.DuckDBPyConnection):
    return con.execute(
        f"""
        SELECT COUNT(*) FROM {db.VOTES_TABLE}
        """
    ).fetchone()[0]


def _rows(con: duckdb.DuckDBPyConnection):
    return con.execute(
        f"""
        SELECT Id, PostId, VoteTypeId, CreationDate FROM {db.VOTES_TABLE} ORDER BY Id
        """
    ).fetchall()


def test_ingest_creates_schema_and_table(con: duckdb.DuckDBPyConnection):
    ingest(SAMPLE_FILE, con)
    exists = con.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'blog_analysis' AND table_name = 'votes'
        """
    ).fetchall()
    assert exists == [(1,)], "Expected table 'votes' to exist in schema 'blog_analysis'"


def test_ingest_loads_all_sample_rows(con: duckdb.DuckDBPyConnection):
    ingest(SAMPLE_FILE, con)
    assert _count(con) == 16, "Expected all 16 sample rows to be ingested"


def test_ingest_is_idempotent(con: duckdb.DuckDBPyConnection):
    ingest(SAMPLE_FILE, con)
    ingest(SAMPLE_FILE, con)
    assert _count(con) == 16, "Re-ingesting the same file should not create duplicates"


def test_ingest_updates_changed_record(tmp_path: Path, con: duckdb.DuckDBPyConnection):
    original = tmp_path / "v1.jsonl"
    original.write_text('{"Id":"1","PostId":"1","VoteTypeId":"2","CreationDate":"2022-01-02T00:00:00.000"}\n')
    ingest(str(original), con)

    updated = tmp_path / "v2.jsonl"
    updated.write_text('{"Id":"1","PostId":"99","VoteTypeId":"3","CreationDate":"2022-05-01T00:00:00.000"}\n')
    ingest(str(updated), con)

    assert _count(con) == 1, "A record with an existing Id should be updated, not inserted"
    assert _rows(con) == [(1, 99, 3, datetime.datetime(2022, 5, 1))], "Row should hold the updated values"


def test_ingest_deduplicates_within_a_file(tmp_path: Path, con: duckdb.DuckDBPyConnection):
    data = tmp_path / "dupes.jsonl"
    data.write_text(
        '{"Id":"1","PostId":"1","VoteTypeId":"2","CreationDate":"2022-01-02T00:00:00.000"}\n'
        '{"Id":"1","PostId":"1","VoteTypeId":"2","CreationDate":"2022-06-02T00:00:00.000"}\n'
    )
    ingest(str(data), con)

    assert _count(con) == 1, "Duplicate Ids within a file should collapse to one row"
    assert _rows(con) == [(1, 1, 2, datetime.datetime(2022, 6, 2))], "The later CreationDate should win"
