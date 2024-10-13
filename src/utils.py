from pathlib import Path
import os
from typing import List


class Directory:
    def __init__(self, path: str):
        self.path: Path = Path(path)
        self.files: List[Path] = []

    def collect(self, suffix: str):
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith(suffix):
                    self.files.append(Path(os.path.join(root, file)))
        return self.files
