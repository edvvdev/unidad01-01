"""Genera el PDF breve del Ejercicio 01 (entrega del mandato)."""

from __future__ import annotations

import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path("/home/trek/source/uasd/cienciadedatos/tareas/Unidad_1/INF8239_U01")
REPORTS = ROOT / "reports"

svm = json.loads((REPORTS / "svm_metrics.json").read_text(encoding="utf-8"))
adult = json.loads((REPORTS / "dataset_svm_metrics.json").read_text(encoding="utf-8"))
conclusion = (ROOT / "docs/CONCLUSION_EJERCICIO_01.md").read_text(encoding="utf-8")
conclusion_body = conclusion.split("**Qué se construyó.**", 1)[1]
conclusion_body = "**Qué se construyó.**" + conclusion_body.split("**Pendiente crítico:**", 1)[0]

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Title2", parent=styles["Title"], fontSize=17, spaceAfter=6))
styles.add(ParagraphStyle(name="H1s", parent=styles["Heading1"], fontSize=12.5, spaceBefore=10, spaceAfter=4))
styles.add(ParagraphStyle(name="BodyJ", parent=styles["BodyText"], alignment=TA_JUSTIFY, leading=13.5, fontSize=9.6))
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.2, leading=10.5))
styles.add(ParagraphStyle(name="Cell", parent=styles["BodyText"], fontSize=8.4, leading=10.5))

story = []

story.append(Paragraph("Ejercicio 01 · Dataset público y SVM reproducible", styles["Title2"]))
story.append(Paragraph(
    "INF-8239 Ciencia de Datos II (UASD) · Unidad 01 · Integración de LAB01 y LAB02", styles["Small"]))
story.append(Spacer(1, 6))

identificacion = [
    ["Estudiante", "PENDIENTE: nombre completo y matrícula"],
    ["Correo institucional", "PENDIENTE: ID+USUARIO@users.noreply.github.com"],
    ["Profesor", "Edwin Ramón José Nolasco"],
    ["Repositorio", "PENDIENTE: enlace de GitHub (publicar antes de entregar)"],
    ["Fecha de ejecución", "2026-11-02"],
]
table = Table(identificacion, colWidths=[4.2 * cm, 11.6 * cm])
table.setStyle(TableStyle([
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#94a3b8")),
    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.4),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
]))
story.append(table)
story.append(Spacer(1, 10))

story.append(Paragraph("1. Identificación del dataset (LAB02)", styles["H1s"]))
story.append(Paragraph(
    "<b>Adult (Census Income)</b> · UCI Machine Learning Repository · licencia <b>CC BY 4.0</b> · "
    "URL <font face='Courier'>https://archive.ics.uci.edu/static/public/2/adult.zip</font> · ficha "
    "<font face='Courier'>https://archive.ics.uci.edu/dataset/2/adult</font>.<br/>"
    f"{adult['filas_totales']:,} filas x 15 columnas; partición estratificada 80/20 con semilla 42 "
    f"({adult['filas_entrenamiento']:,} entrenamiento / {adult['filas_prueba']:,} prueba). "
    "Target <b>income</b> (<=50K / >50K, 23,93 % positivos). "
    "SHA-256 de los bytes descargados: <font face='Courier'>7537312dd56c2b98035880805ce99e68183a30ee468aa5329d6df0fbb3cc21bb</font>.<br/>"
    "Variables usadas: " + ", ".join(adult["variables_utilizadas"]) + ". "
    "Columnas excluidas por motivo semántico y de equidad: " + ", ".join(adult["columnas_excluidas"]) + ". "
    "El candidato alterno evaluado fue <i>Bank Marketing</i> (UCI, CC BY 4.0), que exige excluir "
    "<i>duration</i> por fuga de información. La ficha comparativa completa está en "
    "<font face='Courier'>docs/ficha_dataset.md</font>.<br/>"
    "<b>LAB01</b> usa el dataset de diagnóstico de mama de Wisconsin incluido en scikit-learn "
    "(569 muestras, 30 variables, 2 clases).", styles["BodyJ"]))
story.append(Spacer(1, 6))

story.append(Paragraph("2. Tabla principal de resultados", styles["H1s"]))
rows = [
    ["Laboratorio", "Modelo", "Accuracy", "F1 macro", "Recall"],
    ["LAB01 · Wisconsin", "DummyClassifier (baseline)", f"{svm['baseline_accuracy']:.4f}",
     f"{svm['baseline_f1_macro']:.4f}", f"{svm['baseline_recall_maligno']:.4f}"],
    ["LAB01 · Wisconsin", "SVC rbf, C=10 gamma=0.01", f"{svm['accuracy']:.4f}",
     f"{svm['f1_macro']:.4f}", f"{svm['recall_maligno']:.4f}"],
    ["LAB02 · Adult", "DummyClassifier (mismo preprocesamiento)", f"{adult['baseline_accuracy']:.4f}",
     f"{adult['baseline_f1_macro']:.4f}", f"{adult['baseline_recall_mas_50k']:.4f}"],
    ["LAB02 · Adult", "SVC rbf con pipeline, C=10 gamma=0.1", f"{adult['accuracy']:.4f}",
     f"{adult['f1_macro']:.4f}", f"{adult['recall_mas_50k']:.4f}"],
]
table = Table(rows, colWidths=[3.5 * cm, 6.2 * cm, 2.0 * cm, 2.0 * cm, 1.9 * cm], repeatRows=1)
table.setStyle(TableStyle([
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
story.append(table)
story.append(Spacer(1, 4))
story.append(Paragraph(
    "Recall de la clase costosa: en LAB01 la clase maligno (0 = maligno); en LAB02 la clase "
    "<b>&gt;50K</b>. F1 macro de validación: 0,9739 (LAB01, 5 folds) y 0,7759 (LAB02, submuestra "
    "estratificada del 25 %; el mejor modelo se reajustó sobre las 39.073 filas de entrenamiento). "
    f"LAB02 deja fuera {adult['falsos_negativos_mas_50k']:,} de {adult['verdaderos_positivos_mas_50k'] + adult['falsos_negativos_mas_50k']:,} "
    "casos que superan el umbral de ingreso.", styles["Small"]))
story.append(Spacer(1, 8))

story.append(Paragraph("3. Figuras", styles["H1s"]))
story.append(Paragraph("Figura 1. LAB01 · matriz de confusión del SVM sobre el conjunto de prueba.", styles["Small"]))
story.append(Image(str(REPORTS / "svm_confusion_matrix.png"), width=11 * cm, height=8.25 * cm))
story.append(Spacer(1, 6))
story.append(Paragraph("Figura 2. LAB02 · matriz de confusión del SVM con pipeline sobre el conjunto de prueba.", styles["Small"]))
story.append(Image(str(REPORTS / "dataset_svm_confusion_matrix.png"), width=11 * cm, height=8.25 * cm))
story.append(Spacer(1, 4))

story.append(PageBreak())
story.append(Paragraph("4. Conclusión", styles["H1s"]))
for paragraph in conclusion_body.strip().split("\n\n"):
    texto = paragraph.strip().replace("\n", " ")
    if texto:
        story.append(Paragraph(texto, styles["BodyJ"]))
        story.append(Spacer(1, 4))

story.append(Spacer(1, 6))
story.append(Paragraph(
    "<b>Estado pendiente:</b> la aprobación del docente sobre el dataset del LAB02 sigue sin "
    "recibirse. El manual de la Unidad 01 prohíbe continuar con el entrenamiento final sin ella; el "
    "entrenamiento se ejecutó con la aprobación pendiente y así queda registrado en "
    "<font face='Courier'>reports/dataset_svm_metrics.json</font> "
    f"(<font face='Courier'>aprobacion_docente: {adult['aprobacion_docente']}</font>). "
    "Los resultados de LAB02 corresponden a un censo de 1994-1996 de la población activa estadounidense: "
    "no son extrapolables y no autorizan decisiones sobre personas.", styles["Small"]))

target = ROOT / "docs/EJERCICIO_01_PDF_BRIEF.pdf"
document = SimpleDocTemplate(str(target), pagesize=LETTER, title="Ejercicio 01 · INF-8239",
                              leftMargin=1.9 * cm, rightMargin=1.9 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm)
document.build(story)
print("PDF generado:", target)
