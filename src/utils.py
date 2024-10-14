from pathlib import Path
import os
from typing import List
import pandas as pd
import json
from loguru import logger
from time import time


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


def file_list_to_df(files: List[Path]) -> pd.DataFrame:
    df: pd.DataFrame
    if str(files[0]).endswith("json"):
        start_time = time()
        data = []
        for file in files:
            with open(file, "r") as in_file:
                [data.append(json.loads(row)) for row in in_file.readlines()]
        df = pd.json_normalize(data)
        end_time = time()
        logger.info(
            f"Constructed dataframe from {len(files)} files ({df.size} rows) in {end_time - start_time:.2f} seconds"
        )

        return df

    return pd.DataFrame()
