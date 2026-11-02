# Ejecuta todo el flujo del Ejercicio 01 (LAB00 + LAB01 + LAB02) en Windows / PowerShell.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$env:PYTHONPATH = "src"
if (-not $env:REPO_URL) { $env:REPO_URL = "https://github.com/edvvdev/unidad01-01" }

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Error "No existe el entorno .venv. Créalo con:`n  python -m venv .venv`n  .venv\Scripts\Activate.ps1`n  python -m pip install -r requirements.txt -r requirements-dev.txt"
}

Write-Host "==> 1/5. Dataset (se descarga una vez; el notebook también lo hace solo)" -ForegroundColor Cyan
python -c "from inf8239_u01.data import download_dataset; print('adult:', download_dataset('adult', 'data/raw')); print('bank (candidato alterno):', download_dataset('bank', 'data/raw'))"

Write-Host "==> 2/5. Pruebas (esperado: 15 passed)" -ForegroundColor Cyan
python -m pytest -q

Write-Host "==> 3/5. Notebooks" -ForegroundColor Cyan
foreach ($nb in @("00_verificacion.ipynb", "01_svm_guiada.ipynb", "02_dataset_svm.ipynb")) {
    python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 "notebooks\$nb"
}

Write-Host "==> 4/5. PDF breve de entrega" -ForegroundColor Cyan
python scripts\build_ejercicio01_pdf.py

Write-Host "==> 5/5. Resumen de cifras generadas" -ForegroundColor Cyan
python -c @"
import json
from pathlib import Path
reports = Path('reports')
svm = json.loads((reports / 'svm_metrics.json').read_text())
adult = json.loads((reports / 'dataset_svm_metrics.json').read_text())
print(f'LAB01  accuracy={svm["accuracy"]:.4f}  f1_macro={svm["f1_macro"]:.4f}  recall_maligno={svm["recall_maligno"]:.4f}')
print(f'LAB02  accuracy={adult["accuracy"]:.4f}  f1_macro={adult["f1_macro"]:.4f}  recall_mas_50k={adult["recall_mas_50k"]:.4f}')
print('Revisa que estas cifras coincidan con README, ficha, conclusión y PDF.')
"@

Write-Host "Listo. Revisa 'git status' y publica." -ForegroundColor Green
