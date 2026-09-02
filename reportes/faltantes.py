import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from tkinter import filedialog
from db.query import reporte_faltantes, mostrar_d_personal
from utils.pdf_utils import PageNumCanvas

def iniciar_reporte(n_acta):
        r = mostrar_d_personal(n_acta)
        v1 = r[0][0]
        v2 = r[0][1]
        v3 = r[0][2]
        v4 = r[0][3]
        v5 = r[0][4]
        v6 = r[0][5]

        pathinit = 'exportar/reportes/'
        file_path = filedialog.askdirectory(initialdir=pathinit)        

        j = "Acta " + str(v1) + " " + str(v2) + " " + "AREA " + str(v3) + " " + "OFICINA " + str(v4)
        # j = "Acta " + Paragraph(v1) + " " + Paragraph(v2) + " " + "AREA " + Paragraph(v3) + " " + "OFICINA " + Paragraph(v4)
        pdf_name = "Faltantes_"+str(j)+".pdf"
        pathinit = 'report_actas/reporte_faltantes/'
        pathpdf = os.path.join(file_path, pdf_name)

        doc = SimpleDocTemplate(pathpdf, pagesize=landscape(A4),
                                rightMargin=40, leftMargin=40,
                                topMargin=20, bottomMargin=50)
        
        elements = []

        t11 = [] 
        t22 = [] 
        # Titulos
        estilos = getSampleStyleSheet()
        # Titulo 1
        h1 = ParagraphStyle(name='Heading1', fontSize=15, alignment=1, fontName = 'HELVETICA-BOLD')
        titulo1 = Paragraph('<u>Reporte bienes faltantes</u>',h1)
        # Titulo 2
        t_estilo2 = estilos['Heading2']
        t_estilo2.alignment = 1
        t_estilo2.fontSize = 15
        t_estilo2.spaceAfter = 1
        t_estilo2.spaceBefore = 1
        titulo2 = Paragraph('', t_estilo2)

        test1 = ""
        test2 = ""
        test3 = ""
        test4 = "ACTA NRO: " + str(v1)

        t11.append(test1)
        t11.append(test1)
        t11.append(titulo1)
        t11.append(test2)
        t11.append(test3)
        t11.append(test1)
        t11.append(test4)
        t11.append(test4)
        t11.append(test4)
        t11.append(test4)
        t11.append(test4)
        t11.append(test4)
        t22.append(titulo2)

        x = reporte_faltantes(n_acta)

        p1 = ParagraphStyle(name='Normal', fontSize=7, leading = 8)
        p2 = ParagraphStyle(name='Normal', fontSize=7, leading = 8, alignment=1)
        p3 = ParagraphStyle(name='Normal', fontSize=7, leading = 8, alignment=2)

        table_data = []

        for row in x:
            row_data = []
            for index, cell in enumerate(row):
                if index == 4:
                    row_data.append(Paragraph(str(cell), p2))
                elif index == 10:
                    row_data.append(Paragraph(str(cell), p3))
                else:
                    row_data.append(Paragraph(str(cell), p1))
            table_data.append(row_data)

        entidad = "Oficina Regional Altiplano Puno"
        ruc = "2036418036"
        inventario = "2022"
        local = str(v2)
        area = str(v3)
        oficina = str(v4)
        responsable = str(v6)
        dni = str(v5)
        # Datos del Usuario


        t1 = ("Entidad", "",": " + str(entidad), "","RUC", "",": " + str(ruc), "","Inventario", ": " + str(inventario))
        t2 = ("Local", "",": " + str(local), "","Area:", "",": " + str(area), "","Oficina:", ": " + str(oficina))

        enc=  ('Item','Codigo\nInterno', 'Codigo\nPatrimonial', 'Denominación', 'Estado', 'Dimensión', 
                    'Marca', 'Modelo', 'Serie', 'Color', 'Valor', 'Obs')
        
        table_data.insert(0, enc)
        # table_data.insert(0, t3)
        table_data.insert(0, t2)
        table_data.insert(0, t1)
        table_data.insert(0, t22)
        table_data.insert(0, t11)
        
        tabla = list(table_data)

        rowHeights = [55] + [None] * (len(tabla) - 1)

        colWidths = [30, 40, 60, 150, 30, 60, 80, 80, 80, 50, 50, 50]
        t=Table(tabla, colWidths, rowHeights=rowHeights, repeatRows =5, style=[                                    
                                                        ('SPAN', (0, 0), (1, 0)),
                                                        ('SPAN', (2, 0), (9, 0)),
                                                        ('SPAN', (10, 0), (-1, 0)),
        #('SPAN', (0, 0), (1, 0)), ('SPAN', (2, 0), (10, 0)), ('SPAN', (11, 0), (-1, 0)),
                                                        ('FACENAME', (9, 0), (-1, 0), 'helvetica-bold'),
                                                        ('FONTSIZE', (9, 0), (-1, 0), 12),                                                                 
                                                        
                                                        ('SPAN', (0, 1), (-1, 1)),
                                                        ('ALIGN', (0, 0), (-1, 2), 'CENTER'),
                                                        ('VALIGN', (0, 0), (-1, 2), 'TOP'),

                                                        ('BOX', (0, 2), (-1, 4), 0.5, colors.black),
                                                        ('VALIGN', (0, 2), (-1, 3), 'TOP'),
                                                        ('ALIGN', (0, 2), (-1, 3), 'LEFT'),
                                                        ('BACKGROUND', (0, 2), (-1, 4), '#DBDBDB'),
                                                        ('FONTSIZE', (0, 2), (-1, 5), 8),
                                                        # ('TOPPADDING', (0, 2), (-1, 5), 10),
                                                        # ('BOTTOMPADDING', (0, 2), (-1, 5), 10),
                                                        ('SPAN', (0, 2), (1, 2)),
                                                        ('SPAN', (2, 2), (3, 2)),
                                                        
                                                        ('SPAN', (0, 3), (1, 3)),
                                                        ('SPAN', (2, 3), (3, 3)),
                                                        
                                                        #('SPAN', (0, 4), (1, 4)),
                                                        #('SPAN', (2, 4), (3, 4)),

                                                        ('SPAN', (4, 2), (5, 2)),
                                                        ('SPAN', (6, 2), (7, 2)),
                                                        ('SPAN', (4, 3), (5, 3)),
                                                        ('SPAN', (6, 3), (7, 3)),
                                                        #('SPAN', (4, 4), (5, 4)),
                                                        #('SPAN', (6, 4), (7, 4)),

                                                        ('GRID', (0, 4), (-1, -1), 0.5, colors.black),

                                                        ('VALIGN', (0, 4), (-1, 6), 'MIDDLE'),
                                                        ('ALIGN', (0, 4), (-1, 6), 'CENTER'),
                                                        ('FONTSIZE', (0, 4), (-1, 6), 8),
                                                        
                                                        ])
        
        elements.append(t)

        def create_canvas(*args, **kwargs):
            return PageNumCanvas(*args, **kwargs)

        doc.build(elements, canvasmaker=create_canvas)
