from io import BytesIO
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

from core import CLASS_NAMES, FEATURE_NAMES, RECOMMENDATIONS, visible_value

NAVY = colors.HexColor('#142C42')
TEAL = colors.HexColor('#087E82')
GRAY = colors.HexColor('#65758A')
PALE = colors.HexColor('#EDF4F6')
FONT_ROOT = Path(__file__).resolve().parent / 'assets' / 'fonts'
pdfmetrics.registerFont(TTFont('CyberSans', str(FONT_ROOT / 'DejaVuSans.ttf')))
pdfmetrics.registerFont(TTFont('CyberSans-Bold', str(FONT_ROOT / 'DejaVuSans-Bold.ttf')))
pdfmetrics.registerFontFamily('CyberSans', normal='CyberSans', bold='CyberSans-Bold')


def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(name='Brand', fontName='CyberSans-Bold', fontSize=10, textColor=TEAL, spaceAfter=16))
    s.add(ParagraphStyle(name='Hero', fontName='CyberSans-Bold', fontSize=28, leading=32, textColor=NAVY, spaceAfter=14))
    s.add(ParagraphStyle(name='Sub', fontName='CyberSans', fontSize=11, leading=16, textColor=GRAY, spaceAfter=18))
    s.add(ParagraphStyle(name='Section', fontName='CyberSans-Bold', fontSize=13, leading=18, textColor=NAVY, spaceBefore=12, spaceAfter=8))
    s.add(ParagraphStyle(name='BodyCustom', fontName='CyberSans', fontSize=9.5, leading=14, textColor=NAVY, spaceAfter=8))
    s.add(ParagraphStyle(name='SmallCustom', fontName='CyberSans', fontSize=8, leading=11, textColor=GRAY, spaceAfter=7))
    s.add(ParagraphStyle(name='Cell', fontName='CyberSans', fontSize=8.5, leading=12, textColor=NAVY))
    s.add(ParagraphStyle(name='CellHeader', fontName='CyberSans-Bold', fontSize=8.5, leading=12, textColor=colors.white))
    return s


def paragraph(text, style):
    return Paragraph(escape(str(text)), style)


def table(rows, widths, s):
    wrapped = [[paragraph(cell, s['CellHeader'] if i == 0 else s['Cell']) for cell in row] for i, row in enumerate(rows)]
    result = Table(wrapped, colWidths=widths, repeatRows=1, hAlign='LEFT')
    result.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PALE]),
        ('LINEBELOW', (0, 0), (-1, 0), 1, TEAL),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    return result


def footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(PALE)
    canvas.line(44, 36, width - 44, 36)
    canvas.setFont('CyberSans', 8)
    canvas.setFillColor(GRAY)
    canvas.drawString(44, 23, 'CyberScope | Bryan Madrid | Prototipo de investigación')
    canvas.drawRightString(width - 44, 23, str(doc.page))
    canvas.restoreState()


def document(story):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=44, rightMargin=44,
                           topMargin=38, bottomMargin=52, title='CyberScope', author='Bryan Madrid')
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()


def report_pdf(prediction, labels, evaluation, explanation=None):
    s = styles()
    class_index = labels.index(prediction.label)
    probability = prediction.probabilities[class_index]
    story = [paragraph('CYBERSCOPE / INFORME DE ANÁLISIS', s['Brand']),
             paragraph('Severidad cibernética', s['Hero']),
             paragraph('Estimación para revisión del analista', s['Sub']),
             paragraph(f'Informe {prediction.id} | {prediction.timestamp}', s['SmallCustom'])]
    company = str(prediction.context.get('empresa', '')).strip()
    if company:
        story.append(paragraph(f'Organización: {company}', s['BodyCustom']))
    asset = str(prediction.context.get('activo', '')).strip()
    if asset:
        story.append(paragraph(f'Activo o referencia: {asset}', s['BodyCustom']))
    story.extend([paragraph('Resultado', s['Section']),
                  table([['Indicador', 'Valor'], ['Severidad estimada', CLASS_NAMES[prediction.label]],
                         ['Probabilidad estimada de la clase', f'{probability:.1%}'],
                         ['Diferencia entre las dos clases más probables', f'{prediction.margin:.1%}'],
                         ['Perfiles idénticos en desarrollo', str(prediction.profile_count)],
                         ['Enfoque', 'Macrofamilia y contexto tecnológico'], ['Modelo', prediction.candidate]], [220, 287], s),
                  paragraph(RECOMMENDATIONS[prediction.label], s['BodyCustom']),
                  paragraph('La prioridad operativa y los plazos se definen mediante los procedimientos de la organización y la revisión del analista.', s['SmallCustom']),
                  paragraph('Datos utilizados por el modelo', s['Section']),
                  table([['Variable', 'Valor']] + [[FEATURE_NAMES[c], visible_value(v)] for c, v in prediction.values.items()
], [145, 362], s)])
    if prediction.unknown:
        story.extend([paragraph('Categorías nuevas', s['Section']),
                      paragraph(', '.join(FEATURE_NAMES[c] for c in prediction.unknown) + '. Estos valores no aparecieron en el entrenamiento.', s['BodyCustom'])])
    story.extend([PageBreak(), paragraph('CYBERSCOPE / EVIDENCIA DEL ANÁLISIS', s['Brand']),
                  paragraph('Distribución estimada', s['Hero']),
                  table([['Severidad', 'Probabilidad']] + [[CLASS_NAMES[label], f'{prediction.probabilities[k]:.2%}'] for k, label in enumerate(labels)], [330, 177], s),
                  paragraph('Evaluación global del modelo seleccionado', s['Section']),
                  table([['Métrica del test temporal', 'Valor'], ['Accuracy', f'{evaluation["accuracy"]:.2%}'],
                         ['F1-Macro de tres clases', f'{evaluation["f1_macro_3"]:.4f}'],
                         ['Precision Macro', f'{evaluation["precision_macro_3"]:.4f}'],
                         ['Recall Macro', f'{evaluation["recall_macro_3"]:.4f}']], [330, 177], s),
                  paragraph('Las métricas globales corresponden al modelo congelado y al test temporal de 397 registros. La probabilidad individual no representa la exactitud global.', s['SmallCustom'])])
    if explanation:
        story.extend([paragraph('Explicación local LIME', s['Section']),
                      paragraph(f'Clase explicada: {CLASS_NAMES[explanation["explained_class"]]}. Fondo: {explanation["background"]}. R² local: {explanation["r2"]:.3f}; diferencia modelo-aproximación: {explanation["gap"]:.3f}.', s['BodyCustom']),
                      table([['Condición', 'Peso local']] + [[r['condition'], f'{r["weight"]:+.4f}'] for r in explanation['weights']], [407, 100], s),
                      paragraph('LIME aproxima el comportamiento local del modelo. Los pesos no son causas del incidente ni validan la etiqueta de referencia.', s['SmallCustom'])])
    story.extend([paragraph('Alcance', s['Section']),
                  paragraph('Prototipo experimental basado en etiquetas de referencia de CISA y MITRE. No estima por sí solo la probabilidad de sufrir un ataque ni el impacto económico. La clase low tiene cinco registros en el test. high agrupa high y critical. El test fue revisitado tras redefinir las clases. El contexto puede reflejar la procedencia de los datos.', s['BodyCustom']),
                  paragraph('Bryan Madrid | Ingeniería Civil Informática | Universidad Andrés Bello', s['SmallCustom'])])
    return document(story)
