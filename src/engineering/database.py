from argparse import ArgumentParser
from dotenv import load_dotenv
from pathlib import Path
from src.db_utils import cursor
from src.utils import Directory
import sys
import os
from psycopg.sql import SQL
import time
from loguru import logger

load_dotenv()

CONNECTION_STRING = os.environ["DATABASE_CONNECTION_STRING"]


def read_file_to_sql(filepath: Path) -> SQL:
    with open(filepath, "r") as f:
        return SQL(f.read())  # type: ignore


def load(directory: Directory, load_script: SQL, commit: bool):
    start = time.time()
    with cursor(CONNECTION_STRING, commit) as cur:
        staging_rowcount = 0
        cur.execute("CREATE TEMP TABLE staging (data JSONB) ON COMMIT DROP")
        for file in directory.collect("json"):
            with open(file, "r") as copy_file:
                data = copy_file.read()
            with cur.copy(
                "COPY staging(data) FROM STDIN WITH CSV QUOTE e'\x01' DELIMITER '\x02'"
            ) as copy:
                copy.write(data)
            staging_rowcount += cur.rowcount

        cur.execute("SELECT COUNT(*) FROM staging")
        cur.execute(load_script)

        end = time.time()
        rowcount = cur.rowcount

    logger.info(f"Staged {staging_rowcount} rows from {len(directory.files)} files")
    logger.info(f"Inserted {rowcount} rows in {end - start:.2f} seconds")


def init_db(commit: bool):
    logger.info("initializing")
    with cursor(CONNECTION_STRING, commit) as cur:
        cur.execute(read_file_to_sql(Path("sql/github/ddl/commits_t.sql")))
        cur.execute(read_file_to_sql(Path("sql/github/ddl/authors_t.sql")))
        cur.execute(read_file_to_sql(Path("sql/github/ddl/issues_t.sql")))


if __name__ == "__main__":
    parser = ArgumentParser()

    subparsers = parser.add_subparsers()

    load_parser = subparsers.add_parser("load")
    load_parser.add_argument(
        "--directory", "-d", type=lambda x: Directory(x), required=True
    )
    load_parser.add_argument(
        "--load_script", "-S", type=lambda x: read_file_to_sql(Path(x))
    )
    load_parser.add_argument("--commit", "-c", default=False, action="store_true")

    init_parser = subparsers.add_parser("init")
    init_parser.set_defaults(func=init_db)
    init_parser.add_argument("--commit", "-c", default=False, action="store_true")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    load_parser.set_defaults(func=load)

    args = parser.parse_args()

    func_name = args.func.__name__
    if func_name == "load":
        args.func(args.directory, args.load_script, args.commit)
    elif func_name == "init_db":
        args.func(args.commit)
