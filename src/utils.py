from git import Repo


def get_git_branch():
    try:
        repo = Repo(search_parent_directories=True)
        branch = repo.active_branch.name
        return branch
    except Exception:
        raise ValueError("Must be run in a git initialized directory")


CURRENT_BRANCH = get_git_branch()
