import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import NotFittedError

from inf8239_u01.data import load_breast_cancer
from inf8239_u01.models import build_baseline, build_svm, build_svm_pipeline, identify_column_types


def test_svm_pipeline_predicts_one_label_per_row():
    features, target = load_breast_cancer()
    model = build_svm(C=1.0, gamma="scale")
    model.fit(features.iloc[:120], target.iloc[:120])
    predictions = model.predict(features.iloc[120:130])
    assert len(predictions) == 10
    assert set(predictions).issubset(set(target.unique()))


def test_build_svm_rejects_non_positive_c():
    with pytest.raises(ValueError):
        build_svm(C=0)
    with pytest.raises(ValueError):
        build_svm(C=-1.0)


def test_pipeline_contains_scaler_and_svc():
    model = build_svm()
    steps = [name for name, _ in model.steps]
    assert steps == ["scaler", "model"]
    assert model.named_steps["model"].kernel == "rbf"


def test_baseline_predicts_majority_class():
    features, target = load_breast_cancer()
    baseline = build_baseline()
    baseline.fit(features, target)
    predictions = baseline.predict(features)
    majority = target.value_counts().idxmax()
    assert set(predictions) == {majority}


def test_scaler_is_fitted_inside_pipeline():
    """El escalado se aprende en el pipeline: no se filtra información del test."""
    features, target = load_breast_cancer()
    model = build_svm()
    model.fit(features, target)
    assert hasattr(model.named_steps["scaler"], "mean_")


def test_lab02_pipeline_detects_column_types():
    frame = pd.DataFrame(
        {
            "edad": [23.0, 45.0, 31.0, np.nan],
            "ciudad": ["a", "b", "a", "b"],
            "target": [0, 1, 0, 1],
        }
    )
    numeric, categorical = identify_column_types(frame, "target")
    assert numeric == ["edad"]
    assert categorical == ["ciudad"]
    pipeline = build_svm_pipeline(frame, "target", C=1.0)
    assert [name for name, _ in pipeline.steps] == ["preprocessor", "model"]
    with pytest.raises(NotFittedError):
        pipeline.predict(frame.drop(columns=["target"]))
