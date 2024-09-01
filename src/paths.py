from pathlib import Path
import os


GITHUB_ROOT_PATH = Path(os.path.join("src", "engineering", "github"))

# RAW
GITHUB_RAW_DATA_DIR = Path(os.path.join(GITHUB_ROOT_PATH, "data", "raw"))
GITHUB_COMMITS_RAW_DIR_PATH = Path(os.path.join(GITHUB_RAW_DATA_DIR, "commits"))
GITHUB_REPOSITORIES_RAW_DIR_PATH = Path(os.path.join(GITHUB_RAW_DATA_DIR, "repositories"))

# PROCESSED
GITHUB_PROCESSED_DATA_DIR = Path(os.path.join(GITHUB_ROOT_PATH, "data", "processed"))
GITHUB_COMMITS_PROCESSED_DIR_PATH = Path(os.path.join(GITHUB_PROCESSED_DATA_DIR, "commits"))
GITHUB_REPOSITORIES_PROCESSED_DIR_PATH = Path(os.path.join(GITHUB_PROCESSED_DATA_DIR, "repositories"))
