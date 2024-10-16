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
    GITHUB_ISSUES_RAW_DIR_PATH,
)
import shutil
import argparse
from dataclasses import dataclass
import concurrent.futures


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
    source: str,
    result: Union[Dict[str, Any], List],
    destination: Path,
    partition_column_path: str,
):
    os.makedirs(destination.parents[0], exist_ok=True)
    if source == "repos":
        _write_dict_data(result, destination)
    else:
        _write_list_data(
            result, destination, partition_column_path=partition_column_path
        )


def _write_dict_data(result: Dict[str, Any], destination: Path):
    with open(os.path.join(destination, "data.json"), "a") as out_file:
        for row in result:
            out_file.write(json.dumps(row))
            out_file.write("\n")


def _write_list_data(result: List, destination: Path, partition_column_path: str):
    from itertools import groupby

    groups = []
    keys = []

    for k, g in groupby(
        result, lambda x: str(get_nested_value(x, partition_column_path))[:10]
    ):
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


def get_nested_value(data, path):
    keys = path.split(".")
    value = data
    try:
        for key in keys:
            value = value[key]
        return value
    except KeyError:
        return None


def collect_repositories(
    repository: Repository,
    since: datetime,
    until: datetime,
):
    params = {"since": since, "until": until}
    url = construct_api_url("repos", repository.owner, repository.name)

    repos = collect_and_paginate(url=url)
    return repos


def collect_commits(
    repository: Repository,
    since: datetime,
    until: datetime,
):
    params = {"since": since, "until": until}
    url = construct_api_url("repos", repository.owner, repository.name, "commits")

    commits = collect_and_paginate(url=url, params=params)

    return commits


def collect_issues(
    repository: Repository,
    since: datetime,
    until: datetime,
):
    params = {"since": since, "until": until}
    url = construct_api_url("repos", repository.owner, repository.name, "issues")

    issues = collect_and_paginate(url=url, params=params)

    return issues


def collect_and_paginate(url: str, params: dict = {}):
    data = []

    is_last = False
    resp = get_api_data(url)
    while not is_last:
        resp = get_api_data(url, params)
        resp_data = resp.json()
        if isinstance(resp_data, list):
            for row in resp_data:
                data.append(row)
        else:
            data = resp_data

        # Pagination
        if resp.links.get("next", None):
            url = resp.links["next"]["url"]
        else:
            is_last = True

    return data


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

    collector_map = {
        "commits": collect_commits,
        "repos": collect_repositories,
        "issues": collect_issues,
    }

    destination_map = {
        "commits": GITHUB_COMMITS_RAW_DIR_PATH,
        "repos": GITHUB_REPOSITORIES_RAW_DIR_PATH,
        "issues": GITHUB_ISSUES_RAW_DIR_PATH,
    }

    if source in ["commits"]:
        partition_column_path = "commit.committer.date"
    else:
        partition_column_path = "updated_at"

    shutil.rmtree(destination_map[source], ignore_errors=True)
    os.makedirs(destination_map[source], exist_ok=True)

    collector_func = collector_map[source]

    # Setting arguments here
    def collect_for_repo(repo):
        return collector_func(repo, since=since, until=until)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(repos)) as executor:
        futures = [executor.submit(collect_for_repo, repo) for repo in repos]

        data = []
        for future in concurrent.futures.as_completed(futures):
            if source == "repos":
                data.append(future.result())
            else:
                data.extend(future.result())

    write_result_to_disk(
        source,
        data,
        destination=destination_map[source],
        partition_column_path=partition_column_path,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repos",
        nargs="+",
        required=True,
        help="GitHub repositories (e.g., user/repo1 user/repo2 or a file containing them)",
    )

    parser.add_argument(
        "--source", "-s", required=True, choices=["commits", "repos", "issues"]
    )

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
