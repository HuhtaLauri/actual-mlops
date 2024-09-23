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
from dotenv import load_dotenv
from src.utils import CURRENT_BRANCH

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

    fs = DVCFileSystem(REPOSITORY_URL, rev=CURRENT_BRANCH)

    file_objects = fs.ls(GITHUB_REPOSITORIES_RAW_DIR_PATH)

    usable_paths_objects = []
    for file_obj in file_objects:
        if file_obj["type"] == "file":
            usable_paths_objects.append(file_obj)

    df = pd.concat(
        [pd.read_json(fp["name"], lines=True) for fp in usable_paths_objects],
        ignore_index=True,
    )
    for col in df.columns:
        if col.endswith("_url"):
            df = df.drop(col, axis=1)
        if col.startswith("has_"):
            df = df.drop(col, axis=1)

    df.to_csv(
        os.path.join(GITHUB_REPOSITORIES_PROCESSED_DIR_PATH, "repositories.csv"),
        index=False,
    )


if __name__ == "__main__":
    main()
