"""This module prepares the Iris dataset for training a model."""

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split


def prepare_data():
    iris = load_iris()
    X = iris.data
    y = iris.target
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    return X_train, X_test, y_train, y_test
