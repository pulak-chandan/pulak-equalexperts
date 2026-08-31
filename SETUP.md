# Setup Instructions

## Software prerequisites

This exercise uses [uv](https://docs.astral.sh/uv/) to manage Python and project dependencies. Install `uv` using the instructions for your operating system in the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

The project requires Python 3.14. `uv` will use an installed Python 3.14 interpreter or download a managed copy when needed.

From the root of the repository, create the environment and install the locked dependencies:

```shell
uv sync --locked
```

`uv sync` creates a local `.venv` and installs both the application and development dependencies. The committed `uv.lock` file makes the environment reproducible. If you add or change dependencies, use `uv add` or `uv add --dev`, then commit both `pyproject.toml` and `uv.lock`.

## Running with Docker

Docker is an alternative to installing Python and `uv` locally. You need [Docker Desktop](https://www.docker.com/products/docker-desktop/), or an alternative such as [Rancher Desktop](https://rancherdesktop.io/) or [Colima](https://github.com/abiosoft/colima), with Compose support. From the repository root, build the image:

```shell
docker compose build
```

> **Apple Silicon note**
> Build the image natively on Mac M1/M2 systems first. If the native ARM64 build fails, use an emulated AMD64 image by adding `platform: linux/amd64` to the `exercise` service in `compose.yaml`, then rebuild and run the image. Docker will run the AMD64 image through emulation.

The repository includes a valid empty DuckDB database in `warehouse.db`; do not replace it with a zero-byte file. Docker Compose seeds a named volume from this database on first use and keeps subsequent changes in that volume, so Docker commands do not modify the checked-out `warehouse.db`. To start Docker with a fresh database, remove the volume with `docker compose down -v` and rebuild if needed. The same commands work on macOS, Linux, and Windows:

```shell
docker compose run --rm exercise fetch-data
docker compose run --rm exercise ingest-data
docker compose run --rm exercise detect-outliers
docker compose run --rm exercise test
docker compose run --rm exercise check-ingestion
docker compose run --rm exercise check-outliers
```

Run the first three commands in order before the checks. Make sure Docker Desktop (Windows/macOS) or a Docker Engine (Linux) is running.

## Running the exercise

Use `uv run` to run commands in the project environment:

```shell
uv run exercise --help
```

For example, to run the ingestion process you will write in `ingest.py`:

```shell
uv run exercise ingest-data
```

The other useful commands are:

```shell
uv run exercise fetch-data
uv run exercise detect-outliers
uv run exercise check-ingestion
uv run exercise check-outliers
uv run exercise lint
uv run exercise test
```

## Bootstrap solution

This repository contains a bootstrap solution that you can use to build upon.

You can make any changes you like, as long as the solution can still be executed using the `exercise.py` script.
The base solution uses [DuckDB](https://duckdb.org/) as the database, and for your solution we want you to treat it like a real (OLAP) data warehouse.
The database should be saved in the root folder of the project on the local disk as `warehouse.db`, as shown in the `tests/db_test.py` file.

We also provide the structure for:
* `equalexperts_dataeng_exercise/ingest.py` - the entry point for running the ingestion process.
* `equalexperts_dataeng_exercise/outliers.py` - the entry point for running the outlier detection query.
* `equalexperts_dataeng_exercise/db.py` - is empty, but the associated test demonstrates interaction with a DuckDB database.
