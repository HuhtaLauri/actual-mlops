import argparse
import joblib
import os

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor

from dotenv import load_dotenv

from src.utils import Directory, file_list_to_df
from sqlalchemy import create_engine
from loguru import logger

load_dotenv()


def model_fn(model_dir):
    clf = joblib.load(os.path.join(model_dir, "model.joblib"))
    return clf


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    df["commit_date"] = df["commit.committer.date"].apply(
        lambda x: pd.to_datetime(x[:10])
    )
    df = df.groupby("commit_date").size().reset_index(name="commit_count")

    df["dow"] = df["commit_date"].apply(lambda x: x.weekday())
    df["commit_count_lag1"] = df["commit_count"].shift(1)
    df["commit_count_lag2"] = df["commit_count"].shift(2)
    df["commit_count_lag7"] = df["commit_count"].shift(7)
    df["commit_count_lag30"] = df["commit_count"].shift(30)

    df["commit_epoch"] = df["commit_date"].apply(lambda x: x.timestamp())
    df = df.sort_values("commit_date")

    return df


def build_result_df(predictions: pd.Series, test_x: pd.DataFrame, test_y: pd.Series):
    test_x["value"] = test_y
    test_x["prediction"] = predictions
    test_x["diff"] = test_x["value"] - test_x["prediction"]

    return test_x


def load_result_to_db(df, name: str):
    df["date"] = pd.to_datetime(df["commit_epoch"], unit="s")
    df = df.drop("commit_epoch", axis=1)

    engine = create_engine(os.environ["DATABASE_CONNECTION_STRING"])
    df.to_sql(name, con=engine, if_exists="replace", index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Data, model, and output directories
    parser.add_argument("--model-dir", type=str, default="models")
    parser.add_argument("--data-dir", "-d", type=lambda x: Directory(x))

    args = parser.parse_args()

    df = file_list_to_df(args.data_dir.collect(suffix="json"))
    if df.empty:
        raise ValueError("No dataframe or dataframe is empty")

    df = prepare(df)
    X = df[["commit_epoch", "commit_count_lag1", "commit_count_lag2", "dow"]]
    y = df["commit_count"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.1, random_state=42, shuffle=False
    )

    model = HistGradientBoostingRegressor(max_iter=5000, learning_rate=0.125)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    abs_err = np.abs(preds - y_test)
    for q in [10, 50, 90]:
        logger.info(
            "AE-at-" + str(q) + "th-percentile: " + str(np.percentile(a=abs_err, q=q))
        )

    test_result_df = build_result_df(preds, X_test, y_test)
    load_result_to_db(test_result_df, "prediction")

    # persist model
    path = os.path.join(args.model_dir, "daily-commits.joblib")
    joblib.dump(model, path)
    logger.info("model persisted at " + path)
