"""This module defines the default model and its parameters for training."""

from sklearn.ensemble import RandomForestClassifier

params = {
    "n_estimators": 100,
    "max_depth": None,
    "random_state": 42,
    "criterion": "gini",
}
# params = {}
model = RandomForestClassifier(**params)
