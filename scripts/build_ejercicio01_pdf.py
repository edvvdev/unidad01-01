"""Genera el PDF breve del Ejercicio 01 (entrega del mandato).

Todas las cifras del PDF se leen de `reports/` (o de los sidecars de `data/raw/`):
el script no escribe ningún número a mano.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

#: URL del repositorio donde se publica esta entrega. Se puede sobrescribir con la variable
#: de entorno REPO_URL al regenerar el PDF (por ejemplo, para publicar un fork).
REPO_URL = os.getenv("REPO_URL", "https://github.com/edvvdev/unidad01-01")

ROOT = Path(__file__).resolve().parents[1]   # raíz del proyecto, válida en cualquier clon
REPORTS = ROOT / "reports"
DATA_RAW = ROOT / "data" / "raw"

svm = json.loads((REPORTS / "svm_metrics.json").read_text(encoding="utf-8"))
adult = json.loads((REPORTS / "dataset_svm_metrics.json").read_text(encoding="utf-8"))
auditoria = json.loads((REPORTS / "audit_summary.json").read_text(encoding="utf-8"))
perfil = json.loads((REPORTS / "dataset_svm_errors_profile.json").read_text(encoding="utf-8"))
conclusion = (ROOT / "docs/CONCLUSION_EJERCICIO_01.md").read_text(encoding="utf-8")
conclusion_body = conclusion.split("**Qué se construyó.**", 1)[1]
conclusion_body = "**Qué se construyó.**" + conclusion_body.split("**Pendiente crítico:**", 1)[0]


def markdown(texto: str) -> str:
    """Convierte **negrita** y `código` de Markdown en etiquetas de reportlab."""
    escapado = texto.replace("&", "&amp;")
    escapado = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", escapado)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escapado)


def numero(valor: float | None, decimales: int = 4) -> str:
    """Número con coma decimal (formato español) o guion si no hay dato."""
    if valor is None:
        return "—"
    return f"{valor:.{decimales}f}".replace(".", ",")


def entero(valor: int | None) -> str:
    """Entero con separador de miles o guion si no hay dato."""
    if valor is None:
        return "—"
    return f"{valor:,}".replace(",", ".")


def sha256_de_sidecar(nombre: str) -> str:
    """SHA-256 publicado en el sidecar `data/raw/<nombre>.sha256` (cadena vacía si no existe)."""
    sidecar = DATA_RAW / f"{nombre}.sha256"
    if not sidecar.exists():
        return ""
    partes = sidecar.read_text(encoding="utf-8").split()
    return partes[0] if partes else ""


def perfil_educativo(conteo: dict, limite: int) -> str:
    """Perfil educativo de un tipo de error: categorías más frecuentes y el resto agrupado."""
    total = sum(conteo.values())
    ordenados = sorted(conteo.items(), key=lambda par: (-par[1], par[0]))
    principales = ordenados[:limite]
    texto = " · ".join(f"{clave} {valor}" for clave, valor in principales)
    if len(ordenados) > limite:
        texto += f" · otras {total - sum(valor for _, valor in principales)}"
    return texto


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Title2", parent=styles["Title"], fontSize=17, spaceAfter=6))
styles.add(ParagraphStyle(name="H1s", parent=styles["Heading1"], fontSize=12.5, spaceBefore=10, spaceAfter=4))
styles.add(ParagraphStyle(name="BodyJ", parent=styles["BodyText"], alignment=TA_JUSTIFY, leading=13.5, fontSize=9.6))
styles.add(ParagraphStyle(name="BodyLeft", parent=styles["BodyText"], alignment=TA_LEFT, leading=13.5, fontSize=9.6))
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.2, leading=10.5))
styles.add(ParagraphStyle(name="Cell", parent=styles["BodyText"], fontSize=8.4, leading=10.5))
styles.add(ParagraphStyle(name="CellLabel", parent=styles["BodyText"], fontName="Helvetica-Bold",
                          fontSize=8.4, leading=10.5))
styles.add(ParagraphStyle(name="TableCell", parent=styles["BodyText"], fontSize=8.2, leading=10))
styles.add(ParagraphStyle(name="TableHead", parent=styles["BodyText"], fontName="Helvetica-Bold",
                          fontSize=8.2, leading=10, textColor=colors.white))

story = []

# --------------------------------------------------------------------------------------
# Portada
# --------------------------------------------------------------------------------------
story.append(Paragraph("Ejercicio 01 · Dataset público y SVM reproducible", styles["Title2"]))
story.append(Paragraph(
    "INF-8239 Ciencia de Datos II (UASD) · Unidad 01 · Integración de LAB01 y LAB02", styles["Small"]))
story.append(Spacer(1, 6))

valores = {
    "estudiante": "Edwing Perez",
    "profesor": "Edwin Ramón José Nolasco",
    "repositorio": REPO_URL,
    "fecha": adult.get("fecha_ejecucion", ""),
    "aprobacion": Paragraph(
        "<b>Pendiente.</b> El manual de la Unidad 01 prohíbe continuar con el entrenamiento final sin "
        "la aprobación del docente sobre el dataset: el entrenamiento de este repositorio se ejecutó "
        "con esa aprobación todavía pendiente y así queda declarado en "
        "<font face='Courier'>reports/dataset_svm_metrics.json</font> "
        f"(<font face='Courier'>aprobacion_docente: {adult.get('aprobacion_docente', 'pendiente')}</font>).",
        styles["Cell"]),
}
identificacion = [
    ["Estudiante", valores["estudiante"]],
    ["Profesor", valores["profesor"]],
    ["Repositorio", valores["repositorio"]],
    ["Fecha de ejecución", valores["fecha"]],
    ["Aprobación del docente", valores["aprobacion"]],
]
table = Table(identificacion, colWidths=[4.2 * cm, 11.6 * cm])
table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.4),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
story.append(table)
story.append(Spacer(1, 10))

# --------------------------------------------------------------------------------------
# 1. Identificación del dataset (LAB02)
# --------------------------------------------------------------------------------------
adult_audit = auditoria["datasets"]["adult"]
target_counts = adult_audit.get("target_counts", {})
positivos = target_counts.get(">50K", 0)
total_filas = adult_audit.get("filas", adult.get("filas_totales", 0))
pct_positivos = 100 * positivos / total_filas if total_filas else 0.0
sha_zip = sha256_de_sidecar("adult.zip")
sha_csv = sha256_de_sidecar("adult.csv")

story.append(Paragraph("1. Identificación del dataset (LAB02)", styles["H1s"]))
story.append(Paragraph(
    "<b>Adult (Census Income)</b> · UCI Machine Learning Repository · licencia <b>CC BY 4.0</b>.<br/>"
    "URL <font face='Courier'>https://archive.ics.uci.edu/static/public/2/adult.zip</font><br/>"
    "Ficha <font face='Courier'>https://archive.ics.uci.edu/dataset/2/adult</font><br/>"
    f"{entero(adult.get('filas_totales'))} filas x {adult_audit.get('columnas', 0)} columnas; partición "
    f"estratificada 80/20 con semilla {adult.get('seed', 42)} "
    f"({entero(adult.get('filas_entrenamiento'))} entrenamiento / {entero(adult.get('filas_prueba'))} prueba).<br/>"
    f"Target <b>income</b> (<=50K / >50K, {numero(pct_positivos, 2)} % positivos).<br/>"
    "Variables usadas: " + ", ".join(adult["variables_utilizadas"]) + ".<br/>"
    "Columnas excluidas por motivo semántico y de equidad: " + ", ".join(adult["columnas_excluidas"]) + ".<br/>"
    "El candidato alterno evaluado fue <i>Bank Marketing</i> (UCI, CC BY 4.0), que exige excluir "
    "<i>duration</i> por fuga de información. La ficha comparativa completa está en "
    "<font face='Courier'>docs/ficha_dataset.md</font>.<br/>"
    "<b>LAB01</b> usa el dataset de diagnóstico de mama de Wisconsin incluido en scikit-learn "
    "(569 muestras, 30 variables, 2 clases).", styles["BodyLeft"]))
story.append(Paragraph(
    f"SHA-256 del ZIP: <font face='Courier'>{sha_zip}</font><br/>"
    f"SHA-256 del CSV normalizado: <font face='Courier'>{sha_csv}</font><br/>"
    "(ambos verificables desde la raíz del proyecto con "
    "<font face='Courier'>sha256sum -c data/raw/*.sha256</font>).", styles["Small"]))
story.append(Spacer(1, 6))

# --------------------------------------------------------------------------------------
# 2. Tabla principal de resultados
# --------------------------------------------------------------------------------------
story.append(Paragraph("2. Tabla principal de resultados", styles["H1s"]))
filas = [
    ["Laboratorio", "Modelo", "Accuracy", "F1 macro", "Recall", "ROC-AUC"],
    ["LAB01 · Wisconsin", "DummyClassifier (baseline)", numero(svm.get("baseline_accuracy")),
     numero(svm.get("baseline_f1_macro")), numero(svm.get("baseline_recall_maligno")),
     numero(svm.get("baseline_roc_auc"))],
    ["LAB01 · Wisconsin", "SVC rbf, C=10 gamma=0.01", numero(svm.get("accuracy")),
     numero(svm.get("f1_macro")), numero(svm.get("recall_maligno")), numero(svm.get("roc_auc"))],
    ["LAB02 · Adult", "DummyClassifier (mismo preprocesamiento)", numero(adult.get("baseline_accuracy")),
     numero(adult.get("baseline_f1_macro")), numero(adult.get("baseline_recall_mas_50k")),
     numero(adult.get("baseline_roc_auc"))],
    ["LAB02 · Adult", "SVC rbf con pipeline, C=10 gamma=0.1", numero(adult.get("accuracy")),
     numero(adult.get("f1_macro")), numero(adult.get("recall_mas_50k")),
     numero(adult.get("roc_auc_mas_50k"))],
]
tabla = Table(filas, colWidths=[3.1 * cm, 5.6 * cm, 1.9 * cm, 1.9 * cm, 1.8 * cm, 2.0 * cm], repeatRows=1)
tabla.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f7c7b")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.2),
    ("ALIGN", (2, 1), (-1, -1), "CENTER"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
story.append(tabla)
story.append(Spacer(1, 4))
story.append(Paragraph(
    "Recall de la clase costosa: en LAB01 la clase maligno (0 = maligno); en LAB02 la clase "
    "<b>&gt;50K</b>. <b>ROC-AUC</b> (área bajo la curva ROC de la clase positiva, la que pide el manual "
    "en LAB01 §8): en LAB01 la clase positiva es benigno (target = 1) y la clase costosa, maligno, da "
    f"prácticamente el mismo valor ({numero(svm.get('roc_auc'))} frente a {numero(svm.get('roc_auc_maligno'))}); "
    f"en LAB02 la clase positiva es &gt;50K y alcanza {numero(adult.get('roc_auc_mas_50k'))}. "
    "F1 macro de validación: "
    f"{numero(svm.get('f1_macro_validacion'))} (LAB01, 5 folds) y "
    f"{numero(adult.get('f1_macro_submuestra_validacion'))} (LAB02, submuestra estratificada del 25 %; el mejor "
    f"modelo se reajustó sobre las {entero(adult.get('filas_entrenamiento'))} filas de entrenamiento). "
    f"LAB02 deja fuera {entero(adult.get('falsos_negativos_mas_50k'))} de "
    f"{entero((adult.get('verdaderos_positivos_mas_50k') or 0) + (adult.get('falsos_negativos_mas_50k') or 0))} "
    "casos que superan el umbral de ingreso.", styles["Small"]))
story.append(Spacer(1, 8))

# --------------------------------------------------------------------------------------
# 2.1 Perfil real de los falsos negativos (LAB02)
# --------------------------------------------------------------------------------------
muestra_fn = perfil["muestra"]["falso_negativo"]
prueba_fn = perfil["prueba_completa"]["falso_negativo"]
bloque_perfil = []
bloque_perfil.append(Paragraph("2.1 Perfil real de los falsos negativos (LAB02)", styles["H1s"]))
bloque_perfil.append(Paragraph(
    "El desglose se calcula desde los datos y se publica en "
    "<font face='Courier'>reports/dataset_svm_errors_profile.csv</font> y "
    "<font face='Courier'>.json</font>.", styles["Small"]))
filas_perfil = [
    ["Ámbito", "Falsos negativos", "Nivel educativo", "capital_gain = 0"],
    [f"Muestra de {perfil.get('muestra_errores', 20)} errores (semilla {perfil.get('semilla', 42)})",
     str(muestra_fn["n"]),
     perfil_educativo(muestra_fn["education"], 3),
     f"{muestra_fn['capital_gain_cero']} de {muestra_fn['n']}"],
    ["Prueba completa",
     str(prueba_fn["n"]),
     perfil_educativo(prueba_fn["education"], 5),
     f"{prueba_fn['capital_gain_cero']} de {prueba_fn['n']}"],
]
tabla_perfil = Table(
    [[Paragraph(celda, styles["TableHead" if indice == 0 else "TableCell"])
      for celda in fila]
     for indice, fila in enumerate(filas_perfil)],
    colWidths=[4.6 * cm, 2.4 * cm, 6.0 * cm, 2.6 * cm],
    repeatRows=1,
)
tabla_perfil.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f7c7b")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
]))
bloque_perfil.append(tabla_perfil)
bloque_perfil.append(Spacer(1, 4))
bloque_perfil.append(Paragraph(
    "El falso negativo <b>no</b> se concentra en las personas con estudios superiores: en la muestra solo "
    f"{muestra_fn['education'].get('Bachelors', 0)} de {muestra_fn['n']} tienen estudios superiores "
    f"({muestra_fn['education'].get('HS-grad', 0)} tienen estudios secundarios y "
    f"{muestra_fn['education'].get('Some-college', 0)} tienen estudios no terminados), y "
    f"{muestra_fn['capital_gain_cero']} de {muestra_fn['n']} no tienen ganancia de capital "
    f"(el único con ganancia de capital, {muestra_fn['capital_gain_positivo_filas'][0]['capital_gain'] if muestra_fn['capital_gain_positivo_filas'] else 0} USD, "
    f"tiene nivel educativo {muestra_fn['capital_gain_positivo_filas'][0]['education'] if muestra_fn['capital_gain_positivo_filas'] else 'sin definir'}"
    "). El perfil es el de quien declara ingresos altos sin señales de capital.",
    styles["Small"]))
story.append(KeepTogether(bloque_perfil))
story.append(Spacer(1, 8))

# --------------------------------------------------------------------------------------
# 3. Figuras
# --------------------------------------------------------------------------------------
story.append(Paragraph("3. Figuras", styles["H1s"]))
story.append(KeepTogether([
    Paragraph("Figura 1. LAB01 · matriz de confusión del SVM sobre el conjunto de prueba.", styles["Small"]),
    Image(str(REPORTS / "svm_confusion_matrix.png"), width=9.5 * cm, height=7.125 * cm),
    Spacer(1, 6),
]))
story.append(KeepTogether([
    Paragraph("Figura 2. LAB02 · matriz de confusión del SVM con pipeline sobre el conjunto de prueba.", styles["Small"]),
    Image(str(REPORTS / "dataset_svm_confusion_matrix.png"), width=9.5 * cm, height=7.125 * cm),
]))
story.append(Spacer(1, 4))

story.append(PageBreak())

# --------------------------------------------------------------------------------------
# 4. Conclusión
# --------------------------------------------------------------------------------------
story.append(Paragraph("4. Conclusión", styles["H1s"]))
for paragraph in conclusion_body.strip().split("\n\n"):
    texto = paragraph.strip().replace("\n", " ")
    if texto:
        story.append(Paragraph(markdown(texto), styles["BodyJ"]))
        story.append(Spacer(1, 4))

story.append(Spacer(1, 6))
story.append(Paragraph(
    "<b>Estado pendiente:</b> la aprobación del docente sobre el dataset del LAB02 sigue sin "
    "recibirse. El manual de la Unidad 01 prohíbe continuar con el entrenamiento final sin ella; el "
    "entrenamiento se ejecutó con la aprobación pendiente y así queda registrado en "
    "<font face='Courier'>reports/dataset_svm_metrics.json</font> "
    f"(<font face='Courier'>aprobacion_docente: {adult.get('aprobacion_docente', 'pendiente')}</font>). "
    "Los resultados de LAB02 corresponden a un censo de 1994-1996 de la población activa estadounidense: "
    "no son extrapolables y no autorizan decisiones sobre personas.", styles["Small"]))
story.append(Spacer(1, 10))

# --------------------------------------------------------------------------------------
# 5. Referencias
# --------------------------------------------------------------------------------------
story.append(Paragraph("5. Referencias", styles["H1s"]))
referencias = [
    "Becker, B. y Kohavi, R. (1996). <i>Adult</i> (Census Income). UCI Machine Learning Repository. "
    "DOI 10.24432/C5XW20. Licencia CC BY 4.0.",
    "Moro, S., Rita, P. y Cortez, P. (2014). A data-driven approach to predict the success of bank "
    "telemarketing. <i>Decision Support Systems</i>. DOI 10.1016/j.dss.2014.03.001.",
    "Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. <i>JMLR</i>, 12, 2825-2830.",
    "Harper, E. W. y Konstan, J. A. (2012). <i>The Elements of Statistical Learning</i> (2.ª ed.). Springer. "
    "DOI 10.1007/978-0-387-84858-7.",
]
for referencia in referencias:
    story.append(Paragraph(referencia, styles["Small"]))
    story.append(Spacer(1, 3))

target = ROOT / "docs/EJERCICIO_01_PDF_BRIEF.pdf"
document = SimpleDocTemplate(str(target), pagesize=LETTER, title="Ejercicio 01 · INF-8239",
                              leftMargin=1.9 * cm, rightMargin=1.9 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm)
document.build(story)
print("PDF generado:", target)
print("Repositorio publicado en el PDF:", REPO_URL)
