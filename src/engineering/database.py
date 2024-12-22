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
from datetime import datetime, timedelta
from typing import List

load_dotenv()

CONNECTION_STRING = os.environ["DATABASE_CONNECTION_STRING"]


def read_file_to_sql(filepath: Path) -> SQL:
    with open(filepath, "r") as f:
        return SQL(f.read())  # type: ignore


def load(directory: Directory, load_script: List[SQL], commit: bool):
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
        for load_script in load_scripts:
            cur.execute(load_script)

        end = time.time()
        rowcount = cur.rowcount

    logger.info(f"Staged {staging_rowcount} rows from {len(directory.files)} files")
    logger.info(f"Inserted {rowcount} rows in {end - start:.2f} seconds")


def init_db(commit: bool):
    logger.info("initializing")
    with cursor(CONNECTION_STRING, commit) as cur:
        cur.execute(read_file_to_sql(Path("sql/github/ddl/commits_t.sql")))
        cur.execute(read_file_to_sql(Path("sql/github/ddl/users_t.sql")))
        cur.execute(read_file_to_sql(Path("sql/github/ddl/issues_t.sql")))
        cur.execute(read_file_to_sql(Path("sql/github/ddl/daily_issues_t.sql")))


def daily_issues(num_days: int):
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=num_days)

    with cursor(CONNECTION_STRING, commit=True) as cur:
        sql = read_file_to_sql(Path("sql/github/etl/load-daily-issues.sql"))
        while start_date <= end_date:
            logger.info(f"Creating daily issues for date {start_date}")
            cur.execute(sql.format(current_date=str(start_date)))
            logger.info(f"Inserted {cur.rowcount} rows for date {start_date}")
            start_date = start_date + timedelta(days=1)


if __name__ == "__main__":
    parser = ArgumentParser()

    subparsers = parser.add_subparsers()

    load_parser = subparsers.add_parser("load")
    load_parser.add_argument(
        "--directory", "-d", type=lambda x: Directory(x), required=True
    )
    load_parser.add_argument(
        "--load_script", "-S", nargs="+", type=str
    )
    load_parser.add_argument("--commit", "-c", default=False, action="store_true")

    init_parser = subparsers.add_parser("init")
    init_parser.set_defaults(func=init_db)
    init_parser.add_argument("--commit", "-c", default=False, action="store_true")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    load_parser.set_defaults(func=load)

    daily_measures_parser = subparsers.add_parser("daily")
    daily_measures_parser.add_argument("--num_days", type=int, default=3)
    daily_measures_parser.set_defaults(func=daily_issues)

    args = parser.parse_args()

    func_name = args.func.__name__
    if func_name == "load":
        load_scripts = list(map(read_file_to_sql, args.load_script))
        args.func(args.directory, load_scripts, args.commit)
    elif func_name == "init_db":
        args.func(args.commit)
    elif func_name == "daily_issues":
        args.func(args.num_days)
