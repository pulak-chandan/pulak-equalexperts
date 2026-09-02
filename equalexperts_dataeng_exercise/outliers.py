"""Outlier-week calculation over ingested vote data.

Run with:  python -m equalexperts_dataeng_exercise.outliers

Recreates the blog_analysis.outlier_weeks view and prints its contents.
"""

import logging

import duckdb

from equalexperts_dataeng_exercise import db

logger = logging.getLogger(__name__)

OUTLIER_VIEW = f"{db.SCHEMA}.outlier_weeks"

# strftime %W gives a week number where the days before the first full week are
# week 0 (matching the expected sample output where 2022-01-02 falls in week 0).
# A week is an outlier when its vote count differs from the dataset mean by
# more than 20%, i.e. |1 - x_i / mean| > 0.2.
CREATE_OUTLIER_VIEW = f"""
    CREATE OR REPLACE VIEW {OUTLIER_VIEW} AS
    WITH weekly_votes AS (
        SELECT
            CAST(strftime(CreationDate, '%Y') AS INTEGER) AS Year,
            CAST(strftime(CreationDate, '%W') AS INTEGER) AS WeekNumber,
            COUNT(*) AS VoteCount
        FROM {db.VOTES_TABLE}
        GROUP BY Year, WeekNumber
    ),
    mean_votes AS (
        SELECT AVG(VoteCount) AS mean_votes_per_week FROM weekly_votes
    )
    SELECT Year, WeekNumber, VoteCount
    FROM weekly_votes, mean_votes
    WHERE ABS(1 - VoteCount / mean_votes_per_week) > 0.2
    ORDER BY Year, WeekNumber;
"""


def create_view(con: duckdb.DuckDBPyConnection) -> None:
    """(Re)create the outlier_weeks view."""
    logger.info("Creating view %s", OUTLIER_VIEW)
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {db.SCHEMA};")
    con.execute(CREATE_OUTLIER_VIEW)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    con = db.connect()
    try:
        create_view(con)
        con.sql(f"SELECT * FROM {OUTLIER_VIEW}").show()
    except duckdb.Error as error:
        logger.error("Outlier calculation failed (has data been ingested?): %s", error)
        raise SystemExit(1) from error
    finally:
        con.close()


if __name__ == "__main__":
    main()
