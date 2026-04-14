# On importe le module à tester
import services.def_model as def_model
from sklearn.ensemble import RandomForestClassifier


def test_model_initialization():
    """Vérifie que le modèle est bien un RandomForest avec les bons hyperparamètres"""
    # Vérifie le type d'objet
    assert isinstance(def_model.model, RandomForestClassifier)

    # Vérifie que les paramètres exportés correspondent à ceux du modèle
    assert def_model.params["n_estimators"] == 100
    assert def_model.params["random_state"] == 42
    assert def_model.model.n_estimators == 100
    assert def_model.model.random_state == 42


def test_params_structure():
    """Vérifie que le dictionnaire de paramètres contient les clés attendues"""
    expected_keys = {"n_estimators", "max_depth", "random_state", "criterion"}
    assert expected_keys.issubset(def_model.params.keys())
    assert def_model.params["criterion"] == "gini"


def test_model_is_ready():
    """Vérifie que le modèle n'est pas encore entraîné (pas d'attributs de fit)"""
    # Un modèle sklearn non entraîné n'a pas d'attributs finissant par '_'
    assert not hasattr(def_model.model, "estimators_")
