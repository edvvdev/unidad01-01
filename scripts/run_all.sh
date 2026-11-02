#!/usr/bin/env bash
# Ejecuta todo el flujo del Ejercicio 01 (LAB00 + LAB01 + LAB02) en Linux/macOS.
#
# Usa uv si está disponible; si no, recurre al entorno virtual con venv + requirements.txt
# (el procedimiento que describe el manual de la Unidad 01).
#
#   ./scripts/run_all.sh   # todo el Ejercicio 01 (LAB00 + LAB01 + LAB02)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v uv >/dev/null 2>&1; then
  echo "==> Entorno: uv (uv sync)"
  uv sync
  RUN=(uv run)
  export REPO_URL="${REPO_URL:-https://github.com/edvvdev/unidad01-01}"
else
  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then
    echo "No hay uv ni entorno .venv. Elige una de estas dos opciones:" >&2
    echo "  a) uv sync                      (recomendado)" >&2
    echo "  b) python3 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt" >&2
    exit 1
  fi
  echo "==> Entorno: .venv (venv + requirements.txt)"
  export PYTHONPATH="src"
  RUN=("$PY")
  export REPO_URL="${REPO_URL:-https://github.com/edvvdev/unidad01-01}"
fi

echo "==> 1/5. Dataset (se descarga una vez; el notebook también lo hace solo)"
"${RUN[@]}" - <<'CODE'
from inf8239_u01.data import download_dataset
print("adult:", download_dataset("adult", "data/raw"))
print("bank (candidato alterno):", download_dataset("bank", "data/raw"))
CODE

echo "==> 2/5. Pruebas (esperado: 15 passed)"
"${RUN[@]}" -m pytest -q

echo "==> 3/5. Notebooks"
"${RUN[@]}" -m jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=3600 notebooks/00_verificacion.ipynb
"${RUN[@]}" -m jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=3600 notebooks/01_svm_guiada.ipynb
"${RUN[@]}" -m jupyter nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.timeout=3600 notebooks/02_dataset_svm.ipynb

echo "==> 4/5. PDF breve de entrega"
"${RUN[@]}" python scripts/build_ejercicio01_pdf.py

echo "==> 5/5. Resumen de cifras generadas"
"${RUN[@]}" - <<'CODE'
import json
from pathlib import Path

reports = Path("reports")
svm = json.loads((reports / "svm_metrics.json").read_text())
adult = json.loads((reports / "dataset_svm_metrics.json").read_text())
print(f"LAB01  accuracy={svm['accuracy']:.4f}  f1_macro={svm['f1_macro']:.4f}  recall_maligno={svm['recall_maligno']:.4f}")
print(f"LAB02  accuracy={adult['accuracy']:.4f}  f1_macro={adult['f1_macro']:.4f}  recall_mas_50k={adult['recall_mas_50k']:.4f}")
print("Revisa que estas cifras coincidan con README, ficha, conclusión y PDF.")
CODE

echo "Listo. Revisa 'git status' y publica cuando hayas completado los campos PENDIENTE de los PDF."
