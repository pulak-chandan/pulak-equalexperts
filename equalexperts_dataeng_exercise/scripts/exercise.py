"""
You shouldn't need to change this file.

This is a utility script which allows you to quickly run and test various parts of the exercise.

Use 'uv run exercise --help' to see the various options

For example

    uv run exercise ingest-data
    uv run exercise detect-outliers
    uv run exercise test

"""

import os
import subprocess
import sys
import sysconfig
from pathlib import Path

import duckdb
import typer

app = typer.Typer()


def run_cmd(cmd: str):
    env = os.environ.copy()
    python_dir = str(Path(sys.executable).parent)
    env["PATH"] = os.pathsep.join([python_dir, env.get("PATH", "")])
    site_packages = sysconfig.get_paths()["purelib"]
    env["PYTHONPATH"] = os.pathsep.join([site_packages, env.get("PYTHONPATH", "")])
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.Popen(cmd, shell=True, env=env)
    proc.communicate()
    if proc.returncode:
        raise SystemExit(proc.returncode)


@app.command()
def tidy():
    run_cmd(f"{sys.executable} -m ruff check --fix --unsafe-fixes --extend-select I equalexperts_dataeng_exercise")
    run_cmd(f"{sys.executable} -m ruff format equalexperts_dataeng_exercise")


@app.command()
def lint():
    run_cmd("mypy equalexperts_dataeng_exercise")
    run_cmd("ruff check equalexperts_dataeng_exercise")


@app.command()
def test():
    run_cmd(
        f"{sys.executable} -m pytest --cov=equalexperts_dataeng_exercise equalexperts_dataeng_exercise tests "
        f"--ignore={Path('tests') / 'exercise_tests'}"
    )


@app.command()
def fetch_data():
    run_cmd(f"{sys.executable} -m equalexperts_dataeng_exercise.scripts.fetch_data")


@app.command()
def ingest_data():
    path_to_data = Path("uncommitted") / "votes.jsonl"
    run_cmd(f"{sys.executable} -m equalexperts_dataeng_exercise.ingest {path_to_data}")


@app.command()
def run_query(query: str):
    conn = duckdb.connect("warehouse.db")
    result = conn.sql(query)
    result.show()


@app.command()
def detect_outliers():
    run_cmd(f"{sys.executable} -m equalexperts_dataeng_exercise.outliers")


@app.command()
def check_ingestion():
    run_cmd(f"{sys.executable} -m pytest {Path('tests') / 'exercise_tests' / 'test_ingestion.py'}")


@app.command()
def check_outliers():
    run_cmd(f"{sys.executable} -m pytest {Path('tests') / 'exercise_tests' / 'test_outliers.py'}")


def main():
    app()


if __name__ == "__main__":
    main()
