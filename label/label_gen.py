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

def _get_label_styles():
    return {
        'denom': ParagraphStyle(
            name='BatchDenom',
            fontSize=5,
            fontName=FONT_REGULAR,
            alignment=0,
            borderPadding=1,
            leading=5
        ),
        'cod': ParagraphStyle(
            name='BatchCod',
            fontSize=11,
            fontName=FONT_BOLD,
            alignment=0,
            leading=7
        ),
        'inv': ParagraphStyle(
            name='BatchInv',
            fontSize=6,
            fontName=FONT_BOLD,
            alignment=2,
            charSpace=-5.0
        ),
        'cod_p': ParagraphStyle(
            name='BatchCodP',
            fontSize=8,
            fontName=FONT_BOLD,
            alignment=0,
            leading=7
        ),
        'ubi': ParagraphStyle(
            name='BatchUbi',
            fontSize=4,
            fontName=FONT_REGULAR,
            alignment=0,
            leading=5
        ),
        'entid': ParagraphStyle(
            name='BatchEntid',
            fontSize=5.5,
            fontName=FONT_REGULAR,
            alignment=0
        )
    }

def _safe_xml(txt):
    return str(txt or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def draw_label_page(c, den, codint, codpatr, ubi, inv, entidad, styles, logo_reader=None):
    qr_payload = str(codpatr).strip() if str(codpatr).strip() else str(codint).strip()
    qr_image = qrcode.make(qr_payload)
    qr_buffer = io.BytesIO()
    qr_image.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)

    p_denom = Paragraph(_safe_xml(den), styles['denom'])
    p_cod_i = Paragraph(_safe_xml(codint), styles['cod'])
    p_inven = Paragraph(_safe_xml(inv), styles['inv'])
    p_cod_p = Paragraph(_safe_xml(codpatr), styles['cod_p'])
    p_ubica = Paragraph(_safe_xml(ubi), styles['ubi'])
    p_entid = Paragraph(_safe_xml(entidad), styles['entid'])

    # QR
    c.drawImage(ImageReader(qr_buffer), 31*mm, 4*mm, width=18*mm, height=18*mm, mask='auto')

    # Logo
    if logo_reader is not None:
        c.drawImage(logo_reader, 1*mm, 19*mm, width=15, height=15, mask='auto')

    p_denom.wrapOn(c, 30*mm, 10*mm)
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

def _cargar_logo_reader(direccion):
    if direccion and len(direccion) > 0 and os.path.exists(direccion[0]):
        try:
            logo_width_pt = 15
            logo_height_pt = 15
            logo_width_px = round(logo_width_pt * PRINT_DPI / 72)
            logo_height_px = round(logo_height_pt * PRINT_DPI / 72)
            with Image.open(direccion[0]) as logo_source:
                logo = logo_source.convert("RGBA").resize(
                    (logo_width_px, logo_height_px), Image.Resampling.BILINEAR)
                return ImageReader(logo)
        except Exception as e:
            print(f"Error cargando logo para etiqueta: {e}")
    return None

def build_label(valor, codigo, codact, oficina_personalizada=None):
    config_instance = ConfigUtils()
    direccion = config_instance.load_config()

    datos_ini = datos_iniciales()

    r = data_label(codigo)
    if not r:
        raise ValueError(f"No se encontraron datos de etiqueta para el código: {codigo}")

    if oficina_personalizada is not None and str(oficina_personalizada).strip():
        ubi = str(oficina_personalizada).strip()
    else:
        j = data_label_ubi(codact)
        ubi = str(j[0][0]) if (j and len(j) > 0 and len(j[0]) > 0 and j[0][0] is not None) else ""
    den = str(r[0][2])
    codint = str(r[0][0])
    inv = 'INVENTARIO ' + str(datos_ini[2])
    codpatr = str(r[0][1])

    entidad = datos_ini[1]

    pdf = str(r[0][0]) + "_" + str(r[0][1]) + "_" + str(r[0][3])
    pdf_name = str(pdf) + ".pdf"
    pathinit = 'labels/'
    os.makedirs(pathinit, exist_ok=True)
    pathpdf = os.path.join(pathinit, pdf_name)

    c = canvas.Canvas(pathpdf)
    c.setPageSize((5*cm, 2.5*cm))

    styles = _get_label_styles()
    logo_reader = _cargar_logo_reader(direccion)

    draw_label_page(c, den, codint, codpatr, ubi, inv, entidad, styles, logo_reader)
    c.showPage()
    try:
        c.save()
        if valor == 1:
            try:
                win32api.ShellExecute(0, "print", pdf_name, None, "labels/", 0)
            except Exception:
                win32api.ShellExecute(0, "print", pdf_name, None, "labels", 0)
    except Exception as e:
        mb.showerror(message=f"Ha ocurrido un error, revise si el PDF está abierto o que la impresora esté bien configurada:\n{e}", title="Error")

    return pathpdf

def build_label_batch(items, valor=0, output_name=None, oficina_personalizada_global=None):
    """
    Genera un único archivo PDF con múltiples páginas de etiquetas (una por cada ítem).
    Permite enviar a la impresora térmica todo el lote de una sola vez si valor == 1.
    """
    if not items:
        raise ValueError("No hay elementos para generar etiquetas.")

    config_instance = ConfigUtils()
    direccion = config_instance.load_config()
    datos_ini = datos_iniciales()
    entidad = str(datos_ini[1]) if (datos_ini and len(datos_ini) > 1) else ""
    inv = 'INVENTARIO ' + str(datos_ini[2]) if (datos_ini and len(datos_ini) > 2) else "INVENTARIO"

    styles = _get_label_styles()
    logo_reader = _cargar_logo_reader(direccion)

    pathinit = 'labels/lotes/'
    os.makedirs(pathinit, exist_ok=True)
    if not output_name:
        import time
        output_name = f"lote_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
    if not output_name.lower().endswith('.pdf'):
        output_name += ".pdf"

    pathpdf = os.path.join(pathinit, output_name)
    c = canvas.Canvas(pathpdf)
    c.setPageSize((5*cm, 2.5*cm))

    for item in items:
        den = str(item.get('deno', '') or item.get('DenBien', '') or '')
        codint = str(item.get('codint', '') or item.get('CodInt', '') or '')
        codpatr = str(item.get('codpat', '') or item.get('codpatr', '') or item.get('CodPat', '') or '')

        if oficina_personalizada_global and str(oficina_personalizada_global).strip():
            ubi = str(oficina_personalizada_global).strip()
        else:
            ubi = str(item.get('oficina_etiqueta', '') or item.get('oficina', '') or item.get('oficina_actual', '') or item.get('oficina_anterior', '') or '').strip()

        draw_label_page(c, den, codint, codpatr, ubi, inv, entidad, styles, logo_reader)
        c.showPage()

    try:
        c.save()
        if valor == 1:
            try:
                win32api.ShellExecute(0, "print", output_name, None, pathinit, 0)
            except Exception:
                win32api.ShellExecute(0, "print", pathpdf, None, None, 0)
    except Exception as e:
        mb.showerror(message=f"Ha ocurrido un error al guardar o imprimir el lote:\n{e}", title="Error")
        return None

    return pathpdf
