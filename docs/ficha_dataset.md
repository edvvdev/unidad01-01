# Ficha del dataset · LAB02 (Unidad 01)

Proyecto: `INF8239_U01` · Curso: INF-8239 Ciencia de Datos II · Fecha: 2026-11-02
Estado: **comparación de candidatos completada; el entrenamiento final queda pendiente de la
aprobación del docente** (regla del manual: no continuar con el entrenamiento final sin aprobación).

## Identificación del problema

- **Dominio:** caracterización socioeconómica de personas adultas (ingreso anual) o de clientes
  bancarios (suscripción a una campaña), según el dataset elegido.
- **Unidad de análisis:** una persona (un registro del censo o un cliente del banco), no una fila
  parcial ni un evento.
- **Decisión que se toma con el modelo:** estimar si el ingreso supera un umbral (`income > 50K`) o
  si el cliente responde afirmativamente a una campaña (`y = yes`), para priorizar esfuerzo
  comercial o de triaje.
- **Target:** binario en ambos candidatos (2 clases), observable en el momento de la predicción.
- **Error más costoso:** en ambos casos, el **falso negativo** (clasificar como “no” a quien sí
  cumple la condición) deja fuera a una persona que califica; el falso positivo solo genera
  contacto innecesario. En el caso de ingreso, además, el falso negativo puede traducirse en
  denegación de un producto financiero (crédito, préstamo) y, por tanto, en un perjuicio
  distributivo real.
- **Usuario:** responsable de segmentación comercial / triaje de campañas, que debe entender que la
  salida es una estimación y no una decisión.

## Candidatos evaluados

Se evaluaron dos datasets públicos de **UCI Machine Learning Repository**, con ficha oficial y
descarga automatizada. Ninguno contiene identificadores personales directos.

### Candidato A — Adult (Census Income)

| Aspecto | Detalle verificado |
|---|---|
| Procedencia | UCI Machine Learning Repository, *Adult* (Census Income), http://archive.ics.uci.edu/dataset/2/adult |
| Descarga | `https://archive.ics.uci.edu/static/public/2/adult.zip` (script `download_dataset("adult")`) |
| Licencia | **CC BY 4.0** — uso académico permitido con cita |
| Filas / columnas | **48.842 filas × 15 columnas** (`adult.data` + `adult.test`) |
| Periodo | Censo de 1994 (archivo de entrenamiento) y muestra de 1996 (archivo de prueba) |
| Target y clases | `income`: `<=50K` 37.155 (76,07 %) · `>50K` 11.687 (23,93 %) |
| Tipos | 7 numéricas + 7 categóricas + target → exige imputación y one-hot encoding |
| Ausentes | 6.465 celdas: `workclass` 2.799 · `occupation` 2.809 · `native_country` 857 (marcados `?`) |
| Duplicados | 52 filas idénticas (0,11 %) |
| Exclusiones semánticas | `fnlwgt` (peso de muestreo del censo, no atributo de la persona), `race`, `sex` y `native_country` (atributos sensibles innecesarios para estimar el ingreso) → quedan 10 variables: 5 numéricas y 5 categóricas |
| Riesgo de fuga | **Bajo**: ninguna variable se conoce solo después de la decisión. `education` y `education_num` son redundantes (no fuga, pero conviene dejar solo una) |
| Límite declarado | Atributos sensibles presentes en el origen (se excluyen) y posible **sesgo de representatividad**: una sola población, un solo país y una época de hace tres décadas |

### Candidato B — Bank Marketing

| Aspecto | Detalle verificado |
|---|---|
| Procedencia | UCI Machine Learning Repository, *Bank Marketing*, https://archive.ics.uci.edu/dataset/222/bank-marketing |
| Descarga | `https://archive.ics.uci.edu/static/public/222/bank+marketing.zip` (ZIP anidados; script `download_dataset("bank")`) |
| Licencia | **CC BY 4.0** — uso académico permitido con cita |
| Filas / columnas | **45.211 filas × 17 columnas** (`bank-full.csv`) |
| Target y clases | `y`: `no` 39.922 (88,30 %) · `yes` 5.289 (11,70 %) |
| Tipos | 7 numéricas + 9 categóricas + target |
| Ausentes | 52.124 celdas: `poutcome` 36.959 · `contact` 13.020 · `education` 1.857 · `job` 288 (marcados `unknown`) |
| Duplicados | 0 |
| Exclusiones semánticas | `duration` (duración de la llamada): solo se conoce **después** de la llamada → no está disponible al decidir, es fuga de información clásica → quedan 15 variables |
| Riesgo de fuga | **Alto si no se excluye `duration`**: con esa variable el modelo predice «compró» a partir de cuánto duró la llamada. `pdays`, `previous` y `poutcome` sí están disponibles antes de la campaña |
| Límite declarado | Clase positiva muy desbalanceada (11,7 %) y una sola entidad comercial (Portugal, 2008–2013) |

### Tabla comparativa

| Criterio | A · Adult | B · Bank Marketing |
|---|---|---|
| Procedencia verificable | UCI, ficha con DOI y licencia | UCI, ficha con DOI y licencia |
| Licencia | CC BY 4.0 | CC BY 4.0 |
| Filas / columnas | 48.842 × 15 | 45.211 × 17 |
| Target y clases | `income`, 2 clases (76,07 % / 23,93 %) | `y`, 2 clases (88,30 % / 11,70 %) |
| Ausentes | 6.465 (3 columnas) | 52.124 (4 columnas, con `poutcome` mayoritario) |
| Riesgo de fuga | Bajo (con `fnlwgt` y atributos sensibles excluidos) | Alto (exige excluir `duration`) |
| Facilidad para el laboratorio | Alta: tipos mixtos, nulosmoderados, desbalance moderado | Media: nulos muy altos y desbalance fuerte |
| Sensibilidad al preprocesamiento | Media (one-hot de `native_country` y `occupation`) | Alta (one-hot de muchas categóricas con valores `unknown`) |

## Criterios de aceptación del manual

| Criterio | A · Adult | B · Bank Marketing |
|---|---|---|
| ≥ 500 filas | ✔ 48.842 | ✔ 45.211 |
| Target observable con ≥ 2 clases | ✔ 2 clases | ✔ 2 clases |
| Licencia que permita uso académico | ✔ CC BY 4.0 | ✔ CC BY 4.0 |
| Variables disponibles al momento de predecir | ✔ tras excluir `fnlwgt` y sensibles | ✔ solo si se excluye `duration` |
| Tamaño compatible con CPU / Colab | ✔ 5,3 MB | ✔ 3,3 MB |
| Sin datos personales | ✔ identificadores anónimos | ✔ identificadores anónimos |
| No repetido por otro estudiante | Pendiente de confirmación del docente | Pendiente de confirmación del docente |

## Recomendación y estado de aprobación

**Recomendación: candidato A (Adult).** Cumple los cinco criterios sin necesidad de excluir una
variable por fuga de información (la exclusión de `fnlwgt` y de los atributos sensibles es una
decisión de equidad, no una corrección), tiene un desbalance moderado que hace significativo el F1
macro y aporta tipos mixtos con nulos, que es exactamente lo que el laboratorio pide practicar
(`SimpleImputer` + `OneHotEncoder` dentro de un `ColumnTransformer`).

**El candidato B queda documentado como alternativa** y su única exclusión obligatoria
(`duration`) documenta el riesgo de fuga de forma muy didáctica.

> **Pendiente:** este dataset **no** puede usarse para el entrenamiento final hasta que el docente
> apruebe la comparación anterior (regla del manual de la Unidad 01). Estado de aprobación:
> **pendiente del docente** — fecha: ______ — correo enviado: ______.

## Diccionario de datos (candidato A, con exclusiones aplicadas)

| Columna | Tipo | Significado | Unidad / categorías | Momento de disponibilidad | Transformación | Riesgo |
|---|---|---|---|---|---|---|
| `age` | int | Edad de la persona | años (17–90) | Conocida al predecir | Imputación mediana + escala | Bajo |
| `workclass` | cat | Tipo de empleador | 8 categorías + `?` | Conocida | Imputación moda + one-hot | Bajo |
| `education` | cat | Nivel educativo | 16 categorías | Conocida | One-hot | Bajo |
| `education_num` | int | Nivel educativo codificado | 1–16 | Conocida | Escala | Redundante con `education` |
| `marital_status` | cat | Estado civil | 7 categorías | Conocida | One-hot | Bajo |
| `occupation` | cat | Ocupación | 14 categorías + `?` | Conocida | Imputación moda + one-hot | Bajo |
| `relationship` | cat | Relación en el hogar | 6 categorías | Conocida | One-hot | Bajo |
| `capital_gain` | int | Ganancia de capital del año fiscal anterior | dólares | Conocida (año anterior) | Escala | Sesgo temporal: hoy puede no reflectirse |
| `capital_loss` | int | Pérdida de capital del año fiscal anterior | dólares | Conocida | Escala | Ídem |
| `hours_per_week` | int | Horas trabajadas por semana | horas | Conocida | Escala | Bajo |
| `income` | cat | **Target**: ingreso anual | `<=50K` / `>50K` | Etiqueta | — | Desbalance 76/24 |
| `fnlwgt` | int | *Excluido*: peso de muestreo del censo | ponderación | — | — | No es un atributo de la persona |
| `race` | cat | *Excluido*: raza declarada | 5 categorías | — | — | Atributo sensible: riesgo de discriminación |
| `sex` | cat | *Excluido*: sexo | 2 categorías | — | — | Atributo sensible |
| `native_country` | cat | *Excluido*: país de origen | 41 categorías + `?` | — | — | Atributo sensible y con muchos nulos |

### Ejemplos anonimizados (5 filas, candidato A)

| age | workclass | education | education_num | marital_status | occupation | relationship | capital_gain | capital_loss | hours_per_week | income |
|---|---|---|---|---|---|---|---|---|---|---|
| 39 | State-gov | Bachelors | 13 | Never-married | Adm-clerical | Not-in-family | 2174 | 0 | 40 | `<=50K` |
| 50 | Self-emp-not-inc | Bachelors | 13 | Married-civ-spouse | Exec-managerial | Husband | 0 | 0 | 13 | `<=50K` |
| 38 | Private | HS-grad | 9 | Divorced | Handlers-cleaners | Not-in-family | 0 | 0 | 40 | `<=50K` |
| 53 | Private | 11th | 7 | Married-civ-spouse | Handlers-cleaners | Husband | 0 | 0 | 40 | `<=50K` |
| 28 | Private | Bachelors | 13 | Married-civ-spouse | Prof-specialty | Wife | 0 | 0 | 40 | `<=50K` |

Transformaciones aplicadas: valores `?` convertidos en nulos; espacios iniciales y finales
eliminados; el punto final de la columna `income` en `adult.test` eliminado. **No** se recodificó
ninguna categoría ni se eliminaron filas: las 48.842 se conservan y los nulos los resuelve el
`SimpleImputer` dentro del pipeline.

## Sesgos previsibles, población no cubierta y usos prohibidos

- **Población no cubierta:** el censo de 1994 cubre únicamente a la población **activa** de
  Estados Unidos (adultos con empleo o buscando empleo, 16 años o más). No incluye de hecho a
  menores, ni a Proveniente de otros países, ni a personas sin ingresos declarados.
- **Sesgo de representatividad:** los resultados de 1994–1996 no son extrapolables a la población
  actual (niveles educativos, composición del hogar y mercado laboral han cambiado).
- **Sesgo de etiquetado:** la etiqueta `>50K` es un umbral administrativo de 50.000 dólares de 1994,
  no una medida de capacidad de pago; no representa riqueza ni nivel de vida.
- **Sesgo de variables:** `capital_gain`/`capital_loss` corresponden al año fiscal anterior, por lo
  que el modelo aprende una relación con información desfasada.
- **Usos prohibidos:** usar el modelo o sus resultados para decidir crédito, seguros, empleo o
  cualquier decisión sobre personas; publicar predicciones individuales; usar los atributos
  sensibles (`race`, `sex`, `native_country`) que se excluyeron deliberadamente; y afirmar
  causalidad (el dataset es observacional, sin experimental).
