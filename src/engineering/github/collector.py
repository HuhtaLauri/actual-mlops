import requests
from dotenv import load_dotenv
import click
from pathlib import Path
import os
import json
from typing import Dict, Any
from enum import Enum
from datetime import datetime, timedelta
from src.paths import (
    GITHUB_RAW_DATA_DIR,
    GITHUB_COMMITS_RAW_DIR_PATH,
    GITHUB_REPOSITORIES_RAW_DIR_PATH,
)
import shutil


load_dotenv()

API_BASEURL = "https://api.github.com"


class WriteMode(Enum):
    WRITE = "w"
    APPEND = "a"


@click.group()
@click.pass_context
def main(ctx):
    ctx.ensure_object(dict)
    os.makedirs(GITHUB_RAW_DATA_DIR, exist_ok=True)


def construct_api_url(endpoint: str, *args):
    return API_BASEURL + "/" + endpoint + "/" + "/".join(args)


def get_api_data(url: str, params: dict = {}):
    resp = requests.get(url, params=params)

    return resp


def write_result_to_disk(
    result: Dict[str, Any], destination: Path, mode: WriteMode = WriteMode.WRITE
):
    os.makedirs(destination.parents[0], exist_ok=True)
    if isinstance(result, dict):
        _write_dict_data(result, destination, mode)
    else:
        raise NotImplementedError


def _write_dict_data(
    result: Dict[str, Any], destination: Path, mode: WriteMode = WriteMode.WRITE
):
    with open(destination, str(mode.value)) as out_file:
        out_file.write(json.dumps(result))
        out_file.write("\n")


@main.command
@click.option("owner", "--owner", "-o", required=True)
@click.option("repo", "--repository", "-r", required=True)
def collect_repository(owner: str, repo: str):
    resp = _collect_repository(owner, repo)
    destination_file = Path(
        os.path.join(GITHUB_REPOSITORIES_RAW_DIR_PATH, "repositories.json")
    )
    write_result_to_disk(resp, destination_file, mode=WriteMode.APPEND)


def _collect_repository(owner: str, repo: str) -> Dict[str, Any]:
    url = construct_api_url("repos", owner, repo)
    resp = get_api_data(url)

    return resp.json()


@main.command
@click.pass_context
@click.option("owner", "--owner", "-o", required=True)
@click.option("repo", "--repository", "-r", required=True)
@click.option("start_date", "--start-date", "-s")
@click.option("end_date", "--end-date", "-e")
def collect_commits(
    ctx, owner: str, repo: str, start_date: str = "", end_date: str = ""
):
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_date = datetime.now().date() - timedelta(
            days=3
        )  # 100 for ease of dev. Will be 1

    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    else:
        end_date = datetime.now().date() + timedelta(days=1)

    _collect_commits(ctx, owner, repo, start_date, end_date)


def _collect_commits(
    ctx, owner: str, repo: str, start_date: datetime, end_date: datetime
):
    shutil.rmtree(GITHUB_COMMITS_RAW_DIR_PATH, ignore_errors=True)

    url = construct_api_url("repos", owner, repo, "commits")
    params = {"since": str(start_date), "until": str(end_date)}
    commits = []

    is_last = False
    while not is_last:
        resp = get_api_data(url, params)

        for commit in resp.json():
            commits.append(commit)

        # Pagination
        if resp.links.get("next", None):
            url = resp.links["next"]["url"]
        else:
            is_last = True

    destination_file = Path(
        os.path.join(GITHUB_RAW_DATA_DIR, "commits", "commits.json")
    )
    for commit in commits:
        write_result_to_disk(
            result=commit, destination=destination_file, mode=WriteMode.APPEND
        )


if __name__ == "__main__":
    main()
