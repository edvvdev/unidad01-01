# Ejecuta todo el flujo del Ejercicio 01 (LAB00 + LAB01 + LAB02) en Windows / PowerShell.
#
# Usa uv si está disponible; si no, recurre al entorno virtual con venv + requirements.txt
# (el procedimiento que describe el manual de la Unidad 01).
#
#   .\scripts\run_all.ps1   # todo el Ejercicio 01 (LAB00 + LAB01 + LAB02)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    Write-Host "==> Entorno: uv (uv sync)" -ForegroundColor Cyan
    uv sync
    $Run = @("uv", "run")
    if (-not $env:REPO_URL) { $env:REPO_URL = "https://github.com/edvvdev/unidad01-01" }
} else {
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        Write-Error "No hay uv ni entorno .venv. Elige una de estas dos opciones:`n  a) uv sync`n  b) python -m venv .venv; .venv\Scripts\Activate.ps1; python -m pip install -r requirements.txt -r requirements-dev.txt"
    }
    Write-Host "==> Entorno: .venv (venv + requirements.txt)" -ForegroundColor Cyan
    $env:PYTHONPATH = "src"
    $Run = @("python")
    if (-not $env:REPO_URL) { $env:REPO_URL = "https://github.com/edvvdev/unidad01-01" }
}

Write-Host "==> 1/5. Dataset (se descarga una vez; el notebook también lo hace solo)" -ForegroundColor Cyan
& $Run[0] $Run[1..($Run.Length - 1)] -c "from inf8239_u01.data import download_dataset; print('adult:', download_dataset('adult', 'data/raw')); print('bank (candidato alterno):', download_dataset('bank', 'data/raw'))"

Write-Host "==> 2/5. Pruebas (esperado: 15 passed)" -ForegroundColor Cyan
& $Run[0] $Run[1..($Run.Length - 1)] -m pytest -q

Write-Host "==> 3/5. Notebooks" -ForegroundColor Cyan
foreach ($nb in @("00_verificacion.ipynb", "01_svm_guiada.ipynb", "02_dataset_svm.ipynb")) {
    & $Run[0] $Run[1..($Run.Length - 1)] -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 "notebooks\$nb"
}

Write-Host "==> 4/5. PDF breve de entrega" -ForegroundColor Cyan
& $Run[0] $Run[1..($Run.Length - 1)] scripts\build_ejercicio01_pdf.py

Write-Host "==> 5/5. Resumen de cifras generadas" -ForegroundColor Cyan
& $Run[0] $Run[1..($Run.Length - 1)] -c @"
import json
from pathlib import Path
reports = Path('reports')
svm = json.loads((reports / 'svm_metrics.json').read_text())
adult = json.loads((reports / 'dataset_svm_metrics.json').read_text())
print(f'LAB01  accuracy={svm["accuracy"]:.4f}  f1_macro={svm["f1_macro"]:.4f}  recall_maligno={svm["recall_maligno"]:.4f}')
print(f'LAB02  accuracy={adult["accuracy"]:.4f}  f1_macro={adult["f1_macro"]:.4f}  recall_mas_50k={adult["recall_mas_50k"]:.4f}')
print('Revisa que estas cifras coincidan con README, cards, conclusiones y PDF.')
"@

Write-Host "Listo. Revisa 'git status' y publica cuando hayas completado los campos PENDIENTE de los PDF." -ForegroundColor Green
