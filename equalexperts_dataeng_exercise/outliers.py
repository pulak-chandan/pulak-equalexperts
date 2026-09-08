"""Outlier-week calculation over ingested vote data.
Recreates the blog_analysis.outlier_weeks view and prints its contents.
"""

import logging
import sys

import duckdb

from equalexperts_dataeng_exercise import db

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s::: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

OUTLIER_VIEW = f"{db.SCHEMA}.outlier_weeks"

# A week is an outlier when its vote count differs from the dataset mean by
# more than 20% (i.e., VoteCount > 1.2 * avg or VoteCount < 0.8 * avg).
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
    vote_stats AS (
        SELECT
            Year,
            WeekNumber,
            VoteCount,
            AVG(VoteCount) OVER () AS avg_votes,
            0.8 * AVG(VoteCount) OVER () AS lower_bound,
            1.2 * AVG(VoteCount) OVER () AS upper_bound
        FROM weekly_votes
    )
    SELECT Year, WeekNumber, VoteCount
    FROM vote_stats
    WHERE VoteCount < lower_bound OR VoteCount > upper_bound
    ORDER BY Year, WeekNumber;
"""


def create_view(con: duckdb.DuckDBPyConnection):
    """(Re)create the outlier_weeks view."""
    logger.info(f"Creating view {OUTLIER_VIEW}")
    con.execute(
        f"""
        CREATE SCHEMA IF NOT EXISTS {db.SCHEMA};
        """
    )
    con.execute(CREATE_OUTLIER_VIEW)


def display_outliers(con: duckdb.DuckDBPyConnection):
    """Display the outlier weeks."""
    logger.info(f"Displaying outliers from {OUTLIER_VIEW}")
    result = con.sql(
        f"""
        SELECT * FROM {OUTLIER_VIEW}
        """
    )
    print(result)


def calculate_outliers():
    con = db.connect()
    create_view(con)
    display_outliers(con)
    con.close()


if __name__ == "__main__":
    calculate_outliers()
