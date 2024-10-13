import pandas as pd
from argparse import ArgumentParser
from pathlib import Path
import sys
from loguru import logger
from src.utils import Directory
from sklearn.model_selection import train_test_split
import os


def build_split_from_directory(
    directory: Directory,
    target: str,
    train_portion: float,
    suffix: str,
    target_directory: Directory,
):
    test_portion = 1 - train_portion
    logger.info(
        f"Splitting {directory.path} with {train_portion}/{round(test_portion, 2)} split (train/test)"
    )

    df: pd.DataFrame
    df = pd.concat(
        [pd.read_json(f, lines=True) for f in directory.collect(suffix=suffix)]
    )
    if df.empty:
        raise ValueError("The dataframe is empty")

    train: pd.DataFrame
    test: pd.DataFrame
    train, test = train_test_split(df, train_size=train_portion, test_size=test_portion)  # type: ignore

    if target and target in test.columns:
        test = test.drop(target, axis=1)

    os.makedirs(target_directory.path, exist_ok=True)

    train.to_csv(os.path.join(target_directory.path, "train.csv"), index=False)
    test.to_csv(os.path.join(target_directory.path, "test.csv"), index=False)


if __name__ == "__main__":
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    train_test_parser = subparsers.add_parser("train-test")
    train_test_parser.add_argument(
        "--directory", "-d", type=lambda x: Path(x), required=True
    )
    train_test_parser.add_argument("--target", "-t", help="Target column")
    train_test_parser.add_argument(
        "--train-portion",
        "-tp",
        type=float,
        default=0.8,
        help="Decimal number of train portion",
    )
    train_test_parser.add_argument(
        "--suffix", "-s", type=str, help="Suffix of the collected files", required=True
    )
    train_test_parser.add_argument(
        "--target-directory",
        "-td",
        type=lambda x: Path(x),
        help="Directory where the files are saved",
        required=True,
    )
    train_test_parser.set_defaults(func=build_split_from_directory)

    if len(sys.argv) <= 2:
        parser.print_help()
        sys.exit()

    args = parser.parse_args()
    args.func(
        Directory(args.directory),
        args.target,
        args.train_portion,
        args.suffix,
        Directory(args.target_directory),
    )
