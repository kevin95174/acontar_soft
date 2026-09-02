import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import ParagraphStyle
from utils.pdf_utils import PageNumCanvas
from db.query import selec_vehiculos, selec_vehiculos_tab1

def iniciar_reporte(codigo, direccion):

        j = "FICHA_VEHICULAR_"+str(codigo)
        pdf_name = str(j)+".pdf"

        pathpdf = os.path.join(direccion, pdf_name)

        doc = SimpleDocTemplate(pathpdf, pagesize=A4,
                                rightMargin=40, leftMargin=40,
                                topMargin=20, bottomMargin=50)
        
        elements = []

        rr = selec_vehiculos_tab1(codigo)
        #sql = Entidad, DenBien, NroPlaca, Carroceria, Marca, Modelo, Categoria, NroChasis, NroEjes,
        #        NroMotor, NroSerie, AFab, Color, Combustible, Transm, Cilindrada, Kilometraje,
        #        NroTarjVehi
        
        jj = selec_vehiculos(codigo)
        #sql = f"""SELECT SistMotor, SistFrenos, SistRefri, SistElect, SistTrans, SistDirec, SistSusp,
        #            Crreria, Accesorios, OtrCarac, Apreciacion FROM vehiculos WHERE CodPat = '{codigo}' OR CodInt = '{codigo}' """
        
        h1 = ParagraphStyle(name='Heading1', fontSize=12, alignment=1, fontName = 'HELVETICA-BOLD')

        tabla = [[Paragraph('FICHA TÉCNICA DEL VEHÍCULO', h1)],
                [Paragraph('<b>Entidad u Organización de la Entidad</b>'), Paragraph(rr[0][0]), Paragraph('<b>Categoría</b>'), Paragraph(rr[0][6]), Paragraph('<b>Color</b>'), Paragraph(rr[0][12])],
                [Paragraph('<b>Denominación</b>'), Paragraph(rr[0][1]), Paragraph('<b>Nº de chasis (VIN)</b>'), Paragraph(rr[0][7]), Paragraph('<b>Combustible</b>'), Paragraph(rr[0][13])],
                [Paragraph('<b>N° Placa vehicular</b>'), Paragraph(rr[0][2]), Paragraph('<b>Nº de ejes</b>'), Paragraph(rr[0][8]), Paragraph('<b>Transmisión</b>'), Paragraph(rr[0][14])],
                [Paragraph('<b>Carroceria</b>'), Paragraph(rr[0][3]), Paragraph('<b>Nº de motor</b>'), Paragraph(rr[0][9]), Paragraph('<b>Cilindrada</b>'), Paragraph(rr[0][15])],
                [Paragraph('<b>Modelo</b>'), Paragraph(rr[0][4]), Paragraph('<b>Nº de serie</b>'), Paragraph(rr[0][10]), Paragraph('<b>Kilometraje</b>'), Paragraph(rr[0][16])],
                [Paragraph('<b>Modelo</b>'), Paragraph(rr[0][5]), Paragraph('<b>Año de fabricación</b>'), Paragraph(rr[0][11]), Paragraph('N° de Tarjeta de Identificación Vehicular'), Paragraph(rr[0][17])],
                [Paragraph('Valor de tasación (S/) o valor neto (S/)'), '', '', 'S/35,000.00'],
                [Paragraph('<b>DESCRIPCIÓN</b>', h1), '', '', Paragraph('<b>APRECIACIÓN TÉCNICA DEL SISTEMA</b>', h1)],
                [Paragraph('<b>1. SISTEMA DE MOTOR</b>'), '', '', ''],
                [Paragraph('Cilindros<br/>Carburador / carter<br/>Distribuidor / bomba de inyección<br/>Bomba de gasolina<br/>Purificador de aire'), '', '', Paragraph(jj[0][0])],
                [Paragraph('<b>2. SISTEMA DE FRENOS</b>'), '', '', ''],
                [Paragraph('Bomba de frenos<br/>Zapatas y tambores<br/>Discos y pastillas'), '', '', Paragraph(jj[0][1])],
                [Paragraph('<b>3. SISTEMA DE REFRIGERACIÓN</b>'), '', '', ''],
                [Paragraph('Radiador<br/>Ventilador<br/>Bomba de Agua'), '', '', Paragraph(jj[0][2])],
                [Paragraph('<b>4. SISTEMA ELÉCTRICO</b>'), '', '', ''],
                [Paragraph('Motor de arranque<br/>Batería<br/>Alternador<br/>Bobina<br/>Relay de alternador<br/>Faros delanteros<br/>Direccionales delanteros<br/>Luces posteriores<br/>Direccionales posteriores<br/>Auto radio<br/>Parlantes<br/>Claxon<br/>Circuito de luces (faros, cableados)'), '', '', Paragraph(jj[0][3])],
                [Paragraph('<b>5. SISTEMA DE TRANSMISIÓN</b>'), '', '', ''],
                [Paragraph('Caja de cambios<br/>Bomba de embrague<br/>Caja de transferencia<br/>Diferencial trasero<br/>Diferencial delantero (4x4)'), '', '', Paragraph(jj[0][4])],
                [Paragraph('<b>6. SISTEMA DE DIRECCIÓN</b>'), '', '', ''],
                [Paragraph('Volante<br/>Caña de dirección<br/>Cremallera<br/>Rótulas'), '', '', Paragraph(jj[0][5])],
                [Paragraph('<b>7. SISTEMA DE SUSPENSIÓ</b>'), '', '', ''],
                [Paragraph('Amortiguadores / muelles<br/>Barra de torsión<br/>Barra estabilizadora<br/>Llantas'), '', '', Paragraph(jj[0][6])],
                [Paragraph('<b>8. CARROCERÍA</b>'), '', '', ''],
                [Paragraph('Capot del motor<br/>Capot de maletera<br/>Parachoques delantero<br/>Parachoques posterior<br/>Lunas laterales<br/>Lunas cortaviento<br/>Parabrisas delantero<br/>Parabrisas posterior<br/>Tanque de combustible<br/>Puertas<br/>Asientos'), '', '', Paragraph(jj[0][7])],
                [Paragraph('<b>9. ACCESORIOS</b>'), '', '', ''],
                [Paragraph('Aire acondicionado<br/>Alarma<br/>Plumillas<br/>Espejos<br/>Cinturones de seguridad<br/>Antena'), '', '', Paragraph(jj[0][8])],
                [Paragraph('<b>10. OTRAS CARACTERÍSTICAS RELEVANTES</b>'), '', '', Paragraph(jj[0][9])],
                [Paragraph('<b>11. APRECIACIÓN TÉCNICA GENERAL</b>'), '', '', Paragraph(jj[0][10])]
                ]

        colWidths = [80, 80, 80, 80, 80, 80]

        rowHeights = [55] + [None] * (len(tabla) - 1)

        t=Table(tabla, colWidths, rowHeights=rowHeights, repeatRows=1, style=[
                                        # titulo FORMATO...
                                        ('SPAN', (0, 0), (-1, 0)),
                                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),

                                        ('SPAN', (0, 7), (2, 7)),
                                        ('SPAN', (3, 7), (5, 7)),

                                        ('SPAN', (0, 8), (2, 8)),
                                        ('SPAN', (3, 8), (5, 8)),

                                        ('SPAN', (0, 9), (2, 9)),
                                        ('SPAN', (3, 9), (5, 9)),

                                        ('SPAN', (0, 10), (2, 10)),
                                        ('SPAN', (3, 10), (5, 10)),

                                        ('SPAN', (0, 11), (2, 11)),
                                        ('SPAN', (3, 11), (5, 11)),

                                        ('SPAN', (0, 12), (2, 12)),
                                        ('SPAN', (3, 12), (5, 12)),

                                        ('SPAN', (0, 13), (2, 13)),
                                        ('SPAN', (3, 13), (5, 13)),

                                        ('SPAN', (0, 14), (2, 14)),
                                        ('SPAN', (3, 14), (5, 14)),

                                        ('SPAN', (0, 15), (2, 15)),
                                        ('SPAN', (3, 15), (5, 15)),

                                        ('SPAN', (0, 16), (2, 16)),
                                        ('SPAN', (3, 16), (5, 16)),

                                        ('SPAN', (0, 17), (2, 17)),
                                        ('SPAN', (3, 17), (5, 17)),

                                        ('SPAN', (0, 18), (2, 18)),
                                        ('SPAN', (3, 18), (5, 18)),
                                        
                                        ('SPAN', (0, 19), (2, 19)),
                                        ('SPAN', (3, 19), (5, 19)),
                                        
                                        ('SPAN', (0, 20), (2, 20)),
                                        ('SPAN', (3, 20), (5, 20)),
                                        
                                        ('SPAN', (0, 21), (2, 21)),
                                        ('SPAN', (3, 21), (5, 21)),
                                        
                                        ('SPAN', (0, 22), (2, 22)),
                                        ('SPAN', (3, 22), (5, 22)),
                                        
                                        ('SPAN', (0, 23), (2, 23)),
                                        ('SPAN', (3, 23), (5, 23)),
                                        
                                        ('SPAN', (0, 24), (2, 24)),
                                        ('SPAN', (3, 24), (5, 24)),
                                        
                                        ('SPAN', (0, 25), (2, 25)),
                                        ('SPAN', (3, 25), (5, 25)),
                                        
                                        ('SPAN', (0, 26), (2, 26)),
                                        ('SPAN', (3, 26), (5, 26)),
                                        
                                        ('SPAN', (0, 27), (2, 27)),
                                        ('SPAN', (3, 27), (5, 27)),
                                        
                                        ('SPAN', (0, 28), (2, 28)),
                                        ('SPAN', (3, 28), (5, 28)),
                                        

                                        ('GRID', (0, 1), (-1, -1), 0.5, colors.black),])
        
        elements.append(t)
        
        def create_canvas(*args, **kwargs):
            return PageNumCanvas(*args, orientacion=1, **kwargs)
        
        # write the document to disk
        doc.build(elements, canvasmaker=create_canvas)
        # print("Funciono 1 vez")
