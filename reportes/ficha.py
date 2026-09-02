import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from utils.pdf_utils import PageNumCanvas
from db.query import reportes, mostrar_d_personal, reportes_sobrantes, datos_iniciales

def iniciar_reporte(n_acta, direccion, pinv, Ndni, equi, valor, fecha=None, ndeacta=None):
        fecha = fecha
        ndeacta = ndeacta
        datos_ini = datos_iniciales()
        # print(datos_ini)

        r = mostrar_d_personal(n_acta)
        v1 = r[0][0]
        v2 = r[0][1]
        v3 = r[0][2]
        v4 = r[0][3]
        v5 = r[0][4]
        v6 = r[0][5]

        j = str(v1) + " " + str(v2) + " " + "AREA " + str(v3) + " " + "OFICINA " + str(v4)

        pdf_name = "FICHA "+str(j)+".pdf"
        pathpdf = os.path.join(direccion, pdf_name)

        doc = SimpleDocTemplate(pathpdf, pagesize=landscape(A4),
                                rightMargin=40, leftMargin=40,
                                topMargin=20, bottomMargin=50)
        
        elements = []

        t11 = [] 
        t22 = [] 
        # Titulos
        estilos = getSampleStyleSheet()
        # Titulo 1
        h1 = ParagraphStyle(name='Heading2', fontSize=10, alignment=1, fontName = 'HELVETICA-BOLD')

        titulo1 = Paragraph('FICHA DE LEVANTAMIENTO DE INFORMACIÓN',h1)
        t_estilo2 = estilos['Heading2']
        t_estilo2.alignment = 1
        t_estilo2.fontSize = 10
        t_estilo2.spaceAfter = 1
        t_estilo2.spaceBefore = 1
        titulo2 = Paragraph(f'INVENTARIO PATRIMONIAL AL '+str(datos_ini[3]), t_estilo2)

        test1 = ""
#        acta = "ACTA NRO: " + str(v1)
        acta = "FICHA  " + str(ndeacta).zfill(4)
        # acta = ""

        t11.append(test1)
        t11.append(test1)
        t11.append(titulo1)
        t11.append(test1)
        t11.append(test1)
        t11.append(test1)
        t11.append(test1)
        t11.append(test1)
        t11.append(test1)
        t11.append(test1)
        t11.append(test1)
        t11.append(acta)

        t22.append(titulo2)

        x = reportes(n_acta, 2)
        # print(x)
        sob = reportes_sobrantes(n_acta)

        p1 = ParagraphStyle(name='Normal', fontSize=7, leading = 8)
        p2 = ParagraphStyle(name='Normal', fontSize=7, leading = 8, alignment=1)
        
        # Crear una lista para almacenar los datos de la tabla
        table_data = []

        # Iterar sobre las filas de la consulta
        for row in x:
            # Crear una lista para almacenar las celdas de la fila
            row_data = []
            for index, cell in enumerate(row):
                #print(index)
                if index == 10 or index == 11:
                    row_data.append(Paragraph(str(cell), p2))
                else:
                    row_data.append(Paragraph(str(cell), p1))
            table_data.append(row_data)

        if sob:
            title_row = [Paragraph("", p1) for j in range(len(sob[0]))]
            title_row[1] = Paragraph("<b>SOBRANTES</b>", p1)
            table_data.append(title_row)

            for row in sob:
                row_data = []
                for index, cell in enumerate(row):
                    if index == 10 or index == 11:
                        row_data.append(Paragraph(str(cell), p2))
                    else:
                        row_data.append(Paragraph(str(cell), p1))
                table_data.append(row_data)

        # I = Image('img/Firmas.PNG', width=600, height=130)

        title_row1 = [Paragraph("""(1) Uso(U), Desuso(D)<br/>
                                    (2) El estado es cosignado en base a la siguiente escala: Bueno, Regular, Malo, Chatarra y RAEE. En caso de semovientes, utilizar escala de acuerdo a su naturaleza.<br/>
                                    <b><u>CONSIDERACIONES:</u></b><br/>
                                    - El usuario declara haber mostrado todos los bienes muebles que se encuentran bajo su responsabilidad y no contar con mas bienes muebles materia de inventario<br/>
                                    - El usuario es responsable de la permanencia y conservacion de cada uno de los muebles descritos, recomendandose tomar las precausiones del caso para evitar sustracciones, deteriodos, etc.<br/>
                                    - Cualquier necesidad de desplazamiento del bien mueble dentro o fuera del local de la Entidad, es previamente comunicado al encargado de la OCP.
                                """)]

        table_data.append(title_row1)

        entidad = datos_ini[1]
        ruc = "20608662902"
        inventario = pinv
        local = str(v2)
        area = str(v3)
        oficina = str(v4)
        responsable = str(v6)
        dni = str(v5)
        ufisica = local + " - " + oficina
        equipo = equi
        dniinventariador = Ndni

        # Datos del Usuario
        h1 = ParagraphStyle(name='normal', fontSize=7)
        h2 = ParagraphStyle(name='normal', fontSize=7, alignment=1, leading=7)

        t0 = (Paragraph(entidad, h1), Paragraph("", h1),Paragraph("", h1), Paragraph("", h1),Paragraph("", h1), Paragraph("FECHA: "+fecha, h1),)
        t1 = (Paragraph("<b><u>USUARIO</u></b>", h1), Paragraph("", h1),Paragraph("", h1), Paragraph("", h1),Paragraph("", h1), Paragraph("<b><u>PERSONAL INVENTARIADOR</u></b>", h1),Paragraph("", h1),Paragraph("", h1))
        t2 = (Paragraph(responsable+" - "+dni, h1), Paragraph("", h1),Paragraph("", h1), Paragraph("", h1),Paragraph("", h1), Paragraph(inventario+" - "+dniinventariador, h1),)
        t3 = (Paragraph("ÓRGANO O UNIDAD ORGÁNICA: "+area, h1), Paragraph("", h1),Paragraph("", h1), Paragraph("", h1),Paragraph("", h1), Paragraph("EQUIPO DE TRABAJO: "+equipo, h1),)
        t4 = (Paragraph("UBICACIÓN FÍSICA: "+ufisica, h1),)
        t5 = (Paragraph("TIPO DE VERIFICACIÓN: FÍSICA  (___) DIGITAL  (___)", h1),)
        t6 = (Paragraph("N° de orden", h1), Paragraph("DESCRIPCIÓN", h2),)

        enc= ('N° de\norden', 'Código\nPatrimonial', 'Denominación', 'Detalles tecnicos','','','','','','Detalles tecnicos', 'Situa\nción(1)', 'Estado de\nconserv. (2)', 'Observaciones')
        
        table_data.insert(0, enc)
        # table_data.insert(0, lista_pruebav)
        table_data.insert(0, t6)
        table_data.insert(0, t5)
        table_data.insert(0, t4)
        table_data.insert(0, t3)
        table_data.insert(0, t2)
        table_data.insert(0, t1)
        table_data.insert(0, t0)
        table_data.insert(0, t22)
        table_data.insert(0, t11)
        
        tabla = list(table_data)

        colWidths = [25, 60, 150, 70, 70, 45, 50, 70, 50, 40, 35, 45, 50]
        t=Table(tabla, colWidths, repeatRows = 10, style=[
                                        # titulo FORMATO...
                                        ('SPAN', (0, 0), (1, 0)), ('SPAN', (2, 0), (10, 0)), ('SPAN', (11, 0), (-1, 0)),

                                        ('SPAN', (0, 2), (4, 2)), ('SPAN', (5, 2), (8, 2)), ('SPAN', (9, 2), (12, 2)),
                                        ('SPAN', (0, 3), (4, 3)), ('SPAN', (5, 3), (12, 3)),
                                        ('SPAN', (0, 4), (4, 4)), ('SPAN', (5, 4), (12, 4)),
                                        ('SPAN', (0, 5), (4, 5)), ('SPAN', (5, 5), (12, 5)),
                                        ('SPAN', (0, 6), (12, 6)),
                                        ('SPAN', (1, 7), (12, 7)),
                                        ('SPAN', (1, 8), (12, 8)),
                                        # Número de orden
                                        ('SPAN', (0, 8), (0, 9)),
                                        
                                        ('SPAN', (0, 7), (-1, 7)),

                                        # número de acta
                                        ('FACENAME', (9, 0), (-1, 0), 'helvetica-bold'),
                                        ('FONTSIZE', (9, 0), (-1, 0), 12),                                                                 
                                        # titulo INVENTARIO...
                                        ('SPAN', (0, 1), (-1, 1)),
                                        # formato de los 2 titulos
                                        ('ALIGN', (0, 0), (-1, 2), 'CENTER'),
                                        ('VALIGN', (0, 0), (-1, 2), 'TOP'),
                                        ('FACENAME', (0, 2), (0, 2), 'helvetica-bold'),
                                        # ('FONTSIZE', (0, 2), (0, 2), 12),                                        
                                        # formato de los datos USUARIO...
                                        ('VALIGN', (0, 2), (-1, 6), 'TOP'),
                                        ('ALIGN', (0, 2), (-1, 6), 'LEFT'),

                                        # Agrupar para detalles tecnicos

                                        #('SPAN', (3, 9), (8, len(table_data)-2)),

                                        *[
                                            ('SPAN', (3, i), (9, i)) for i in range(9, len(table_data)-1)
                                        ],


                                        # agrupo celdas de los datos de USUARIO Y PERSONAL INVENTARIADOR
                                        # ('SPAN', (0, 2), (1, 2)),
                                        # ('SPAN', (2, 2), (3, 2)),
                                        # ('SPAN', (0, 3), (1, 3)),
                                        # ('SPAN', (2, 3), (3, 3)),
                                        # ('SPAN', (0, 4), (1, 4)),
                                        # ('SPAN', (2, 4), (3, 4)),

                                        # ('SPAN', (4, 2), (5, 2)),
                                        # ('SPAN', (6, 2), (7, 2)),
                                        # ('SPAN', (4, 3), (5, 3)),
                                        # ('SPAN', (6, 3), (7, 3)),
                                        # ('SPAN', (4, 4), (5, 4)),
                                        # ('SPAN', (6, 4), (7, 4)),

                                        ('FONTSIZE', (0, 2), (-1, 6), 7),
                                        # pone bordes desde el encabezado hasta el final de la tabla
                                        # ('GRID', (0, 7), (-1, -2), 0.5, colors.black),
                                        ('GRID', (0, 8), (-1, -2), 0.5, colors.black),
                                        # encabezados N° DE ORDEN...
                                        ('BACKGROUND', (0, 8), (-1, 8), '#DBDBDB'),
                                        ('BACKGROUND', (0, 9), (-1, 9), '#DBDBDB'),
                                        ('VALIGN', (0, 8), (-1, 8), 'MIDDLE'),
                                        ('ALIGN', (0, 9), (-1, 9), 'CENTER'),
                                        ('FONTSIZE', (0, 8), (-1, 8), 7),
                                        ('FONTSIZE', (0, 9), (-1, 9), 7),
                                        # cuerpo de la tabla
                                        # define el tamaño fuente y horientacion del cuerpo de la tabla
                                    # ('FONTSIZE', (0, 8), (-1, -1), 7),
                                    # ('ALIGN', (0, 8), (-1, -1), 'LEFT'),
                                        # centra la columna 11 ESTADO...
                                    # ('ALIGN', (11, 8), (11, -1), 'CENTER'),
                                    # ('ALIGN', (10, 8), (10, -1), 'CENTER'),
                                        # alinea toda la tabla
                                        ('VALIGN', (0, 9), (-1, -1), 'MIDDLE'),
                                        ('SPAN', (0, len(table_data)-1), (-1, len(table_data)-1)),

                                        ])

        elements.append(t)

        # Insertar espacio para firmas al final
        firma_data = [
            ["__________________________", "__________________________"],
            ["Usuario", "Personal Inventariador"]
        ]

        firma_table = Table(firma_data, colWidths=[250, 250])
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Alinea los textos en la parte superior de las celdas
            ('TOPPADDING', (0, 0), (-1, 0), 100),  # Espacio extra arriba de las líneas de firma
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),  # Eliminar espacio adicional debajo de la firma
            ('BOTTOMPADDING', (0, 0), (-1, 1), 0),  # Espacio entre la línea y la descripción
            ('TOPPADDING', (0, 1), (-1, 1), 0),  # Quita espacio adicional entre la línea y la descripción
        ]))

        # Añadir la tabla de firmas al final de los elementos
        elements.append(firma_table)

        def create_canvas(*args, **kwargs):
            return PageNumCanvas(*args, fecha=fecha, **kwargs)

        # doc.build(elements, canvasmaker=PageNumCanvas)
        doc.build(elements, canvasmaker=create_canvas)