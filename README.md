# INF-8239 · Unidad 01 · Ejercicio 01 (LAB01 + LAB02)

Curso: Ciencia de Datos II (INF-8239) · Profesor: Edwin Ramón José Nolasco
Repositorio de esta entrega: https://github.com/edvvdev/unidad01-01

Proyecto de los laboratorios guiados 00–03 de la Unidad 01. Este README documenta el **Ejercicio 01**
(entrega que integra LAB01 y LAB02). Los laboratorios 01 y 02 se resuelven en este mismo proyecto,
porque LAB03 reutiliza el dataset, el target y las exclusiones del LAB02.

## Instalación

Dos caminos equivalentes: **uv** (recomendado, bloquea las versiones exactas en `uv.lock`) o el
procedimiento del manual con `venv` + `requirements.txt` (se conserva porque el mandato exige que
el repositorio incluya `requirements.txt`).

**Con uv**

```bash
git clone https://github.com/edvvdev/unidad01-01.git
cd unidad01-01
uv python install 3.12
uv sync --frozen          # instala exactamente lo que fija uv.lock
uv run pytest -q          # 40 passed
uv run ruff check .       # lint en verde
```

**Con venv + requirements.txt (el procedimiento del manual)**

```powershell
cd C:\Proyectos\INF8239_U01
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt      # jupyter, reportlab y ruff
$env:PYTHONPATH="src"
python -m pytest -q                                # 40 passed
```

En macOS/Linux: `python3 -m venv .venv` y `source .venv/bin/activate`.

El proyecto **no usa ningún paquete fuera de la biblioteca estándar sin declararlo**: la descarga
de datos se hace con `urllib.request` (biblioteca estándar), de modo que `uv sync --frozen` basta
para ejecutarlo todo.

### Dependencias declaradas

- `pyproject.toml` declara las dependencias de ejecución (numpy, pandas, scikit-learn, matplotlib,
  seaborn, joblib) y el grupo `dev` con las herramientas de desarrollo: **pytest**, **ruff**,
  jupyter, nbformat, ipykernel y reportlab.
- `uv.lock` fija las versiones exactas de todo lo anterior y se mantiene sincronizado con
  `pyproject.toml` (`uv lock` después de cualquier cambio; `uv lock --check` falla si diverge).
- El proyecto fija `scikit-learn<1.11` porque el manual de la Unidad 01 (LAB01 §8) construye el
  SVM con `probability=True`, opción que scikit-learn 1.9 marca como obsoleta y que se elimina
  en 1.11. El sustituto oficial es `CalibratedClassifierCV(SVC(), ensemble=False)`.
- No se usa `requests`: la descarga se hace con `urllib.request` de la biblioteca estándar, así que
  no hace falta declarar ningún paquete adicional.

## Ejecución

Un script hace todo el flujo: descarga el dataset, audita los CSV, corre las pruebas, ejecuta los
notebooks de principio a fin con sus salidas guardadas y regenera el PDF.

```powershell
.\scripts\run_all.ps1        # Windows
```
```bash
./scripts/run_all.sh         # macOS / Linux
```

Paso a paso (son los mismos comandos que usa `scripts/run_all.sh`):

```bash
# 1. Descarga reproducible de los dos datasets candidatos
uv run python -c "from inf8239_u01.data import download_dataset; download_dataset('adult', 'data/raw'); download_dataset('bank', 'data/raw')"

# 2. Auditoría publicada en reports/audit_summary.json
uv run python scripts/audit_datasets.py

# 3. Pruebas
uv run python -m pytest -q

# 4. Notebooks (se ejecutan de principio a fin y guardan sus salidas)
uv run python -m jupyter nbconvert --to notebook --execute --inplace notebooks/00_verificacion.ipynb
uv run python -m jupyter nbconvert --to notebook --execute --inplace notebooks/01_svm_guiada.ipynb
uv run python -m jupyter nbconvert --to notebook --execute --inplace notebooks/02_dataset_svm.ipynb

# 5. PDF breve de entrega (lee todas las cifras de reports/)
uv run python scripts/build_ejercicio01_pdf.py
```

El PDF usa por defecto la URL de esta entrega, `https://github.com/edvvdev/unidad01-01`. Para
publicarlo en otro repositorio (por ejemplo, un fork) se sobrescribe con la variable de entorno
`REPO_URL`:

```bash
REPO_URL=https://github.com/edvvdev/unidad01-01 uv run python scripts/build_ejercicio01_pdf.py
```

Tiempos orientativos en CPU: LAB01 ~1 min y LAB02 ~10 min (el SVM ajusta 39.073 filas y calibra
probabilidades). Las **métricas se reproducen exactamente**; los tiempos varían con el hardware.

## Descarga reproducible de los datos

Ninguno de los dos datasets requiere cuenta ni ruta personal: la descarga la hace un script que
valida la URL, guarda el ZIP original y registra el SHA-256 de **cada** archivo en un sidecar
`.sha256` con el formato de `sha256sum -c`.

```python
from inf8239_u01.data import download_dataset
download_dataset("adult", "data/raw")   # UCI Adult (Census Income)
download_dataset("bank", "data/raw")    # UCI Bank Marketing (candidato alterno)
```

| Dataset | URL | Ficha · DOI | Licencia | SHA-256 del CSV | SHA-256 del ZIP |
|---|---|---|---|---|---|
| Adult | `https://archive.ics.uci.edu/static/public/2/adult.zip` | https://archive.ics.uci.edu/dataset/2/adult · `10.24432/C5XW20` | CC BY 4.0 | `9479f8b76861e48c66836d97937f2c5a469581672e12c795d770b297817ae3a1` | `7537312dd56c2b98035880805ce99e68183a30ee468aa5329d6df0fbb3cc21bb` |
| Bank Marketing | `https://archive.ics.uci.edu/static/public/222/bank+marketing.zip` | https://archive.ics.uci.edu/dataset/222/bank-marketing · `10.24432/C5K306` | CC BY 4.0 | `658415da53b6bdf1b4c30b4dd30d6ca9844b8b45bda7a4f71628b0c514090925` | `e0bf5f5de5b846e2f18e9d90606637267d46dfa260e0f17bb12e605db5efbeb4` |

Los sidecars quedan en `data/raw/` (`adult.csv.sha256`, `adult.zip.sha256`, `bank.csv.sha256`,
`bank.zip.sha256`) y se verifican desde la raíz del proyecto:

```bash
sha256sum -c data/raw/*.sha256     # adult.csv: OK · adult.zip: OK · bank.csv: OK · bank.zip: OK
```

LAB01 usa `load_breast_cancer()` de scikit-learn (569 muestras, 30 variables, 2 clases), que no
requiere descarga.

## Estructura

```
unidad01-01/
├── data/raw/                 datos descargados (no versionados) + .sha256 + .source.txt
├── docs/
│   ├── ficha_dataset.md      ficha comparativa de los dos candidatos + diccionario de datos
│   ├── CONCLUSION_EJERCICIO_01.md
│   └── EJERCICIO_01_PDF_BRIEF.pdf   PDF breve de la entrega
├── notebooks/
│   ├── 00_verificacion.ipynb LAB00 · verificación del entorno
│   ├── 01_svm_guiada.ipynb   LAB01 · SVM con pipeline, GridSearchCV y evaluación
│   └── 02_dataset_svm.ipynb  LAB02 · dataset público, auditoría y pipeline completo
├── reports/                  métricas, tablas y figuras generadas
├── scripts/
│   ├── run_all.sh            flujo completo (Linux/macOS)
│   ├── run_all.ps1           flujo completo (Windows/PowerShell)
│   ├── audit_datasets.py     auditoría de los CSV → reports/audit_summary.json
│   └── build_ejercicio01_pdf.py   genera docs/EJERCICIO_01_PDF_BRIEF.pdf
├── src/inf8239_u01/
│   ├── data.py               carga, auditoría, descarga reproducible y sidecars SHA-256
│   ├── models.py             build_svm, build_baseline, ColumnTransformer, build_svm_pipeline
│   ├── evaluation.py         partición, métricas, ROC-AUC, perfiles de error y figuras
│   └── environment.py        comprobación del entorno
├── tests/                    test_environment.py · test_models.py · test_data_contract.py · test_entrega.py
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── uv.lock
└── AI_USE_DECLARATION.md
```

## Target y métrica

| Laboratorio | Dataset | Target (binario) | Métrica principal | Costo del error |
|---|---|---|---|---|
| LAB01 | Breast Cancer Wisconsin (diagnóstico) | `target`: 0 maligno · 1 benigno | F1 macro (media de las clases) | Falso negativo: maligno clasificado como benigno |
| LAB02 | UCI Adult (Census Income) | `income`: `<=50K` / `>50K` | F1 macro | Falso negativo: califica y no se detecta (posible denegación de crédito) |

El manual (LAB01 §8) pide además el **ROC-AUC de la clase positiva**: se reporta en los dos
laboratorios y se guarda en `reports/svm_metrics.json` (`roc_auc`) y
`reports/dataset_svm_metrics.json` (`roc_auc_mas_50k`). Aparece en el notebook 01 (sección
«ROC-AUC de la clase positiva»), en el notebook 02 (sección 7), en la tabla 2 del PDF y en el
resumen que imprime `scripts/run_all.sh`.

## Resultados de referencia (2026-11-05)

**LAB01** (`reports/svm_metrics.json`, `reports/svm_cv_results.csv`):

| Modelo | Accuracy | F1 macro | Recall maligno | ROC-AUC |
|---|---|---|---|---|
| DummyClassifier (baseline) | 0,6316 | 0,3871 | 0,0000 | 0,5000 |
| SVC rbf (C=10, gamma=0.01) | **0,9825** | **0,9812** | 0,9762 | **0,9977** |

Matriz de confusión (prueba, 114 casos): 41 malignos correctos, 1 falso negativo, 1 falso positivo,
71 benignos correctos. F1 macro de validación (5 folds, semilla 42): 0,9739. El ROC-AUC de la clase
positiva (benigno) es 0,9977 y el de la clase malignant (la costosa) también 0,9977; la configuración
base del manual (C=1, gamma=scale) alcanza 0,9950.

**LAB02** (`reports/dataset_svm_metrics.json`):

| Modelo | Accuracy | F1 macro | Recall `>50K` | ROC-AUC `>50K` |
|---|---|---|---|---|
| DummyClassifier (mismo preprocesamiento) | 0,7607 | 0,4320 | 0,0000 | 0,5000 |
| SVC rbf con pipeline (C=10, gamma=0.1) | **0,8588** | **0,7928** | 0,6146 | **0,8840** |

Prueba: 9.769 casos; 901 falsos negativos y 478 falsos positivos. La búsqueda de hiperparámetros se
hizo sobre una submuestra estratificada del 25 % del entrenamiento (un ajuste completo del SVM sobre
39.073 filas tarda ~30 s) y el mejor modelo se reajustó sobre todo el entrenamiento.

## Lectura de los errores (LAB02)

El perfil de los falsos negativos se **calcula desde los datos** (`reports/dataset_svm_errors_profile.csv`
y `.json`), no se escribe a mano:

| Ámbito | Falsos negativos | `education` | `capital_gain` = 0 |
|---|---|---|---|
| Muestra de 20 errores (semilla 42) | 12 | `HS-grad` 6 · `Bachelors` 3 · `Some-college` 3 | 11 de 12 |
| Prueba completa | 901 | `HS-grad` 357 · `Some-college` 211 · `Bachelors` 117 · `Assoc-voc` 57 · `Masters` 50 · otras 109 | 853 de 901 |

El falso negativo **no** se concentra en las personas con estudios superiores (3 de 12 en la
muestra), sino en quienes declaran ingresos altos sin señales de capital: 11 de los 12 tienen
`capital_gain` = 0 y el único con ganancia de capital (3.103 USD) tiene estudios secundarios. Por eso
la conclusión y el PDF citan estas cifras y no la afirmación anterior.

## Documentos de la entrega

| Documento | Contenido |
|---|---|
| `docs/ficha_dataset.md` | Ficha comparativa de los dos datasets, criterios de aceptación, diccionario, sesgos y usos prohibidos |
| `docs/CONCLUSION_EJERCICIO_01.md` | Conclusión de 350 palabras que integra LAB01 y LAB02 |
| `docs/EJERCICIO_01_PDF_BRIEF.pdf` | PDF breve de la entrega (cifras leídas de `reports/`) |
| `reports/svm_metrics.json` · `reports/dataset_svm_metrics.json` | Métricas de LAB01 y LAB02 (incluido el ROC-AUC) |
| `reports/audit_summary.json` | Auditoría de los dos datasets (tipos, nulos, duplicados, target) |
| `reports/dataset_svm_errors.csv` · `reports/dataset_svm_errors_profile.csv` | 20 errores con categoría y perfil real de los falsos negativos |
| `reports/svm_cv_results.csv` · `reports/dataset_svm_cv_results.csv` | Tablas de la búsqueda de hiperparámetros |
| `reports/*_confusion_matrix.png` · `reports/*_cv_results.png` | Figuras |
| `AI_USE_DECLARATION.md` | Uso honesto del asistente de IA y verificaciones pendientes del estudiante |

## Estado y limitaciones

- **Pendiente:** la aprobación del docente sobre el dataset del LAB02. El manual de la Unidad 01
  prohíbe continuar con el entrenamiento final sin ella; el entrenamiento de este repositorio se
  ejecutó con esa aprobación aún pendiente y así queda registrado en
  `reports/dataset_svm_metrics.json` (`aprobacion_docente: pendiente`), en la portada del PDF
  (fila «Aprobación del docente») y en la sección 4 del PDF.
- **scikit-learn 1.9** marca `SVC(probability=True)` como obsoleto (se elimina en 1.11) y avisa
  durante el ajuste; el manual de la Unidad 01 pide esa opción para el ROC-AUC, así que el proyecto
  la usa y fija `scikit-learn<1.11` en `pyproject.toml`. El sustituto oficial es
  `CalibratedClassifierCV(SVC(), ensemble=False)`.
- Los resultados de LAB02 corresponden a un censo de 1994–1996 de la población activa estadounidense:
  no son extrapolables y no autorizan decisiones sobre personas.

## Cierre de la entrega

La entrega se publica con la etiqueta **`u01-ejercicio01`**:

```bash
git tag -a u01-ejercicio01 -m "Ejercicio 01 · Unidad 01 · LAB00 + LAB01 + LAB02"
git push origin main
git push origin u01-ejercicio01
```

El manual de la Unidad 01 pide cerrar con la etiqueta; el historial completo está en
`git log --oneline`.

## Referencias

- Becker, B. y Kohavi, R. (1996). *Adult* (Census Income). UCI Machine Learning Repository.
  DOI [10.24432/C5XW20](https://doi.org/10.24432/C5XW20). Licencia CC BY 4.0.
- Moro, S., Rita, P. y Cortez, P. (2014). A data-driven approach to predict the success of bank
  telemarketing. *Decision Support Systems*. DOI [10.1016/j.dss.2014.03.001](https://doi.org/10.1016/j.dss.2014.03.001).
- Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. *JMLR*, 12, 2825–2830.
  <https://www.jmlr.org/papers/v12/pedregosa11a.html>.
- Harper, E. W. y Konstan, J. A. (2012). *The Elements of Statistical Learning* (2.ª ed.). Springer.
  DOI [10.1007/978-0-387-84858-7](https://doi.org/10.1007/978-0-387-84858-7).
