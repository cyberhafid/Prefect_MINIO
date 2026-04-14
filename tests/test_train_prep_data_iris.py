import numpy as np
from services.prep_data_iris import prepare_data


def test_prepare_data_shapes():
    """Vérifie que le split 80/20 est respecté sur les 150 lignes d'Iris"""
    X_train, X_test, y_train, y_test = prepare_data()

    # Iris a 150 échantillons au total
    # 80% de 150 = 120
    # 20% de 150 = 30
    assert len(X_train) == 120
    assert len(X_test) == 30
    assert len(y_train) == 120
    assert len(y_test) == 30


def test_prepare_data_content():
    """Vérifie le format des données en sortie"""
    X_train, X_test, y_train, y_test = prepare_data()

    # Vérifie qu'il y a bien 4 features (sepal length/width, petal length/width)
    assert X_train.shape[1] == 4

    # Vérifie que ce sont des arrays numpy (ou convertibles)
    assert isinstance(X_train, np.ndarray)
    assert isinstance(y_train, np.ndarray)


def test_prepare_data_randomness():
    """Vérifie que deux appels ne donnent pas exactement le même split (pas de random_state fixé)"""
    X_train1, _, _, _ = prepare_data()
    X_train2, _, _, _ = prepare_data()

    # Il est statistiquement quasi-impossible d'avoir exactement le même split
    # si le hasard fait son travail.
    assert not np.array_equal(X_train1, X_train2)
