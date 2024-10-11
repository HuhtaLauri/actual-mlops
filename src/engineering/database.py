from argparse import ArgumentParser
from dotenv import load_dotenv
from pathlib import Path
from src.db_utils import cursor
import sys
import os
from typing import List
from psycopg.sql import SQL
import time

load_dotenv()

CONNECTION_STRING = os.environ["DATABASE_CONNECTION_STRING"]

class Directory:
    def __init__(self, path: str):
        self.path: Path = Path(path)
        self.files: List[Path] = []

    def collect(self, suffix: str):
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith(suffix):
                    self.files.append(Path(os.path.join(root, file)))
        return self.files

def read_file_to_sql(filepath: Path) -> SQL:
    with open(filepath, "r") as f:
        return SQL(f.read()) # type: ignore


def load(directory: Directory, load_script: SQL, commit: bool):
    start = time.time() 
    with cursor(CONNECTION_STRING, commit) as cur:
        staging_rowcount = 0
        cur.execute("CREATE TEMP TABLE staging (data JSONB) ON COMMIT DROP")
        for file in directory.collect("json"):
            with open(file, "r") as copy_file:
                data = copy_file.read()
            with cur.copy("COPY staging(data) FROM STDIN WITH CSV QUOTE e'\x01' DELIMITER '\x02'") as copy:
                copy.write(data)
            staging_rowcount += cur.rowcount
        
        cur.execute("SELECT COUNT(*) FROM staging")
        cur.execute(load_script)
        
        end = time.time()
        rowcount = cur.rowcount

    print(f"Staged {staging_rowcount} rows")
    print(f"Inserted {rowcount} rows from {len(directory.files)} files in {end - start:.2f} seconds")


def init_db(commit: bool):
    print("initializing")
    with cursor(CONNECTION_STRING, commit) as cur:
        cur.execute(read_file_to_sql(Path("sql/github/ddl/commits_t.sql")))

if __name__ == "__main__":
    parser = ArgumentParser()

    subparsers = parser.add_subparsers()

    load_parser = subparsers.add_parser("load")
    load_parser.add_argument(
        "--directory", "-d", type=lambda x: Directory(x), required=True
    )
    load_parser.add_argument("--load_script",
                             "-S",
                             type=lambda x: read_file_to_sql(Path(x)))
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

