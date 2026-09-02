import os
import io
import win32api
from tkinter import messagebox as mb
from barcode import Code128
from barcode.writer import ImageWriter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from db.query import data_label, data_label_ubi, datos_iniciales
from utils.config_utils import ConfigUtils

def build_label(valor, codigo, codact):
        
        config_instance = ConfigUtils()
        direccion = config_instance.load_config()

        datos_ini = datos_iniciales()

        r = data_label(codigo)
        # print(r)
        j = data_label_ubi(codact)
        den = str(r[0][2])
        codint = str(r[0][0])
        inv = 'INV-' + str(datos_ini[2])
        codpatr = str(r[0][1])
        ubi = str(j[0][0])
        entidad = datos_ini[1]

        pdf = str(r[0][0])+"_"+str(r[0][1])+"_"+str(r[0][3])
        pdf_name= str(pdf)+".pdf"
        pathinit = 'labels/'
        pathpdf = os.path.join(pathinit, pdf_name)

        c = canvas.Canvas(pathpdf)
        c.setPageSize((5*cm, 2.5*cm))

        fp = io.BytesIO()
        options = {'write_text': False}
        Code128 (codpatr, writer=ImageWriter()).write(fp, options=options)

        fp.seek(0)

        formato_denominacion = ParagraphStyle(name='Body', 
                        fontSize=5, 
                        alignment=0, 
                        # backColor = '#FFFF00',
                        borderPadding= 1,
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        leading = 5)

        formato_codigo = ParagraphStyle(name='Body', 
                        fontSize=12,
                        fontName = 'Helvetica-Bold', 
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        alignment=1, 
                        leading = 7)

        formato_inventario = ParagraphStyle(name='Body', 
                        fontSize=6,
                        fontName = 'Helvetica-Bold', 
                        alignment=1,
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        # backColor = '#ffffff',
                        # rotation=90,
                        leading = 7)

        formato_cod_patrimonial = ParagraphStyle(name='Body', 
                        fontSize=10,
                        fontName = 'Helvetica-Bold', 
                        alignment=1,
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        leading = 7)

        formato_ubicacion = ParagraphStyle(name='Body', 
                        fontSize=4,
                        fontName = 'Helvetica', 
                        alignment=0, 
                        # backColor = '#ffffff',
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        leading = 5)

        formato_entid = ParagraphStyle(name='Body', 
                        fontSize=6,
                        fontName = 'Helvetica', 
                        alignment=0, 
                        # backColor = '#ffffff',
                        leading = 5)

        p_denom = Paragraph(den, formato_denominacion)
        p_cod_i = Paragraph(codint, formato_codigo)
        p_inven = Paragraph(inv, formato_inventario)
        p_cod_p = Paragraph(codpatr, formato_cod_patrimonial)
        p_ubica = Paragraph(ubi, formato_ubicacion)
        p_entid = Paragraph(entidad, formato_entid)

        # codigo de barras
        c.drawImage(ImageReader(fp), 10*mm, 10*mm, width=35*mm, height=5*mm)

        # logo = ImageReader("img/pro.jpg")
        logo = ImageReader(direccion[0])
        c.drawImage(logo, 1*mm, 8*mm, width=30, height=30)

        # wrapOn Tamaño de la caja
        p_denom.wrapOn(c, 33*mm, 10*mm)
        # drawOn Posicion de la caja
        p_denom.drawOn(c, 13.5*mm, c._pagesize[1] - 4*mm - p_denom.height)

        p_cod_i.wrapOn(c, 12*mm, 8*mm)
        p_cod_i.drawOn(c, 1*mm, 5*mm)

        p_inven.wrapOn(c, 1*mm, 10*mm)
        p_inven.drawOn(c, 48*mm, 3*mm)

        p_cod_p.wrapOn(c, 28*mm, 5.8*mm)
        p_cod_p.drawOn(c, 13.5*mm, 7.5*mm)

        p_ubica.wrapOn(c, 33*mm, 10*mm)
        p_ubica.drawOn(c, 13.5*mm, c._pagesize[1] - 20*mm - p_ubica.height)

        p_entid.wrapOn(c, 45*mm, 5*mm)
        p_entid.drawOn(c, 1*mm, 22*mm)

        c.showPage()
        try:
                c.save()
                if valor == 1:
                        try:
                                win32api.ShellExecute (0, "print", pdf_name, None, "labels/", 0)
                        except:
                                win32api.ShellExecute (0, "print", pdf_name, None, "labels", 0)
        except:
                mb.showerror(message="""Ha ocurrido un error, revise si el PDF este abierto o que la impresora este bien configurada""", title="Error")

        return pathpdf

