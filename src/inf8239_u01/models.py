"""Modelos reutilizables del laboratorio (LAB01 y LAB02)."""

from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC

#: Semilla fija de todos los modelos (manual de la Unidad 01, LAB01 §7).
RANDOM_STATE = 42


def build_svm(
    C: float = 1.0,
    gamma: str | float = "scale",
    probability: bool = True,
    random_state: int = RANDOM_STATE,
) -> Pipeline:
    """Pipeline de SVM con estandarización dentro (evita fuga de información).

    `probability=True` habilita `predict_proba`, que es lo que necesita el manual
    (LAB01 §8) para calcular el ROC-AUC de la clase positiva. No cambia las
    predicciones: la calibración de Platt se ajusta aparte de la función de decisión.

    Nota: scikit-learn 1.9 marca `probability` como obsoleto (se elimina en 1.11) en
    favor de `CalibratedClassifierCV(SVC(), ensemble=False)`; el proyecto fija
    `scikit-learn<1.11` para que el código del manual siga funcionando.

    Raises:
        ValueError: si C no es un valor positivo.
    """
    if C is None or float(C) <= 0:
        raise ValueError("C debe ser un valor mayor que cero")
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                SVC(
                    C=float(C),
                    gamma=gamma,
                    kernel="rbf",
                    probability=probability,
                    random_state=random_state,
                ),
            ),
        ]
    )


def build_baseline() -> DummyClassifier:
    """Baseline mínimo: predecir siempre la clase mayoritaria."""
    return DummyClassifier(strategy="most_frequent")


def identify_column_types(frame: pd.DataFrame, target_column: str | None = None) -> tuple[list[str], list[str]]:
    """Separa variables numéricas y categóricas; el target nunca entra como variable de entrada."""
    features = frame.drop(columns=[target_column]) if target_column and target_column in frame.columns else frame
    numeric = [column for column in features.columns if pd.api.types.is_numeric_dtype(features[column])]
    categorical = [column for column in features.columns if column not in numeric]
    return numeric, categorical


def build_preprocessor(frame: pd.DataFrame, target_column: str | None = None) -> ColumnTransformer:
    """ColumnTransformer: imputación + escala para numéricas, imputación + one-hot para categóricas."""
    numeric, categorical = identify_column_types(frame, target_column)
    transformers = []
    if numeric:
        transformers.append(
            ("numeric", Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]), numeric)
        )
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="most_frequent")), ("encoder", OneHotEncoder(handle_unknown="ignore"))]),
                categorical,
            )
        )
    return ColumnTransformer(transformers=transformers)


def build_svm_pipeline(
    frame: pd.DataFrame,
    target_column: str | None = None,
    C: float = 1.0,
    gamma: str | float = "scale",
    probability: bool = False,
    random_state: int = RANDOM_STATE,
) -> Pipeline:
    """Pipeline completo con ColumnTransformer y SVM (LAB02).

    `frame` debe ser el conjunto de variables de entrada (sin el target). Si se indica
    `target_column` y esa columna está en `frame`, se excluye de las variables de entrada.

    `probability=True` habilita `predict_proba` (ROC-AUC de la clase positiva). Se deja
    apagado por defecto porque la búsqueda de hiperparámetros no lo necesita y la
    calibración multiplica el coste de cada ajuste.
    """
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(frame, target_column)),
            (
                "model",
                SVC(
                    C=float(C),
                    gamma=gamma,
                    kernel="rbf",
                    cache_size=2000,
                    probability=probability,
                    random_state=random_state,
                ),
            ),
        ]
    )
