from pathlib import Path
import os


DATA_ROOT = Path("data")

# RAW
GITHUB_RAW_DATA_DIR = Path(os.path.join(DATA_ROOT, "raw"))
GITHUB_COMMITS_RAW_DIR_PATH = Path(os.path.join(GITHUB_RAW_DATA_DIR, "commits"))
GITHUB_REPOSITORIES_RAW_DIR_PATH = Path(
    os.path.join(GITHUB_RAW_DATA_DIR, "repositories")
)

# ML
GITHUB_ML_DATA_DIR = Path(os.path.join(DATA_ROOT, "ml"))
GITHUB_COMMITS_ML_DIR_PATH = Path(os.path.join(GITHUB_ML_DATA_DIR, "commits"))
