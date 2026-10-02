import os
import io
import win32api
import qrcode
from PIL import Image
from tkinter import messagebox as mb
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from db.query import data_label, data_label_ubi, datos_iniciales
from utils.config_utils import ConfigUtils

# Resolución térmica estándar en impresoras de etiquetas.
PRINT_DPI = 203

# Configuración de fuente Roboto (con respaldo a Helvetica si no existen los archivos TTF)
FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONTS_DIR = os.path.join(_BASE_DIR, 'fonts')
_ROBOTO_REG_PATH = os.path.join(_FONTS_DIR, 'Roboto-Regular.ttf')
_ROBOTO_BOLD_PATH = os.path.join(_FONTS_DIR, 'Roboto-Bold.ttf')

if os.path.exists(_ROBOTO_REG_PATH) and os.path.exists(_ROBOTO_BOLD_PATH):
    try:
        if 'Roboto' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('Roboto', _ROBOTO_REG_PATH))
        if 'Roboto-Bold' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('Roboto-Bold', _ROBOTO_BOLD_PATH))
        FONT_REGULAR = 'Roboto'
        FONT_BOLD = 'Roboto-Bold'
    except Exception:
        pass

def build_label(valor, codigo, codact):
        
        config_instance = ConfigUtils()
        direccion = config_instance.load_config()

        datos_ini = datos_iniciales()

        r = data_label(codigo)
        # print(r)
        j = data_label_ubi(codact)
        den = str(r[0][2])
        codint = str(r[0][0])
        inv = 'INVENTARIO ' + str(datos_ini[2])
        codpatr = str(r[0][1])
        ubi = str(j[0][0])
        entidad = datos_ini[1]

        pdf = str(r[0][0])+"_"+str(r[0][1])+"_"+str(r[0][3])
        pdf_name= str(pdf)+".pdf"
        pathinit = 'labels/'
        pathpdf = os.path.join(pathinit, pdf_name)

        c = canvas.Canvas(pathpdf)
        c.setPageSize((5*cm, 2.5*cm))

        # El QR identifica el bien con ambos códigos para que la aplicación
        # pueda localizarlo aun si uno de ellos cambia de formato visual.
        qr_payload = codpatr
        qr_image = qrcode.make(qr_payload)
        qr_buffer = io.BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        formato_denominacion = ParagraphStyle(name='Body', 
                        fontSize=5, 
                        fontName = FONT_REGULAR,
                        alignment=0, 
                        # backColor = '#FFFF00',
                        borderPadding= 1,
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        leading = 5)

        formato_codigo = ParagraphStyle(name='Body', 
                        fontSize=11,
                        fontName = FONT_BOLD, 
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        alignment=0, 
                        leading = 7)

        formato_inventario = ParagraphStyle(name='Body', 
                        fontSize=6,
                        fontName = FONT_BOLD, 
                        alignment=2,
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        # backColor = '#ffffff',
                        # rotation=90,
                        charSpace=-5.0)

        formato_cod_patrimonial = ParagraphStyle(name='Body', 
                        fontSize=8,
                        fontName = FONT_BOLD, 
                        alignment=0,
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        leading = 7)

        formato_ubicacion = ParagraphStyle(name='Body', 
                        fontSize=4,
                        fontName = FONT_REGULAR, 
                        alignment=0, 
                        # backColor = '#ffffff',
                        # borderWidth = 0.25,
                        # borderColor = '#000000',
                        leading = 5)

        formato_entid = ParagraphStyle(name='Body', 
                        fontSize=5.5,
                        fontName = FONT_REGULAR, 
                        alignment=0, 
                        # backColor = '#ffffff',
                        )

        p_denom = Paragraph(den, formato_denominacion)
        p_cod_i = Paragraph(codint, formato_codigo)
        p_inven = Paragraph(inv, formato_inventario)
        p_cod_p = Paragraph(codpatr, formato_cod_patrimonial)
        p_ubica = Paragraph(ubi, formato_ubicacion)
        p_entid = Paragraph(entidad, formato_entid)

        # Código QR: se deja un borde blanco para facilitar su lectura al imprimir.
        c.drawImage(
                ImageReader(qr_buffer),
                31*mm, 4*mm, width=18*mm, height=18*mm, mask='auto')

        # logo = ImageReader("img/pro.jpg")
        # Rasterizar el logo a la densidad de impresión, conservando la caja
        # física actual (15 x 15 puntos) y su ubicación en la etiqueta.
        logo_width_pt = 15
        logo_height_pt = 15
        logo_width_px = round(logo_width_pt * PRINT_DPI / 72)
        logo_height_px = round(logo_height_pt * PRINT_DPI / 72)
        with Image.open(direccion[0]) as logo_source:
                logo = logo_source.convert("RGBA").resize(
                        (logo_width_px, logo_height_px),
                        Image.Resampling.BILINEAR)
        c.drawImage(ImageReader(logo), 1*mm, 19*mm,
                    width=logo_width_pt, height=logo_height_pt, mask='auto')

        # wrapOn Tamaño de la caja
        p_denom.wrapOn(c, 30*mm, 10*mm)
        # drawOn Posicion de la caja
        p_denom.drawOn(c, 2*mm, c._pagesize[1] - 6.5*mm - p_denom.height)

        p_cod_i.wrapOn(c, 12*mm, 8*mm)
        p_cod_i.drawOn(c, 2*mm, 3.5*mm)

        p_inven.wrapOn(c, 20*mm, 15*mm)
        p_inven.drawOn(c, 27*mm, 1*mm)

        p_cod_p.wrapOn(c, 20*mm, 5.8*mm)
        p_cod_p.drawOn(c, 2*mm, 10.5*mm)

        p_ubica.wrapOn(c, 30*mm, 10*mm)
        p_ubica.drawOn(c, 2*mm, c._pagesize[1] - 15.5*mm - p_ubica.height)

        p_entid.wrapOn(c, 45*mm, 5*mm)
        p_entid.drawOn(c, 7*mm, 19*mm)

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

