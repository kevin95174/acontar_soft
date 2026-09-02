import os
import win32api
from tkinter import messagebox as mb
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from db.query import datos_iniciales
from utils.config_utils import ConfigUtils

def build_label_sobrante(acta, local, area, oficina, deno, valor):

        config_instance = ConfigUtils()
        direccion = config_instance.load_config()

        datos_ini = datos_iniciales()

        den = deno
        # item = str(j[0][0])
        inv = 'INV - ' + str(datos_ini[2])
        bsob = "BIEN SOBRANTE"
        ubi = local + " "+ area + " "+ oficina
        entidad = datos_ini[1]

        # pdf = str(j[0][0])+"_"+ubi
        pdf = str("sobrante")+"_"+ubi
        pdf_name= str(pdf)+".pdf"
        pathinit = 'labels/sobrantes/'
        pathpdf = os.path.join(pathinit, pdf_name)

        c = canvas.Canvas(pathpdf)
        c.setPageSize((5*cm, 2.5*cm))

        s1 = ParagraphStyle(name='Body', 
                        fontSize=5, 
                        alignment=1, 
                        # backColor = '#FFFF00',
                        borderPadding= 1,
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        leading = 5)

        s2 = ParagraphStyle(name='Body', 
                        fontSize=10,
                        fontName = 'Helvetica-Bold', 
                        alignment=1, 
                        # backColor = '#FFFF00',
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        leading = 7)

        s3 = ParagraphStyle(name='Body', 
                        fontSize=8,
                        fontName = 'Helvetica-Bold', 
                        alignment=1, 
                        # backColor = '#ffffff',
                        leading = 7)

        s4 = ParagraphStyle(name='Body', 
                        fontSize=8,
                        fontName = 'Helvetica-Bold', 
                        alignment=1, 
                        backColor = '#ffffff',
                        leading = 7)

        s5 = ParagraphStyle(name='Body', 
                        fontSize=5,
                        fontName = 'Helvetica', 
                        alignment=0, 
                        # backColor = '#ffffff',
                        leading = 5)
                        
        p1 = Paragraph(den, s1)
        # p2 = Paragraph(item, s2)
        p3 = Paragraph(inv, s3)
        p4 = Paragraph(bsob, s4)
        p5 = Paragraph(ubi, s5)
        p6 = Paragraph(entidad, s3)

        logo = ImageReader(direccion[0])
        c.drawImage(logo, 1*mm, 17*mm, width=18, height=20)

        p1.wrapOn(c, 49*mm, 5*mm)
        p1.drawOn(c, 1, 1)

        # p2.wrapOn(c, 12*mm, 8*mm)
        # p2.drawOn(c, 4.5*mm, 12.5*mm)

        p3.wrapOn(c, 15*mm, 5*mm)
        p3.drawOn(c, 32*mm, 22*mm)

        p4.wrapOn(c, 37*mm, 5.5*mm)
        p4.drawOn(c, 15*mm, 12.5*mm)

        p5.wrapOn(c, 49*mm, 5*mm)
        p5.drawOn(c, 0.5*mm, 4*mm)

        p6.wrapOn(c, 30*mm, 5*mm)
        p6.drawOn(c, 5*mm, 22*mm)

        c.showPage()
        
        try:
                c.save()
                if valor == 1:
                        try:
                                win32api.ShellExecute (0, "print", pdf_name, None, "labels/sobrantes/", 0)
                        except:
                                win32api.ShellExecute (0, "print", pdf_name, None, "labels/sobrantes", 0)
        except:
                mb.showerror(message="""Ha ocurrido un error, revise si el PDF este abierto o que la impresora este bien configurada""", title="Error")