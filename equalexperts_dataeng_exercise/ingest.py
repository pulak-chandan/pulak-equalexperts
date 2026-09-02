"""Incremental ingestion of vote data into the blog_analysis.votes table.

Run with:  python -m equalexperts_dataeng_exercise.ingest <path-to-votes.jsonl>

The process is safe to run repeatedly: new records are inserted and records
whose Id already exists are updated, so consumers never see duplicates.
"""

import logging
import sys
from pathlib import Path

import duckdb

from equalexperts_dataeng_exercise import db

logger = logging.getLogger(__name__)

# Upsert with a standard SQL MERGE: match incoming rows to existing ones on Id,
# updating when the Id already exists and inserting when it does not. MERGE is the
# portable ANSI upsert (Postgres/BigQuery/Snowflake/SQL Server all support it),
# rather than DuckDB/Postgres-specific INSERT ... ON CONFLICT.
#
# The source is deduplicated first: read_json_auto reads only the columns we ask
# for (so unexpected fields cannot break ingestion), and ROW_NUMBER keeps just the
# newest CreationDate per Id, so the load stays idempotent even if a file repeats
# an Id. read_json_auto is the one DuckDB-specific piece and is unavoidable here.
UPSERT_SQL = f"""
    MERGE INTO {db.VOTES_TABLE} AS target
    USING (
        SELECT Id, PostId, VoteTypeId, CreationDate
        FROM (
            SELECT
                Id, PostId, VoteTypeId, CreationDate,
                ROW_NUMBER() OVER (PARTITION BY Id ORDER BY CreationDate DESC) AS rn
            FROM read_json_auto(
                ?,
                columns = {{
                    'Id': 'BIGINT',
                    'PostId': 'BIGINT',
                    'VoteTypeId': 'INTEGER',
                    'CreationDate': 'TIMESTAMP'
                }}
            )
        )
        WHERE rn = 1
    ) AS source
    ON target.Id = source.Id
    WHEN MATCHED THEN UPDATE SET
        PostId       = source.PostId,
        VoteTypeId   = source.VoteTypeId,
        CreationDate = source.CreationDate
    WHEN NOT MATCHED THEN INSERT (Id, PostId, VoteTypeId, CreationDate)
        VALUES (source.Id, source.PostId, source.VoteTypeId, source.CreationDate);
"""


def ingest(path: str, con: duckdb.DuckDBPyConnection | None = None) -> int:
    """Ingest a votes JSONL file, returning the total row count afterwards."""
    if not Path(path).is_file():
        raise FileNotFoundError(f"Data file not found: {path}")
    owns_connection = con is None
    con = con or db.connect()
    try:
        logger.info("Ingesting votes from %s", path)
        db.ensure_schema(con)
        con.execute(UPSERT_SQL, [path])
        result = con.execute(f"SELECT COUNT(*) FROM {db.VOTES_TABLE}").fetchone()
        total = int(result[0]) if result else 0
        logger.info("Ingestion complete: %s now contains %d rows", db.VOTES_TABLE, total)
        return total
    finally:
        if owns_connection:
            con.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m equalexperts_dataeng_exercise.ingest <path-to-votes.jsonl>")
    path = sys.argv[1]
    try:
        ingest(path)
    except (FileNotFoundError, duckdb.Error) as error:
        logger.error("Ingestion failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
