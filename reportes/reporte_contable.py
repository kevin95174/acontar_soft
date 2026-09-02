import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import ParagraphStyle
from utils.pdf_utils import PageNumCanvas
from collections import defaultdict

def iniciar_reporte_contable(reporte, encabezados, datos, colWidths, direccion):
    pdf_name = str(reporte) + ".pdf"
    pathpdf = os.path.join(direccion, pdf_name)

    doc = SimpleDocTemplate(pathpdf, pagesize=landscape(A4),
                            rightMargin=40, leftMargin=40,
                            topMargin=20, bottomMargin=50)

    elements = []

    # Título 1        
    h1 = ParagraphStyle(name='Heading2', fontSize=12, alignment=1, fontName='HELVETICA-BOLD')
    titulo1 = [[Paragraph(str(reporte), h1)]]

    c1 = ParagraphStyle(name='Normal', fontSize=7, leading=8)
    c3 = ParagraphStyle(name='Normal', fontSize=7, leading=8, fontName='HELVETICA-BOLD', alignment=2)
    c2 = ParagraphStyle(name='Normal', fontSize=7, leading=8, alignment=2)
    c4 = ParagraphStyle(name='Normal', fontSize=7, leading=8, fontName='HELVETICA-BOLD')
    
    # Separar datos por cuenta contable
    datos_por_cuenta = defaultdict(list)
    for row in datos:
        cuenta = row[4]  # Asumiendo que el índice 4 corresponde a 'Cuenta contable'
        datos_por_cuenta[cuenta].append(row)

    # Crear una lista para almacenar los datos de la tabla con subtotales
    table_data = []

    # Variable para el total general
    total_general = 0.0

    # Iterar sobre las cuentas contables y sus datos
    for cuenta, filas in datos_por_cuenta.items():
        # Agregar encabezado de cuenta contable
        table_data.append([Paragraph(f"Cuenta Contable: {cuenta}", c4)] + [""] * (len(encabezados) - 1))

        # Inicializar subtotal para la cuenta actual
        subtotal = 0.0

        # Iterar sobre las filas de la cuenta actual
        for row in filas:
            # Crear una lista para almacenar las celdas de la fila
            row_data = []
            for index, cell in enumerate(row):
                row_data.append(Paragraph(str(cell), c1 if index < 7 else c2))
                if index == 8:  # Asumiendo que el índice 8 corresponde a 'Valor Adquisición'
                    subtotal += float(cell)
            table_data.append(row_data)

        # Agregar subtotal de la cuenta actual con span
        table_data.append([Paragraph(f"Subtotal {cuenta}", c3), "", "", "", "", "", "", "", Paragraph(f"{subtotal:,.2f}", c3)])
        total_general += subtotal

        # Agregar una fila en blanco para la separación visual
        table_data.append([""] * len(encabezados))
        
    # Agregar total general con span
    table_data.append([Paragraph("Total General", c3), "", "", "", "", "", "", "", Paragraph(f"{total_general:,.2f}", c3)])

    # Añadir encabezados a los datos de la tabla
    tabla = titulo1 + [encabezados] + list(table_data)

    # Definir las alturas de fila, siendo 55 el valor para la primera fila
    rowHeights = [55] + [None] * (len(tabla) - 1)

    # Estilo de la tabla
    estilo = [
        # Título del reporte...
        ('SPAN', (0, 0), (-1, 0)),
        # Encabezado
        ('BACKGROUND', (0, 1), (-1, 1), '#DBDBDB'),
        # Bordes de la tabla
        ('GRID', (0, 1), (-1, -1), 0.5, colors.black),
        # Cuerpo de la tabla
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 2), (10, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    # Agregar span a las filas de subtotales y total general
    for i in range(len(titulo1) + 1, len(tabla)):
        if isinstance(tabla[i][0], Paragraph):
            if "Subtotal" in tabla[i][0].text or "Total General" in tabla[i][0].text:
                estilo.append(('SPAN', (0, i), (5, i)))
                estilo.append(('LINEBELOW', (0, i), (5, i), 1, colors.white))
                estilo.append(('LINEBEFORE', (0, i), (5, i), 1, colors.white))
            elif "Cuenta Contable" in tabla[i][0].text:
                estilo.append(('SPAN', (0, i), (-1, i)))
                # estilo.append(('GRID', (0, i), (-1, i), 1, colors.white))
        # Establecer el estilo para las filas en blanco
        elif tabla[i] == [""] * len(encabezados):
            estilo.append(('LINEBEFORE', (0, i), (-1, i), 1, colors.white))
            estilo.append(('LINEAFTER', (0, i), (-1, i), 1, colors.white))
            estilo.append(('LINEBELOW', (0, i), (-1, i), 0.5, colors.black))
            estilo.append(('LINEABOVE', (6, i), (-1, i), 0.5, colors.black))

    t = Table(tabla, colWidths, rowHeights=rowHeights, repeatRows=2, style=estilo)

    elements.append(t)

    doc.build(elements, canvasmaker=PageNumCanvas)