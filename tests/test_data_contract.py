"""Contrato de datos del LAB02: la descarga y el dataset deben cumplir reglas explícitas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from inf8239_u01.data import (
    DATASET_SPECS,
    audit_dataframe,
    download_dataset,
    load_dataset,
    validate_url,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"


# --------------------------------------------------------------------------------------
# Reglas de descarga (no requieren red)
# --------------------------------------------------------------------------------------

def test_validate_url_rejects_non_http_urls():
    with pytest.raises(ValueError):
        validate_url("ftp://example.com/dataset.csv")
    with pytest.raises(ValueError):
        validate_url("C:\\Users\\Nombre\\dataset.csv")
    with pytest.raises(ValueError):
        validate_url("datos/dataset.csv")


def test_download_dataset_rejects_unknown_name():
    with pytest.raises(ValueError):
        download_dataset("dataset_que_no_existe")


def test_load_dataset_requires_the_file():
    with pytest.raises(FileNotFoundError):
        load_dataset("adult", DATA_RAW / "no_existe.csv")


def test_every_candidate_declares_the_required_metadata():
    for name, spec in DATASET_SPECS.items():
        assert spec["url"].startswith("https://")
        assert spec["ficha"].startswith("https://")
        assert "CC BY" in spec["licencia"]
        assert spec["doi"].startswith("10.")
        assert spec["target"] and spec["target_positive"]
        assert spec["exclude"], f"{name} debe justificar sus exclusiones"
        assert spec["motivo_exclusion"]


# --------------------------------------------------------------------------------------
# Contrato sobre el dataset descargado (se omite si todavía no se descargó)
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(DATASET_SPECS))
def test_dataset_contract(name):
    path = DATA_RAW / f"{name}.csv"
    if not path.exists():
        pytest.skip(f"Falta descargar el dataset: download_dataset('{name}')")
    spec = DATASET_SPECS[name]
    frame = load_dataset(name, path)

    # 1. Criterio de aceptación: al menos 500 filas y target observable con dos clases
    assert len(frame) >= 500
    assert frame[spec["target"]].nunique() == 2

    # 2. Las columnas excluidas por decisión semántica no se usan como variables de entrada
    usable = frame.drop(columns=spec["exclude"] + [spec["target"]])
    assert usable.shape[1] >= 5

    # 3. Todas las variables de entrada están documentadas como numéricas o categóricas
    audit = audit_dataframe(frame, spec["target"])
    assert set(audit["dtypes"].values()) <= {"int64", "float64", "str", "object", "bool"}

    # 4. No se puede filtrar información del conjunto de prueba: el target no está en X
    assert spec["target"] not in usable.columns

    # 5. La distribución del target queda registrada y no está degenerada
    proportions = audit["target_distribution"]
    assert min(proportions.values()) > 0.0
    assert max(proportions.values()) < 1.0


@pytest.mark.parametrize("name", sorted(DATASET_SPECS))
def test_duplicated_rows_match_the_published_audit(name):
    """El número de duplicados que declara `reports/audit_summary.json` debe ser real."""
    path = DATA_RAW / f"{name}.csv"
    if not path.exists():
        pytest.skip(f"Falta descargar el dataset: download_dataset('{name}')")
    summary_path = REPORTS / "audit_summary.json"
    if not summary_path.exists():
        pytest.skip("Falta reports/audit_summary.json (ejecuta scripts/audit_datasets.py)")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert name in summary["datasets"], f"la auditoría publicada no cubre {name}"
    declarado = summary["datasets"][name]["duplicate_rows"]
    frame = load_dataset(name, path)
    detectado = int(frame.duplicated().sum())
    assert declarado == detectado, (
        f"la auditoría declara {declarado} filas duplicadas y el CSV tiene {detectado}"
    )
    assert 0 <= declarado <= len(frame)


@pytest.mark.parametrize("name", sorted(DATASET_SPECS))
def test_deduplicated_frame_has_no_repeated_rows(name):
    """Tras deduplicar no queda ninguna fila repetida y se pierden solo las duplicadas."""
    path = DATA_RAW / f"{name}.csv"
    if not path.exists():
        pytest.skip(f"Falta descargar el dataset: download_dataset('{name}')")
    frame = load_dataset(name, path)
    duplicated = int(frame.duplicated().sum())
    limpio = frame.drop_duplicates()
    assert int(limpio.duplicated().sum()) == 0, "quedan filas repetidas tras deduplicar"
    assert len(limpio) == len(frame) - duplicated
    if duplicated:
        repetidas = frame[frame.duplicated(keep=False)]
        grupos = repetidas.groupby(list(frame.columns), dropna=False).size()
        assert (grupos >= 2).all(), "hay filas repetidas que no son idénticas entre sí"
        assert len(repetidas) - len(grupos) == duplicated
