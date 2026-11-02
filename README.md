# INF-8239 · Unidad 01 · Ejercicio 01 (LAB01 + LAB02)

Curso: Ciencia de Datos II (INF-8239) · Profesor: Edwin Ramón José Nolasco
Repositorio de esta entrega: https://github.com/edvvdev/unidad01-01

Proyecto de los laboratorios guiados 00–03 de la Unidad 01. Este README documenta el **Ejercicio 01**
(entrega que integra LAB01 y LAB02). Los laboratorios 01 y 02 se resuelven en este mismo proyecto,
porque LAB03 reutiliza el dataset, el target y las exclusiones del LAB02.

## Instalación (Windows, PowerShell)

```powershell
cd C:\Proyectos\INF8239_U01
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
$env:PYTHONPATH="src"
python -m pytest -q
```

Resultado esperado: `15 passed`. Para ejecutar los notebooks se necesita además el kernel de Jupyter:

```powershell
python -m pip install -r requirements-dev.txt
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_svm_guiada.ipynb
python -m jupyter nbconvert --to notebook --execute --inplace notebooks/02_dataset_svm.ipynb
```

El PDF breve de la entrega se regenera con `python scripts/build_ejercicio01_pdf.py` (requiere
`reportlab`, incluido en `requirements-dev.txt`).

## Descarga reproducible de los datos

Ninguno de los dos datasets requiere cuenta ni ruta personal: la descarga la hace un script que
valida la URL y registra el SHA-256 de los bytes obtenidos.

```python
from inf8239_u01.data import download_dataset
download_dataset("adult", "data/raw")   # UCI Adult (Census Income)
download_dataset("bank", "data/raw")    # UCI Bank Marketing (candidato alterno)
```

| Dataset | URL | Ficha | Licencia | SHA-256 |
|---|---|---|---|---|
| Adult | `https://archive.ics.uci.edu/static/public/2/adult.zip` | https://archive.ics.uci.edu/dataset/2/adult | CC BY 4.0 | `7537312dd56c2b98035880805ce99e68183a30ee468aa5329d6df0fbb3cc21bb` |
| Bank Marketing | `https://archive.ics.uci.edu/static/public/222/bank+marketing.zip` | https://archive.ics.uci.edu/dataset/222/bank-marketing | CC BY 4.0 | ver `data/raw/bank.csv.sha256` |

LAB01 usa `load_breast_cancer()` de scikit-learn (569 muestras, 30 variables, 2 clases), que no
requiere descarga.

## Estructura

```
INF8239_U01/
├── data/raw/                 datos descargados (no versionados) + .sha256 + .source.txt
├── docs/
│   ├── ficha_dataset.md      ficha comparativa de los dos candidatos + diccionario de datos
│   ├── CONCLUSION_EJERCICIO_01.md
│   └── plantilla_informe.md  (opcional) plantilla del informe en Markdown
├── notebooks/
│   ├── 00_verificacion.ipynb LAB00 · verificación del entorno
│   ├── 01_svm_guiada.ipynb   LAB01 · SVM con pipeline, GridSearchCV y evaluación
│   └── 02_dataset_svm.ipynb  LAB02 · dataset público, auditoría y pipeline completo
├── reports/                  métricas, tablas y figuras generadas
├── src/inf8239_u01/
│   ├── data.py               carga, auditoría y descarga reproducible
│   ├── models.py             build_svm, build_baseline, ColumnTransformer, build_svm_pipeline
│   └── evaluation.py         partición, métricas, matrices de confusión y figuras
├── tests/                    test_environment.py · test_models.py · test_data_contract.py
├── requirements.txt
└── AI_USE_DECLARATION.md
```

## Target y métrica

| Laboratorio | Dataset | Target (binario) | Métrica principal | Costo del error |
|---|---|---|---|---|
| LAB01 | Breast Cancer Wisconsin (diagnóstico) | `target`: 0 maligno · 1 benigno | F1 macro (media de las clases) | Falso negativo: maligno clasificado como benigno |
| LAB02 | UCI Adult (Census Income) | `income`: `<=50K` / `>50K` | F1 macro | Falso negativo: califica y no se detecta (posible denegación de crédito) |

## Ejecución

```bash
# LAB01
uv run python scripts/...   # o abrir notebooks/01_svm_guiada.ipynb y ejecutar todas las celdas
python -m pytest tests/test_models.py -q

# LAB02
python -m pytest tests/test_data_contract.py -q
```

Comandos equivalents para los notebooks: `python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_svm_guiada.ipynb` y el mismo para `02_dataset_svm.ipynb`.

## Resultados de referencia (2026-11-02)

**LAB01** (`reports/svm_metrics.json`, `reports/svm_cv_results.csv`):

| Modelo | Accuracy | F1 macro | Recall maligno |
|---|---|---|---|
| DummyClassifier (baseline) | 0,6316 | 0,3871 | 0,0000 |
| SVC rbf (C=10, gamma=0.01) | **0,9825** | **0,9812** | 0,9762 |

Matriz de confusión (prueba, 114 casos): 41 malignos correctos, 1 falso negativo, 1 falso positivo,
71 benignos correctos. F1 macro de validación (5 folds, semilla 42): 0,9739.

**LAB02** (`reports/dataset_svm_metrics.json`):

| Modelo | Accuracy | F1 macro | Recall `>50K` |
|---|---|---|---|
| DummyClassifier (mismo preprocesamiento) | 0,7607 | 0,4320 | 0,0000 |
| SVC rbf con pipeline (C=10, gamma=0.1) | **0,8588** | **0,7928** | 0,6146 |

Prueba: 9.769 casos; 901 falsos negativos y 478 falsos positivos. La búsqueda de hiperparámetros se
hizo sobre una submuestra estratificada del 25 % del entrenamiento (un ajuste completo del SVM sobre
39.073 filas tarda ~30 s) y el mejor modelo se reajustó sobre todo el entrenamiento.

## Documentos de la entrega

| Documento | Contenido |
|---|---|
| `docs/ficha_dataset.md` | Ficha comparativa de los dos datasets, criterios de aceptación, diccionario, sesgos y usos prohibidos |
| `docs/CONCLUSION_EJERCICIO_01.md` | Conclusión de 350 palabras que integra LAB01 y LAB02 |
| `reports/svm_cv_results.csv` · `reports/dataset_svm_cv_results.csv` | Tablas de la búsqueda de hiperparámetros |
| `reports/*_confusion_matrix.png` · `reports/*_cv_results.png` | Figuras |
| `reports/dataset_svm_errors.csv` | 20 errores con categoría, muestra aleatoria con semilla 42 |
| `AI_USE_DECLARATION.md` | Uso honesto del asistente de IA y verificaciones pendientes del estudiante |

## Estado y limitaciones

- **Pendiente:** la aprobación del docente sobre el dataset del LAB02. El manual de la Unidad 01
  prohíbe continuar con el entrenamiento final sin ella; el entrenamiento de este repositorio se
  ejecutó con esa aprobación aún pendiente y así queda registrado en
  `reports/dataset_svm_metrics.json` (`aprobacion_docente: pendiente`).
- Los resultados de LAB02 corresponden a un censo de 1994–1996 de la población activa estadounidense:
  no son extrapolables y no autorizan decisiones sobre personas.
