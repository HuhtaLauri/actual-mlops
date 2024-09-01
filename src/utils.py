from git import Repo


def get_git_branch():
    try:
        repo = Repo(search_parent_directories=True)
        branch = repo.active_branch.name
        return branch
    except Exception as e:
        return None

CURRENT_BRANCH = get_git_branch()
