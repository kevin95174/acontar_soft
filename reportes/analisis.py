import os
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import ParagraphStyle
from utils.pdf_utils import PageNumCanvas

def iniciar_reporte(datos, direccion, colWidths, nombre, encabezados, orientacion, columna):

        today = date.today()
        pdf_name = str(nombre)+today.strftime("%d_%m_%Y")+".pdf"
        pathpdf = os.path.join(direccion, pdf_name)

        doc = SimpleDocTemplate(pathpdf, pagesize= A4 if orientacion ==1 else landscape(A4),
                                rightMargin=40, leftMargin=40,
                                topMargin=20, bottomMargin=50)
        
        elements = []
        # Titulo 1        
        h1 = ParagraphStyle(name='Heading2', fontSize=12, alignment=1, fontName = 'HELVETICA-BOLD')
        titulo1 = [[Paragraph(str(nombre),h1)]]
        h2 = ParagraphStyle(name='Heading', fontSize=12, alignment=1, fontName = 'HELVETICA-BOLD', leading=15)

        # data = [[Paragraph('Análisis por cuenta contable', h2)], [Paragraph('<b>Cuenta Contable</b>', h1), Paragraph('<b>SubCuenta</b>', h1), Paragraph('<b>Denominación</b>', h1), Paragraph('<b>Valor Registro Patrimonial</b>', h1), Paragraph('<b>Cantidad Registro Patrimonial</b>', h1), Paragraph('<b>Valor Resultado Inventario</b>', h1), Paragraph('<b>Cantidad Resultado Inventario</b>', h1), Paragraph('<b>Valor Faltantes</b>', h1), Paragraph('<b>Cantidad Faltantes</b>', h1)]]

        b1 = ParagraphStyle(name='Normal', fontSize=8, leading = 9)
        b2 = ParagraphStyle(name='Normal', fontSize=8, alignment=2, leading = 9)
        # Crear una lista para almacenar los datos de la tabla
        table_data = []
        for row in datos:
            # Crear una lista para almacenar las celdas de la fila
            row_data = []
            for index, cell in enumerate(row):
			# my_tag = 'normal' if str(g[4]) == str(self.valor.get()) else 'fail'
                row_data.append(Paragraph(str(cell), b1 if index < columna else b2))
            table_data.append(row_data)

        # for i in tabla:
        #     data.append(i)

        tabla = titulo1 + [encabezados] + list(table_data)

        # print(tabla)

        rowHeights = [55] + [None] * (len(tabla) - 1)
        # colWidths = [55, 70, 180, 75, 65, 75, 65, 75, 65]

        t=Table(tabla, colWidths=colWidths, rowHeights=rowHeights, repeatRows=2, style=[
                                        # titulo FORMATO...
                                        ('SPAN', (0, 0), (-1, 0)),
                                        ('BACKGROUND', (0, 1), (-1, 1), '#DBDBDB'),
                                        # ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                                        ('ALIGN', (0, 1), (-1, 1), 'CENTER'),
                                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                        
                                        #('ALIGN', (int(columna), 1), (2, -1), 'RIGHT'),
                                        
                                        ('GRID', (0, 1), (-1, -1), 0.5, colors.black),
                                        
                                        ('SPAN', (0, len(tabla)-1), (int(columna)-1, len(tabla)-1)),
                                        
                                        ])
        
        elements.append(t)
        # write the document to disk
        def create_canvas(*args, **kwargs):
            return PageNumCanvas(*args, orientacion=orientacion, **kwargs)
        doc.build(elements, canvasmaker=create_canvas)
        # print("Funciono 1 vez")
