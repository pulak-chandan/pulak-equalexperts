"""Shared DuckDB access for the exercise.

A single place that knows the warehouse location and the physical model, so
ingestion and the outliers query cannot drift out of sync on names or types.
"""

import logging

import duckdb

logger = logging.getLogger(__name__)

WAREHOUSE_PATH = "warehouse.db"
SCHEMA = "blog_analysis"
VOTES_TABLE = f"{SCHEMA}.votes"

# Types chosen for an OLAP warehouse: fixed-width numerics for the identifiers
# and a real TIMESTAMP for the date so week/year can be derived in SQL. Id is
# the business key we upsert on, so it is the primary key.
CREATE_VOTES_TABLE = f"""
    CREATE TABLE IF NOT EXISTS {VOTES_TABLE} (
        Id            BIGINT PRIMARY KEY,
        PostId        BIGINT,
        VoteTypeId    INTEGER,
        CreationDate  TIMESTAMP
    );
"""


def connect(path: str = WAREHOUSE_PATH, *, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open a connection to the warehouse database file."""
    return duckdb.connect(path, read_only=read_only)


def ensure_schema(con: duckdb.DuckDBPyConnection) -> None:
    """Create the schema and votes table if they do not already exist."""
    logger.debug("Ensuring schema %s and table %s exist", SCHEMA, VOTES_TABLE)
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};")
    con.execute(CREATE_VOTES_TABLE)
