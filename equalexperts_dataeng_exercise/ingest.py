"""Incremental ingestion of vote data into the blog_analysis.votes table.

Run with:  python -m equalexperts_dataeng_exercise.ingest <path-to-votes.jsonl>

The process is safe to run repeatedly: new records are inserted and records
whose Id already exists are updated, so consumers never see duplicates.
"""

import argparse
import logging
import sys
from pathlib import Path

import duckdb

from equalexperts_dataeng_exercise import db

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s::: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Upsert with a standard SQL MERGE: match incoming rows to existing ones on Id,
# updating when the Id already exists and inserting when it does not.
VOTES_TABLE_UPSERT_SQL = f"""
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


def ingest(path: str, con: duckdb.DuckDBPyConnection):
    """Ingest a votes JSONL file."""
    logger.info(f"Ingesting votes from {path}")
    con.execute(VOTES_TABLE_UPSERT_SQL, [path])
    result = con.execute(
        f"""
        SELECT COUNT(*) FROM {db.VOTES_TABLE}
        """
    ).fetchone()
    total = result[0] if result else 0
    logger.info(f"Ingestion complete: {db.VOTES_TABLE} now contains {total} rows")


def ensure_data_file_exists(path: str):
    """Verify that the data file exists."""
    if not Path(path).is_file():
        raise FileNotFoundError(f"Data file not found: {path}")
    logger.info(f"Data file verified: {path}")


def ensure_schema_exists(con: duckdb.DuckDBPyConnection):
    """Ensure the schema exists in the database."""
    db.ensure_schema(con)
    logger.info(f"Schema ensured: {db.SCHEMA}")


def ingest_data(path: str):
    """Orchestrate the ingestion process."""
    con = db.connect()

    ensure_data_file_exists(path)
    ensure_schema_exists(con)
    ingest(path, con)
    con.close()


def main():
    """Entry point: parse arguments and orchestrate ingestion."""
    parser = argparse.ArgumentParser(description="Ingest vote data into the database")
    parser.add_argument("path", help="Path to votes JSONL file")
    args = parser.parse_args()
    ingest_data(args.path)
    logger.info("All Done!")


if __name__ == "__main__":
    main()
