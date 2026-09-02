import os
from datetime import date
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from tkinter import messagebox as mb
from db.query import reporte_faltantes, mostrar_d_personal


class PageNumCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):
        """Constructor"""
        canvas.Canvas.__init__(self, *args, **kwargs)
        
        self.pages = []

    def showPage(self):
        """
        On a page break, add information to the list
        """
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):

        page_count = len(self.pages)
        
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)
            
        canvas.Canvas.save(self)
        
    def draw_page_number(self, page_count):

        page = "Página %s de %s" % (self._pageNumber, page_count)
        self.setFont("Helvetica", 9)
        self.drawRightString(800, 20, page)
        today = date.today()
        today_ = "Generado: "+today.strftime("%d/%m/%Y")
        self.setFont("Helvetica", 9)
        self.drawRightString(120, 20, str(today_))

def iniciar_reporte(n_acta):
        r = mostrar_d_personal(n_acta)
        v1 = r[0][0]
        v2 = r[0][1]
        v3 = r[0][2]
        v4 = r[0][3]
        v5 = r[0][4]
        v6 = r[0][5]

        j = "Acta " + str(v1) + " " + str(v2) + " " + "AREA " + str(v3) + " " + "OFICINA " + str(v4)
        pdf_name = "Faltantes_"+str(j)+".pdf"
        pathinit = 'report_actas/reporte_faltantes/'
        pathpdf = os.path.join(pathinit, pdf_name)

        doc = SimpleDocTemplate(pathpdf, pagesize=landscape(A4),
                                rightMargin=40, leftMargin=40,
                                topMargin=20, bottomMargin=50)
        
        elements = []

        t11 = [] 
        t22 = [] 
        # Titulos
        estilos = getSampleStyleSheet()
        # Titulo 1
        h1 = ParagraphStyle(name='Heading1', fontSize=15, alignment=0, fontName = 'HELVETICA-BOLD')
        titulo1 = Paragraph('<u>Reporte bienes faltantes</u>',h1)
        # Titulo 2
        t_estilo2 = estilos['Heading2']
        t_estilo2.alignment = 1
        t_estilo2.fontSize = 15
        t_estilo2.spaceAfter = 10
        t_estilo2.spaceBefore = 1
        titulo2 = Paragraph('', t_estilo2)

        test1 = ""
        test2 = ""
        test3 = ""
        test4 = "ACTA NRO: " + str(v1)

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

        entidad = "Oficina Regional Altiplano Puno"
        ruc = "2036418036"
        inventario = "2022"
        local = str(v2)
        area = str(v3)
        oficina = str(v4)
        responsable = str(v6)
        dni = str(v5)
        # Datos del Usuario


        t1 = ("Entidad", "",": "+entidad, "","RUC", "",": "+ruc, "","Inventario", ": "+inventario)
        t2 = ("Local", "",": "+local, "","Area:", "",": "+area, "","Oficina:", ": "+oficina)
        t3 = ("", "","","", "","", "","","")
        enc=  ('Item','Codigo\nInterno', 'Codigo\nPatrimonial', 'Denominación', 'Estado', 'Dimensión', 
                    'Marca', 'Modelo', 'Serie', 'Color', 'Valor', 'Obs')
        
        
        
        x.insert(0, enc)
        x.insert(0, t3)
        x.insert(0, t2)
        x.insert(0, t1)
        x.insert(0, t22)
        x.insert(0, t11)
        

        tabla = list(x)
        # print(sob)

        rowHeights = []
        rh  = len(x)

        for i in range(rh-6):
            i=10
            rowHeights.append(i)

        # cabecera
        rowHeights.insert(0, 25)
        # responsable dni
        rowHeights.insert(0, 0)
        # local area oficina
        rowHeights.insert(0, 18)
        # entidad ruc inventario
        rowHeights.insert(0, 18)
        # formato de levantamiento
        rowHeights.insert(0, 22)
        # acta de invesntario
        rowHeights.insert(0, 25)


        colWidths = [30, 40, 60, 150, 30, 60, 80, 80, 80, 50, 50, 50]
        t=Table(tabla, colWidths, rowHeights, repeatRows =6, style=[                                    
                                                        # ('SPAN', (0, 0), (2, 0)),
                                                        ('SPAN', (0, 0), (8, 0)),
                                                        ('SPAN', (9, 0), (-1, 0)),
                                                        ('FACENAME', (9, 0), (-1, 0), 'helvetica-bold'),
                                                        ('FONTSIZE', (9, 0), (-1, 0), 12),                                                                 
                                                        
                                                        ('SPAN', (0, 1), (-1, 1)),
                                                        ('ALIGN', (0, 0), (-1, 2), 'CENTER'),
                                                        ('VALIGN', (0, 0), (-1, 2), 'TOP'),

                                                        ('BOX', (0, 2), (-1, 5), 0.5, colors.black),
                                                        ('VALIGN', (0, 2), (-1, 3), 'TOP'),
                                                        ('ALIGN', (0, 2), (-1, 3), 'LEFT'),
                                                        ('BACKGROUND', (0, 2), (-1, 5), '#8ff0ff'),
                                                        ('FONTSIZE', (0, 2), (-1, 5), 8),
                                                        # ('TOPPADDING', (0, 2), (-1, 5), 10),
                                                        # ('BOTTOMPADDING', (0, 2), (-1, 5), 10),
                                                        ('SPAN', (0, 2), (1, 2)),
                                                        ('SPAN', (2, 2), (3, 2)),
                                                        ('SPAN', (0, 3), (1, 3)),
                                                        ('SPAN', (2, 3), (3, 3)),
                                                        ('SPAN', (0, 4), (1, 4)),
                                                        ('SPAN', (2, 4), (3, 4)),

                                                        ('SPAN', (4, 2), (5, 2)),
                                                        ('SPAN', (6, 2), (7, 2)),
                                                        ('SPAN', (4, 3), (5, 3)),
                                                        ('SPAN', (6, 3), (7, 3)),
                                                        ('SPAN', (4, 4), (5, 4)),
                                                        ('SPAN', (6, 4), (7, 4)),

                                                        ('GRID', (0, 5), (-1, -1), 0.5, colors.black),

                                                        ('VALIGN', (0, 5), (-1, 6), 'MIDDLE'),
                                                        ('ALIGN', (0, 5), (-1, 6), 'CENTER'),
                                                        ('FONTSIZE', (0, 5), (-1, 6), 8),
                                                        # ('TOPPADDING', (0, 3), (-1, 0), 10),
                                                        # ('BOTTOMPADDING', (0, 3), (-1, 0), 10),

                                                        ('FONTSIZE', (0, 6), (-1, -1), 7),
                                                        ('VALIGN', (0, 6), (-1, -1), 'TOP'),
                                                        ('ALIGN', (0, 6), (-1, -1), 'LEFT'),
                                                        ('ALIGN', (4, 6), (4, -1), 'CENTER'),
                                                        ('TOPPADDING', (0, 6), (-1, -1), 0),
                                                        ('BOTTOMPADDING', (0, 6), (-1, -1), 0),
                                                        ('LEFTPADDING', (0, 6), (-1, -1), 3)])
        
        elements.append(t)

        # elements.append(Paragraph('NOTA: Los responsables de la Toma del Inventario Fisico de bienes en representacion de la Oficina Regional Altiplano Puno - INPE, procedieron a realizar el levante del inventario de bienes de activo fijo'))
        # write the document to disk
        doc.build(elements, canvasmaker=PageNumCanvas)
        mb.showinfo(message="Generado con exito")
