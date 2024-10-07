import requests
from dotenv import load_dotenv
from pathlib import Path
import os
import json
from typing import Dict, Any, List, Union
from enum import Enum
from datetime import datetime, timedelta
from src.paths import (
    GITHUB_COMMITS_RAW_DIR_PATH,
    GITHUB_REPOSITORIES_RAW_DIR_PATH,
)
import shutil
import argparse
from dataclasses import dataclass


load_dotenv()

API_BASEURL = "https://api.github.com"


class WriteMode(Enum):
    WRITE = "w"
    APPEND = "a"


@dataclass
class Repository:
    owner: str
    name: str


def construct_api_url(endpoint: str, *args):
    return API_BASEURL + "/" + endpoint + "/" + "/".join(args)


def get_api_data(url: str, params: dict = {}):
    bearer_token = f'Bearer {os.environ["GITHUB_TOKEN"]}'
    headers = {"Authorization": bearer_token, "X-GitHub-Api-Version": "2022-11-28"}
    resp = requests.get(url, params=params, headers=headers)

    return resp


def write_result_to_disk(
    result: Union[Dict[str, Any], List], destination: Path, mode: WriteMode
):
    os.makedirs(destination.parents[0], exist_ok=True)
    if isinstance(result, dict):
        _write_dict_data(result, destination, mode)
    else:
        _write_list_data(result, destination, mode)


def _write_dict_data(
    result: Dict[str, Any], destination: Path, mode: WriteMode = WriteMode.WRITE
):
    with open(destination, str(mode.value)) as out_file:
        out_file.write(json.dumps(result))
        out_file.write("\n")


def _write_list_data(
    result: List, destination: Path, mode: WriteMode = WriteMode.APPEND
):
    from itertools import groupby

    groups = []
    keys = []

    for k, g in groupby(result, lambda x: str(x["commit"]["committer"]["date"])[:10]):
        groups.append(list(g))  # Store group iterator as a list
        keys.append(k)

    for k, g in zip(keys, groups):
        out_dirpath = os.path.join(destination, k.replace("-", "/"))
        out_filepath = os.path.join(out_dirpath, "data.json")

        os.makedirs(out_dirpath, exist_ok=True)
        with open(out_filepath, "a") as out_file:
            for row in g:
                out_file.write(json.dumps(row))
                out_file.write("\n")


def collect_repositories(repositories: List[Repository]):
    shutil.rmtree(GITHUB_REPOSITORIES_RAW_DIR_PATH, ignore_errors=True)
    os.makedirs(GITHUB_REPOSITORIES_RAW_DIR_PATH, exist_ok=True)
    for repo in repositories:
        data = _collect_repository_data(repo)
        write_result_to_disk(
            result=data,
            destination=Path(
                os.path.join(GITHUB_REPOSITORIES_RAW_DIR_PATH),
                f"{repo.owner}-{repo.name}.json",
            ),
            mode=WriteMode.APPEND,
        )


def _collect_repository_data(repo: Repository):
    url = construct_api_url("repos", repo.owner, repo.name)
    resp = get_api_data(url)

    if resp.status_code == 200:
        return resp.json()
    else:
        raise ValueError("No repository data found")


def collect_commits(
    repositories: List[Repository],
    since: datetime,
    until: datetime,
):
    shutil.rmtree(GITHUB_COMMITS_RAW_DIR_PATH, ignore_errors=True)
    os.makedirs(GITHUB_COMMITS_RAW_DIR_PATH, exist_ok=True)

    commits = []

    params = {"since": since, "until": until}

    for repo in repositories:
        commits = commits + _collect_commits_data(repo, params)

    return commits


def _collect_commits_data(repo: Repository, params: Dict[str, datetime]) -> list:
    url = construct_api_url("repos", repo.owner, repo.name, "commits")
    resp = get_api_data(url)

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

    return commits


def read_repos_from_file(filepath: Path) -> List[Repository]:
    repos: List[Repository] = []
    with open(filepath, "r") as repos_file:
        for repo in repos_file.readlines():
            owner, name = repo.strip().split("/")
            repository = Repository(owner=owner, name=name)
            repos.append(repository)

    return repos


def main(source: str, repos: list, since: datetime, until: datetime):
    print(repos)
    repos = list(map(lambda repo: Repository(*repo.split("/")), repos))

    collector_map = {"commits": collect_commits}

    destination_map = {"commits": GITHUB_COMMITS_RAW_DIR_PATH}

    collector_func = collector_map[source]
    data: List[dict] = collector_func(repositories=repos, since=since, until=until)

    write_result_to_disk(
        data, destination=destination_map[source], mode=WriteMode.APPEND
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repos",
        nargs="+",
        required=True,
        help="GitHub repositories (e.g., user/repo1 user/repo2 or a file containing them)",
    )

    parser.add_argument("--source", "-s", required=True, choices=["commits"])

    parser.add_argument(
        "-n",
        "--num-days",
        type=int,
        help="NUM-DAYS argument takes precedence to [SINCE] and [UNTIL]",
    )

    parser.add_argument(
        "--since",
        "-S",
        type=lambda x: datetime.strptime(x, "%Y-%m-%d"),
        default=datetime.now().date() - timedelta(days=3),
    )

    parser.add_argument(
        "--until",
        "-U",
        type=lambda x: datetime.strptime(x, "%Y-%m-%d"),
        default=datetime.now(),
    )

    args = parser.parse_args()
    if len(args.repos) == 1 and os.path.exists(args.repos[0]):
        with open(args.repos[0], "r") as repo_file:
            repos = repo_file.readlines()
            repos = list(map(str.strip, repos))
    else:
        repos = args.repos

    if args.num_days:
        since = datetime.now().date() - timedelta(days=args.num_days)
        until = datetime.now().date()
    else:
        since = args.since
        until = args.until

    print(f"Collecting for {repos} ({since}-{until})")
    main(source=args.source, repos=repos, since=since, until=until)
