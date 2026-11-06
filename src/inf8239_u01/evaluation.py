"""Evaluación reproducible: partición, métricas y figuras (LAB01 y LAB02)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
TEST_SIZE = 0.20
CV_FOLDS = 5


def stratified_split(features, target, test_size: float = TEST_SIZE, random_state: int = RANDOM_STATE):
    """Partición estratificada 80/20 con semilla fija.

    Se llama **antes** de cualquier ajuste de escala o imputación: la transformación
    se aprende dentro del pipeline, nunca sobre el conjunto completo.
    """
    return train_test_split(
        features,
        target,
        test_size=test_size,
        stratify=target,
        random_state=random_state,
    )


def cv_table(cv_results: dict) -> pd.DataFrame:
    """Tabla legible de GridSearchCV: parámetros, media, desviación y tiempo de ajuste."""
    rows = []
    for index, params in enumerate(cv_results["params"]):
        rows.append(
            {
                "C": params.get("model__C"),
                "gamma": params.get("model__gamma"),
                "f1_macro_mean": cv_results["mean_test_score"][index],
                "f1_macro_std": cv_results["std_test_score"][index],
                "fit_time_mean_s": cv_results["mean_fit_time"][index],
                "fit_time_std_s": cv_results["std_fit_time"][index],
                "rank_test_score": cv_results["rank_test_score"][index],
            }
        )
    table = pd.DataFrame(rows).sort_values(["rank_test_score", "fit_time_mean_s"]).reset_index(drop=True)
    return table


def _describe_errors(subset: pd.DataFrame) -> dict:
    """Describe un conjunto de errores: tamaño y desglose de las variables relevantes."""
    description = {
        "n": int(len(subset)),
        "education": {str(key): int(value) for key, value in subset["education"].value_counts().items()},
        "capital_gain_cero": int((subset["capital_gain"] == 0).sum()),
        "capital_gain_positivo": int((subset["capital_gain"] > 0).sum()),
        "capital_gain_positivo_filas": [
            {
                "age": int(row["age"]),
                "education": str(row["education"]),
                "capital_gain": int(row["capital_gain"]),
            }
            for _, row in subset[subset["capital_gain"] > 0].iterrows()
        ],
        "edad_media": float(subset["age"].mean()) if len(subset) else 0.0,
        "edad_mediana": float(subset["age"].median()) if len(subset) else 0.0,
        "horas_media": float(subset["hours_per_week"].mean()) if len(subset) else 0.0,
        "horas_mediana": float(subset["hours_per_week"].median()) if len(subset) else 0.0,
    }
    return description


def error_profile(
    errors: pd.DataFrame,
    real_column: str = "real",
    pred_column: str = "predicho",
    positive_label: str = ">50K",
    negative_label: str = "<=50K",
) -> dict:
    """Perfil real de los errores: falso negativo y falso positivo, con su desglose.

    Se calcula **desde los datos** (nunca a mano): número de casos de cada tipo de
    error, nivel educativo, presencia de `capital_gain`, edad y jornada.
    """
    falsos_negativos = errors[(errors[real_column] == positive_label) & (errors[pred_column] == negative_label)]
    falsos_positivos = errors[(errors[real_column] == negative_label) & (errors[pred_column] == positive_label)]
    return {
        "n_falso_negativo": int(len(falsos_negativos)),
        "n_falso_positivo": int(len(falsos_positivos)),
        "falso_negativo": _describe_errors(falsos_negativos),
        "falso_positivo": _describe_errors(falsos_positivos),
    }


def report_frame(y_true, y_pred, target_names: list[str] | None = None) -> pd.DataFrame:
    """Reporte por clase en DataFrame (soporta sklearn >= 1.4 con target_names)."""
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    if target_names is not None:
        report = {target_names[int(key)] if key.isdigit() else key: value for key, value in report.items()}
    rows = []
    for label, values in report.items():
        if not isinstance(values, dict):
            continue
        rows.append(
            {
                "clase": label,
                "precision": values.get("precision"),
                "recall": values.get("recall"),
                "f1_score": values.get("f1-score"),
                "support": values.get("support"),
            }
        )
    return pd.DataFrame(rows)


def confusion_matrix_frame(y_true, y_pred, labels: list[int], target_names: list[str]) -> pd.DataFrame:
    """Matriz de confusión con nombres de clase legibles."""
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    frame = pd.DataFrame(matrix, index=[f"real_{name}" for name in target_names], columns=[f"pred_{name}" for name in target_names])
    return frame


def plot_confusion(y_true, y_pred, labels: list[int], target_names: list[str], path: str | Path, title: str) -> Path:
    """Guarda la matriz de confusión como figura legible."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    figure, axis = plt.subplots(figsize=(7.2, 5.4))
    image = axis.imshow(matrix, cmap="Blues")
    figure.colorbar(image, ax=axis)
    axis.set_xticks(range(len(target_names)), target_names)
    axis.set_yticks(range(len(target_names)), target_names)
    axis.set_xlabel("Predicho")
    axis.set_ylabel("Real")
    axis.set_title(title, fontsize=11, wrap=True)
    threshold = matrix.max() / 2
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            axis.text(column, row, str(matrix[row, column]), ha="center", va="center",
                      color="white" if matrix[row, column] > threshold else "#0f172a")
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path


def plot_cv_results(table: pd.DataFrame, path: str | Path, title: str) -> Path:
    """Guarda el gráfico de F1 macro por configuración de la búsqueda."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [f"C={row.C}\ngamma={row.gamma}" for row in table.itertuples()]
    figure, axis = plt.subplots(figsize=(9, 4.8))
    positions = np.arange(len(table))
    axis.bar(positions, table["f1_macro_mean"], yerr=table["f1_macro_std"], capsize=4, color="#0f7c7b")
    axis.set_xticks(positions, labels, fontsize=8)
    axis.set_ylabel("F1 macro (media de validación)")
    axis.set_xlabel("Configuración SVM (C, gamma)")
    axis.set_title(title, fontsize=11, wrap=True)
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(path, dpi=160)
    plt.close(figure)
    return path
