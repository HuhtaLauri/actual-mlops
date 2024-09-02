import argparse
import joblib
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from io import StringIO
import sklearn

from dotenv import load_dotenv
from pathlib import Path


load_dotenv(dotenv_path)


def predict_fn(input_data, model):
    prediction = model.predict(input_data)
    pred_prob = model.predict_proba(input_data)
    return np.array([prediction, pred_prob])


# inference functions ---------------
def model_fn(model_dir):
    clf = joblib.load(os.path.join(model_dir, "model.joblib"))
    return clf


def input_fn(request_body, request_content_type):
    raise NotImplementedError


if __name__ == "__main__":
    print("extracting arguments")
    parser = argparse.ArgumentParser()

    parser.add_argument("--n-estimators", type=int, default=10)

    # Data, model, and output directories
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR"))
    parser.add_argument(
        "--train-dir", type=str, default=os.environ.get("SM_CHANNEL_TRAIN")
    )
    parser.add_argument(
        "--test-dir", type=str, default=os.environ.get("SM_CHANNEL_TEST")
    )
    parser.add_argument("--train-file", type=str, default="train.csv")
    parser.add_argument("--test-file", type=str, default="test.csv")

    args, _ = parser.parse_known_args()

    print("reading data")
    train_df = pd.read_csv(os.path.join(args.train_dir, args.train_file))
    test_df = pd.read_csv(os.path.join(args.test_dir, args.test_file))

    print("building training and testing datasets")
    X_train = pd.get_dummies(train_df[args.features.split()])
    y_train = train_df[args.target]
    X_test = pd.get_dummies(test_df[args.features.split()])
    y_test = test_df[args.target]
    print(X_train.head())

    # train
    print("training model")
    model = RandomForestClassifier(
        n_estimators=args.n_estimators, max_depth=5, random_state=1
    )

    model.fit(X_train.values, y_train)

    # print abs error
    print("validating model")
    abs_err = np.abs(model.predict(X_test) - y_test)

    # print couple perf metrics
    for q in [10, 50, 90]:
        print(
            "AE-at-" + str(q) + "th-percentile: " + str(np.percentile(a=abs_err, q=q))
        )

    # persist model
    path = os.path.join(args.model_dir, "model.joblib")
    joblib.dump(model, path)
    print("model persisted at " + path)
