#!/usr/bin/env bash
# Ejecuta todo el flujo del Ejercicio 01 (LAB00 + LAB01 + LAB02) en Linux/macOS.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY=".venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "No existe el entorno .venv. Créalo con:" >&2
  echo "  uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt" >&2
  exit 1
fi

export PYTHONPATH="src"
export REPO_URL="${REPO_URL:-https://github.com/edvvdev/unidad01-01}"

echo "==> 1/5. Dataset (se descarga una vez; el notebook también lo hace solo)"
$PY - <<'CODE'
from inf8239_u01.data import download_dataset
print("adult:", download_dataset("adult", "data/raw"))
print("bank (candidato alterno):", download_dataset("bank", "data/raw"))
CODE

echo "==> 2/5. Pruebas (esperado: 15 passed)"
$PY -m pytest -q

echo "==> 3/5. Notebooks"
for nb in 00_verificacion 01_svm_guiada 02_dataset_svm; do
  $PY -m jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=3600 "notebooks/${nb}.ipynb"
done

echo "==> 4/5. PDF breve de entrega"
$PY scripts/build_ejercicio01_pdf.py

echo "==> 5/5. Resumen de cifras generadas"
$PY - <<'CODE'
import json
from pathlib import Path
reports = Path("reports")
svm = json.loads((reports / "svm_metrics.json").read_text())
adult = json.loads((reports / "dataset_svm_metrics.json").read_text())
print(f"LAB01  accuracy={svm['accuracy']:.4f}  f1_macro={svm['f1_macro']:.4f}  recall_maligno={svm['recall_maligno']:.4f}")
print(f"LAB02  accuracy={adult['accuracy']:.4f}  f1_macro={adult['f1_macro']:.4f}  recall_mas_50k={adult['recall_mas_50k']:.4f}")
print("Revisa que estas cifras coincidan con README, ficha, conclusión y PDF.")
CODE

echo "Listo. Revisa 'git status' y publica."
