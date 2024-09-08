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
    resp = requests.get(url, params=params)

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
    with open(destination, str(mode.value)) as out_file:
        for row in result:
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


def set_commit_params(
    starttime: Union[str, None] = None, endtime: Union[str, None] = None
) -> Dict[str, str]:
    if isinstance(starttime, str):
        try:
            start = datetime.strptime(starttime, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Invalid starttime format: {starttime}. Expected format: YYYY-MM-DD."
            )
    else:
        start = datetime.now() - timedelta(days=7)

    if isinstance(endtime, str):
        try:
            end = datetime.strptime(endtime, "%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Invalid endtime format: {starttime}. Expected format: YYYY-MM-DD."
            )
    else:
        end = datetime.now()

    return {"since": start.isoformat(), "until": end.isoformat()}


def collect_commits(
    repositories: List[Repository],
    starttime: Union[str, None],
    endtime: Union[str, None],
):
    shutil.rmtree(GITHUB_COMMITS_RAW_DIR_PATH, ignore_errors=True)
    os.makedirs(GITHUB_COMMITS_RAW_DIR_PATH, exist_ok=True)

    params = set_commit_params(starttime, endtime)

    commits = {}
    for repo in repositories:
        fullname = repo.owner + "-" + repo.name
        commits[fullname] = _collect_commits_data(repo, params)

    repo_keys = list(commits.keys())
    for repo_key in repo_keys:
        destination_file = Path(
            os.path.join(GITHUB_COMMITS_RAW_DIR_PATH, f"{repo_key}.json")
        )
        write_result_to_disk(commits[repo_key], destination_file, WriteMode.APPEND)


def _collect_commits_data(repo: Repository, params: Dict[str, str]):
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


def main():
    parser = argparse.ArgumentParser(
        description="A CLI tool for GitHub data collection."
    )

    shared_parser = argparse.ArgumentParser(add_help=False)
    shared_parser.add_argument(
        "--repos",
        nargs="+",
        required=True,
        help="GitHub repositories (e.g., user/repo1 user/repo2 or a file containing them)",
    )

    # Create subparsers for the subcommands
    subparsers = parser.add_subparsers(
        dest="command", help="Subcommands to run different functionalities"
    )

    # Subcommand for collecting commits
    commit_parser = subparsers.add_parser(
        "collect-commits",
        parents=[shared_parser],
        help="Collect commits from repositories",
    )
    commit_parser.add_argument(
        "--starttime",
        default=None,
        help="Earliest point to get commit data from [YYYY-MM-DD]",
    )
    commit_parser.add_argument(
        "--endtime",
        default=None,
        help="Last point to get commit data up to [YYYY-MM-DD]",
    )

    # Subcommand for collecting repositories
    repo_parser = subparsers.add_parser(
        "collect-repos",
        parents=[shared_parser],
        help="Collect repositories from a GitHub user",
    )

    args = parser.parse_args()

    # Check if the first argument is a file
    if len(args.repos) == 1 and os.path.isfile(args.repos[0]):
        repos = read_repos_from_file(args.repos[0])
    else:
        repos = []
        for repo in args.repos:
            owner, name = repo.split("/")
            repository = Repository(owner=owner, name=name)
            repos.append(repository)

    # Determine which subcommand was used and call the corresponding function
    if args.command == "collect-commits":
        collect_commits(repos, args.starttime, args.endtime)
    elif args.command == "collect-repos":
        collect_repositories(repos)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
