# Conclusión · Ejercicio 01 (LAB01 + LAB02)

Proyecto: `INF8239_U01` · Unidad 01 · Fecha: 2026-11-05 · Extensión: 421 palabras (el manual pide 300-500)

**Qué se construyó.** Dos experimentos reproducibles con el mismo esqueleto de proyecto: un pipeline
de SVM con estandarización dentro del `Pipeline` sobre el dataset de diagnóstico de mama de Wisconsin
(LAB01), y un pipeline completo con `ColumnTransformer` (imputación + escala para variables
numéricas, imputación + codificación one-hot para categóricas) sobre el dataset público **Adult
(Census Income)** de UCI (LAB02), elegido tras comparar dos candidatos verificados y documentado en
`docs/ficha_dataset.md`.

**Resultados.** En LAB01 el baseline `DummyClassifier` alcanza 0,6316 de exactitud y 0,3871 de F1 macro
(recall 0 para la clase maligno, porque predice siempre la mayoritaria) y el SVM con `C=10,
gamma=0.01` llega a **0,9825 de exactitud y 0,9812 de F1 macro** en la prueba, con un único falso
negativo sobre 42 casos malignos (recall 0,9762) y un **ROC-AUC de 0,9977** para la clase positiva y
otro de 0,9977 para la clase malignant. En LAB02, sobre 48.842 registros de Adult, el baseline marca
0,7607 de exactitud con recall 0,0000 para la clase `>50K` y el SVM llega a **0,8588 de exactitud,
0,7928 de F1 macro, 0,6146 de recall y 0,8840 de ROC-AUC** para `>50K`.

**Lectura crítica.** El contraste entre ambos resultados es la lección principal. En LAB01 el
desempeño muy alto es coherente con un benchmark didáctico y bien estructurado; en LAB02 el mismo
tipo de modelo deja fuera a **901 de 2.338 personas** que superan el umbral de ingreso. La causa no
está en el algoritmo: `capital_gain` es cero en el 91,74 % de las filas y solo el 21,3 % de los casos
`>50K` lo tienen positivo, de modo que la variable que más distingue los ingresos altos falta en
cuatro de cada cinco casos positivos. A eso se suman 52 filas duplicadas, un censo de 1994–1996 sin
contexto temporal y una población que no cubre a menores ni a personas sin ingresos declarados. Los
20 errores revisados, con semilla fija, **corrigen** una lectura anterior: de los 12 falsos negativos
de la muestra, 6 tienen estudios secundarios (`HS-grad`) y 3 `Some-college`; solo 3 tienen estudios
superiores (`Bachelors`) y 11 de 12 tienen `capital_gain` = 0 (el único con ganancia de capital, 3.103
USD, es un caso `HS-grad`). El desglose, calculado desde los datos, está en
`reports/dataset_svm_errors_profile.csv`.

**Decisión.** Ambos pipelines se entregan como líneas base auditables, no como herramientas de
decisión sobre personas. El siguiente experimento es medir el desempeño por grupo sin usar los
atributos sensibles excluidos (`race`, `sex`, `native_country`), contrastar con un modelo capaz de
representar la dispersión de `capital_gain` y repetir el análisis sobre una cohorte más reciente.

**Pendiente crítico:** la aprobación del docente sobre el dataset de LAB02 sigue sin recibirse; el
manual de la Unidad 01 prohíbe continuar con el entrenamiento final sin ella, y esa limitación queda
registrada en `reports/dataset_svm_metrics.json` (`aprobacion_docente: pendiente`).
