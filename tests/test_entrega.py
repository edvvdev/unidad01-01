"""Verificación de los artefactos de la entrega (LAB01 + LAB02).

Comprueba que lo que el repositorio publica (sidecars SHA-256, perfil de los falsos
negativos, ROC-AUC, cifras de la documentación) es coherente con los datos y con `reports/`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import pytest

from inf8239_u01.data import DATASET_SPECS, sha256_file, write_sha256_sidecar

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
REPORTS = ROOT / "reports"
SIDECAR = re.compile(r"^(?P<hash>[0-9a-f]{64})  (?P<name>.+)$")


def _leer_json(nombre: str) -> dict:
    """Lee un JSON de `reports/` o salta la prueba si todavía no existe."""
    ruta = REPORTS / nombre
    if not ruta.exists():
        pytest.skip(f"Falta reports/{nombre} (ejecuta el flujo completo)")
    return json.loads(ruta.read_text(encoding="utf-8"))


def _numero(valor: float, decimales: int = 4) -> str:
    """Número con coma decimal, como se escribe en la documentación."""
    return f"{valor:.{decimales}f}".replace(".", ",")


def _plano(texto: str) -> str:
    """Texto en una sola línea: el Markdown parte las frases en varias líneas."""
    return " ".join(texto.split())


# --------------------------------------------------------------------------------------
# Descarga reproducible y sidecars SHA-256 (D3, D6)
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(DATASET_SPECS))
@pytest.mark.parametrize("suffix", [".csv", ".zip"])
def test_sha256_sidecar_matches_its_own_file(name, suffix):
    """Cada sidecar guarda el SHA-256 de **su** archivo y usa el formato de `sha256sum -c`."""
    target = DATA_RAW / f"{name}{suffix}"
    sidecar = DATA_RAW / f"{name}{suffix}.sha256"
    if not target.exists() or not sidecar.exists():
        pytest.skip(f"Falta descargar el dataset: download_dataset('{name}')")
    match = SIDECAR.match(sidecar.read_text(encoding="utf-8").strip())
    assert match, f"formato inválido en {sidecar.name}"
    assert match.group("hash") == sha256_file(target), "el sidecar no corresponde a su archivo"
    ruta = Path(match.group("name"))
    assert (ruta if ruta.is_absolute() else ROOT / ruta).exists(), "la ruta del sidecar no existe"


def test_write_sha256_sidecar_uses_the_sha256sum_format(tmp_path):
    """El sidecar que escribe el proyecto es verificable con `sha256sum -c`."""
    archivo = tmp_path / "datos.csv"
    archivo.write_text("a,b\n1,2\n", encoding="utf-8")
    sidecar = write_sha256_sidecar(archivo)
    partes = sidecar.read_text(encoding="utf-8").split()
    assert partes[0] == sha256_file(archivo)
    assert Path(partes[1]).name == "datos.csv"
    assert Path(partes[1]).is_absolute()


def test_data_module_does_not_import_undeclared_packages():
    """`uv sync --frozen` debe bastar: la descarga usa la biblioteca estándar."""
    fuente = (ROOT / "src/inf8239_u01/data.py").read_text(encoding="utf-8")
    assert "import requests" not in fuente
    assert "from urllib.request import" in fuente


# --------------------------------------------------------------------------------------
# Auditoría publicada (D5, D9)
# --------------------------------------------------------------------------------------

def test_published_audit_matches_the_downloaded_csvs():
    """`reports/audit_summary.json` debe describir los CSV descargados."""
    summary = _leer_json("audit_summary.json")
    for name in sorted(DATASET_SPECS):
        path = DATA_RAW / f"{name}.csv"
        if not path.exists():
            pytest.skip(f"Falta descargar el dataset: download_dataset('{name}')")
        frame = pd.read_csv(path)
        declarado = summary["datasets"][name]
        assert declarado["filas"] == len(frame)
        assert declarado["columnas"] == frame.shape[1]
        assert declarado["n_numericas"] == sum(
            1 for dtype in frame.dtypes if str(dtype).startswith(("int", "float"))
        )
        assert declarado["duplicate_rows"] == int(frame.duplicated().sum())


def test_ficha_declares_the_real_number_of_column_types():
    """La ficha debe contar los tipos como los calcula `dtypes`."""
    summary = _leer_json("audit_summary.json")
    ficha = (ROOT / "docs/ficha_dataset.md").read_text(encoding="utf-8")
    adult = summary["datasets"]["adult"]
    declarado = f"{adult['n_numericas']} numéricas + {adult['n_categoricas']} categóricas + target"
    assert declarado in ficha, f"la ficha no dice: {declarado}"
    assert "10.24432/C5XW20" in ficha, "la ficha no cita el DOI canónico del dataset"


def test_ficha_declares_the_approval_status_explicitly():
    """Sin marcadores sin resolver: el estado de aprobación queda explícito."""
    ficha = (ROOT / "docs/ficha_dataset.md").read_text(encoding="utf-8")
    assert "____" not in ficha, "quedan marcadores sin resolver en la ficha"
    assert "Estado de aprobación: pendiente" in ficha


# --------------------------------------------------------------------------------------
# Perfil real de los falsos negativos (D4)
# --------------------------------------------------------------------------------------

def test_error_profile_matches_the_published_errors():
    """El perfil de los falsos negativos debe derivar de `reports/dataset_svm_errors.csv`."""
    errores = REPORTS / "dataset_svm_errors.csv"
    if not errores.exists():
        pytest.skip("Faltan los artefactos del LAB02 (ejecuta el notebook 02)")
    perfil = _leer_json("dataset_svm_errors_profile.json")
    muestra = pd.read_csv(errores)
    falsos_negativos = muestra[(muestra["real"] == ">50K") & (muestra["predicho"] == "<=50K")]
    falsos_positivos = muestra[(muestra["real"] == "<=50K") & (muestra["predicho"] == ">50K")]
    assert perfil["muestra"]["n_falso_negativo"] == len(falsos_negativos)
    assert perfil["muestra"]["n_falso_positivo"] == len(falsos_positivos)
    assert perfil["muestra"]["falso_negativo"]["education"] == {
        str(key): int(value) for key, value in falsos_negativos["education"].value_counts().items()
    }
    assert perfil["muestra"]["falso_negativo"]["capital_gain_cero"] == int(
        (falsos_negativos["capital_gain"] == 0).sum()
    )
    assert perfil["muestra"]["falso_negativo"]["capital_gain_positivo"] == int(
        (falsos_negativos["capital_gain"] > 0).sum()
    )


def test_conclusion_cites_the_real_false_negative_profile():
    """La conclusión debe citar el perfil calculado, no una suposición."""
    perfil = _leer_json("dataset_svm_errors_profile.json")
    conclusion = _plano((ROOT / "docs/CONCLUSION_EJERCICIO_01.md").read_text(encoding="utf-8"))
    fn = perfil["muestra"]["falso_negativo"]
    assert f"{fn['education'].get('Bachelors', 0)} tienen estudios superiores" in conclusion
    assert f"{fn['education'].get('HS-grad', 0)} tienen estudios secundarios" in conclusion
    assert f"{fn['capital_gain_cero']} de {fn['n']} tienen" in conclusion
    assert "son personas con estudios superiores" not in conclusion, "vuelve la afirmación anterior"


def test_conclusion_declares_its_own_word_count():
    """La extensión declarada en la conclusión debe ser la real."""
    texto = (ROOT / "docs/CONCLUSION_EJERCICIO_01.md").read_text(encoding="utf-8")
    cuerpo = texto.split("**Qué se construyó.**", 1)[1]
    cuerpo = "**Qué se construyó.**" + cuerpo.split("**Pendiente crítico:**", 1)[0]
    declaradas = int(re.search(r"Extensión: (\d+) palabras", texto).group(1))
    assert declaradas == len(cuerpo.split())


# --------------------------------------------------------------------------------------
# ROC-AUC (D10)
# --------------------------------------------------------------------------------------

def test_lab01_metrics_report_roc_auc():
    """El manual (LAB01 §8) pide ROC-AUC: debe estar en `reports/svm_metrics.json`."""
    metricas = _leer_json("svm_metrics.json")
    assert 0.5 <= metricas["roc_auc"] <= 1.0
    assert 0.5 <= metricas["roc_auc_maligno"] <= 1.0
    assert metricas["roc_auc_configuracion_base"] <= metricas["roc_auc"]


def test_lab02_metrics_report_roc_auc():
    """El LAB02 publica el ROC-AUC de la clase positiva (`>50K`)."""
    metricas = _leer_json("dataset_svm_metrics.json")
    assert 0.5 <= metricas["roc_auc_mas_50k"] <= 1.0
    assert metricas["aprobacion_docente"] == "pendiente"


def test_readme_cites_the_published_metrics():
    """Las cifras del README salen de `reports/`, no de una transcripción manual."""
    svm = _leer_json("svm_metrics.json")
    adult = _leer_json("dataset_svm_metrics.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for valor in (svm["accuracy"], svm["f1_macro"], svm["roc_auc"], adult["accuracy"],
                  adult["f1_macro"], adult["recall_mas_50k"], adult["roc_auc_mas_50k"]):
        assert _numero(valor) in readme, f"el README no cita {_numero(valor)}"


def test_pdf_builder_publishes_roc_auc_and_the_error_profile():
    """El PDF debe incluir el ROC-AUC, el perfil de errores y el estado de aprobación."""
    fuente = (ROOT / "scripts/build_ejercicio01_pdf.py").read_text(encoding="utf-8")
    assert "roc_auc" in fuente
    assert "dataset_svm_errors_profile.json" in fuente
    assert "aprobacion_docente" in fuente


# --------------------------------------------------------------------------------------
# Documentación y entorno (D1, D2, D5, D7, D8, D11, D12)
# --------------------------------------------------------------------------------------

def test_pdf_builder_uses_the_repository_url_without_placeholders():
    """El PDF debe salir con la URL del repositorio y sin marcadores pendientes."""
    fuente = (ROOT / "scripts/build_ejercicio01_pdf.py").read_text(encoding="utf-8")
    assert 'os.getenv("REPO_URL", "https://github.com/edvvdev/unidad01-01")' in fuente
    assert "PENDIENTE" not in fuente


def test_readme_has_no_placeholder_commands():
    """El README documenta comandos reales, no rutas con puntos suspensivos."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "scripts/..." not in readme
    assert "plantilla_informe.md" not in readme
    assert "https://github.com/edvvdev/unidad01-01" in readme


def test_readme_structure_matches_the_repository():
    """El árbol del README describe los archivos que existen."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for obligatorio in ("scripts/", "docs/EJERCICIO_01_PDF_BRIEF.pdf", "reports/", "tests/",
                        "scripts/build_ejercicio01_pdf.py", "scripts/run_all.sh"):
        assert obligatorio in readme, f"el árbol del README no menciona {obligatorio}"


def test_readme_and_ficha_cite_the_references():
    """El manual pide cerrar con referencias."""
    for documento in ("README.md", "docs/ficha_dataset.md"):
        texto = (ROOT / documento).read_text(encoding="utf-8")
        assert "10.24432/C5XW20" in texto
        assert "Pedregosa" in texto
        assert "Harper" in texto and "Konstan" in texto


def test_dev_group_declares_ruff_and_the_lock_is_coherent():
    """`uv run ruff check .` debe existir y `uv.lock` debe estar sincronizado."""
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "ruff" in pyproject
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    assert 'name = "ruff"' in lock


def test_runner_does_not_mention_removed_pdf_fields():
    """El runner avisa de campos PENDIENTE que ya no existen en el PDF."""
    for runner in ("scripts/run_all.sh", "scripts/run_all.ps1"):
        texto = (ROOT / runner).read_text(encoding="utf-8")
        assert "matrícula" not in texto
        assert "correo" not in texto.lower()


def test_readme_cites_the_published_checksums():
    """Los SHA-256 que cita el README son los de los archivos realmente descargados."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for nombre in ("adult.csv", "adult.zip", "bank.csv", "bank.zip"):
        sidecar = DATA_RAW / f"{nombre}.sha256"
        if not sidecar.exists():
            pytest.skip("Falta descargar el dataset")
        partes = sidecar.read_text(encoding="utf-8").split()
        assert partes[0] in readme, f"el README no cita el SHA-256 de {nombre}"
