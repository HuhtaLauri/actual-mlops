import dvc.api
from dvc.api import DVCFileSystem
import pandas as pd
import click
from src.paths import (
    GITHUB_REPOSITORIES_RAW_DIR_PATH,
    GITHUB_REPOSITORIES_PROCESSED_DIR_PATH,
    REPOSITORY_URL,
)
import os
import shutil
from io import StringIO
from dotenv import load_dotenv

load_dotenv()


@click.group
def main():
    pass


@main.command
def process_repositories():
    shutil.rmtree(
        os.path.join(GITHUB_REPOSITORIES_PROCESSED_DIR_PATH), ignore_errors=True
    )
    os.makedirs(os.path.join(GITHUB_REPOSITORIES_PROCESSED_DIR_PATH), exist_ok=True)

    fs = DVCFileSystem(REPOSITORY_URL, rev="main")

    text = fs.read_text(
        os.path.join(GITHUB_REPOSITORIES_RAW_DIR_PATH, "repositories.json"),
        recursive=False,
    )
    df = pd.read_json(StringIO(text), lines=True)
    for col in df.columns:
        if col.endswith("_url"):
            df = df.drop(col, axis=1)
        if col.startswith("has_"):
            df = df.drop(col, axis=1)

    df.to_csv(
        os.path.join(GITHUB_REPOSITORIES_PROCESSED_DIR_PATH, "repostiories.csv"),
        index=False,
    )


if __name__ == "__main__":
    main()
