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
from label.label_layout import get_label_layout

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


def _safe_xml(txt):
    return str(txt or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def draw_label_page(c, den, codint, codpatr, ubi, inv, entidad, styles=None, logo_reader=None, layout=None):
    """
    Dibuja una etiqueta en el canvas de ReportLab usando las posiciones y tamaños
    configurados en el diseño personalizable (o por defecto si layout es None).
    """
    if layout is None:
        layout = get_label_layout()

    elems = layout.get("elements", {})
    label_cfg = layout.get("label", {})
    page_h = float(label_cfg.get("height_mm", 25.0)) * mm

    align_map = {'left': 0, 'center': 1, 'right': 2}

    # 1. Código QR
    cfg_qr = elems.get("qr", {})
    if cfg_qr.get("visible", True):
        qr_payload = str(codpatr).strip() if str(codpatr).strip() else str(codint).strip()
        qr_image = qrcode.make(qr_payload)
        qr_buffer = io.BytesIO()
        qr_image.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)

        qr_w = float(cfg_qr.get("width_mm", 18.0)) * mm
        qr_h = float(cfg_qr.get("height_mm", 18.0)) * mm
        qr_x = float(cfg_qr.get("x_mm", 31.0)) * mm
        qr_y = page_h - (float(cfg_qr.get("y_mm", 3.0)) * mm) - qr_h
        c.drawImage(ImageReader(qr_buffer), qr_x, qr_y, width=qr_w, height=qr_h, mask='auto')

    # 2. Logo
    cfg_logo = elems.get("logo", {})
    if cfg_logo.get("visible", True) and logo_reader is not None:
        logo_w = float(cfg_logo.get("width_mm", 5.3)) * mm
        logo_h = float(cfg_logo.get("height_mm", 5.3)) * mm
        logo_x = float(cfg_logo.get("x_mm", 1.0)) * mm
        logo_y = page_h - (float(cfg_logo.get("y_mm", 1.0)) * mm) - logo_h
        c.drawImage(logo_reader, logo_x, logo_y, width=logo_w, height=logo_h, mask='auto')

    # 3. Entidad
    cfg_ent = elems.get("entidad", {})
    if cfg_ent.get("visible", True) and entidad:
        f_size = float(cfg_ent.get("font_size", 5.5))
        f_name = FONT_BOLD if cfg_ent.get("font_bold", False) else FONT_REGULAR
        align = align_map.get(cfg_ent.get("align", "left"), 0)
        style_ent = ParagraphStyle(name='L_Entid', fontSize=f_size, fontName=f_name, alignment=align, leading=f_size + 1.5)
        p_entid = Paragraph(_safe_xml(entidad), style_ent)
        wrap_w = float(cfg_ent.get("max_width_mm", 45.0)) * mm
        p_entid.wrapOn(c, wrap_w, 8 * mm)
        ent_x = float(cfg_ent.get("x_mm", 7.0)) * mm
        ent_y = page_h - (float(cfg_ent.get("y_mm", 1.2)) * mm) - p_entid.height
        p_entid.drawOn(c, ent_x, ent_y)

    # 4. Denominación
    cfg_den = elems.get("denominacion", {})
    if cfg_den.get("visible", True) and den:
        f_size = float(cfg_den.get("font_size", 5.0))
        f_name = FONT_BOLD if cfg_den.get("font_bold", False) else FONT_REGULAR
        align = align_map.get(cfg_den.get("align", "left"), 0)
        style_den = ParagraphStyle(name='L_Denom', fontSize=f_size, fontName=f_name, alignment=align, leading=f_size + 1.2)
        p_denom = Paragraph(_safe_xml(den), style_den)
        wrap_w = float(cfg_den.get("max_width_mm", 30.0)) * mm
        wrap_h = float(cfg_den.get("max_height_mm", 10.0)) * mm
        p_denom.wrapOn(c, wrap_w, wrap_h)
        den_x = float(cfg_den.get("x_mm", 2.0)) * mm
        den_y = page_h - (float(cfg_den.get("y_mm", 6.8)) * mm) - p_denom.height
        p_denom.drawOn(c, den_x, den_y)

    # 5. Código Patrimonial
    cfg_cp = elems.get("cod_patrimonial", {})
    if cfg_cp.get("visible", True) and codpatr:
        f_size = float(cfg_cp.get("font_size", 8.0))
        f_name = FONT_BOLD if cfg_cp.get("font_bold", True) else FONT_REGULAR
        align = align_map.get(cfg_cp.get("align", "left"), 0)
        style_cp = ParagraphStyle(name='L_CodP', fontSize=f_size, fontName=f_name, alignment=align, leading=f_size + 1.5)
        p_cod_p = Paragraph(_safe_xml(codpatr), style_cp)
        wrap_w = float(cfg_cp.get("max_width_mm", 26.0)) * mm
        p_cod_p.wrapOn(c, wrap_w, 8 * mm)
        cp_x = float(cfg_cp.get("x_mm", 2.0)) * mm
        cp_y = page_h - (float(cfg_cp.get("y_mm", 11.2)) * mm) - p_cod_p.height
        p_cod_p.drawOn(c, cp_x, cp_y)

    # 6. Ubicación / Oficina
    cfg_ubi = elems.get("ubicacion", {})
    if cfg_ubi.get("visible", True) and ubi:
        f_size = float(cfg_ubi.get("font_size", 4.0))
        f_name = FONT_BOLD if cfg_ubi.get("font_bold", False) else FONT_REGULAR
        align = align_map.get(cfg_ubi.get("align", "left"), 0)
        style_ubi = ParagraphStyle(name='L_Ubi', fontSize=f_size, fontName=f_name, alignment=align, leading=f_size + 1.2)
        p_ubica = Paragraph(_safe_xml(ubi), style_ubi)
        wrap_w = float(cfg_ubi.get("max_width_mm", 28.0)) * mm
        wrap_h = float(cfg_ubi.get("max_height_mm", 8.0)) * mm
        p_ubica.wrapOn(c, wrap_w, wrap_h)
        ubi_x = float(cfg_ubi.get("x_mm", 2.0)) * mm
        ubi_y = page_h - (float(cfg_ubi.get("y_mm", 15.2)) * mm) - p_ubica.height
        p_ubica.drawOn(c, ubi_x, ubi_y)

    # 7. Código Interno
    cfg_ci = elems.get("cod_interno", {})
    if cfg_ci.get("visible", True) and codint:
        f_size = float(cfg_ci.get("font_size", 11.0))
        f_name = FONT_BOLD if cfg_ci.get("font_bold", True) else FONT_REGULAR
        align = align_map.get(cfg_ci.get("align", "left"), 0)
        style_ci = ParagraphStyle(name='L_CodI', fontSize=f_size, fontName=f_name, alignment=align, leading=f_size + 1.5)
        p_cod_i = Paragraph(_safe_xml(codint), style_ci)
        wrap_w = float(cfg_ci.get("max_width_mm", 20.0)) * mm
        p_cod_i.wrapOn(c, wrap_w, 10 * mm)
        ci_x = float(cfg_ci.get("x_mm", 2.0)) * mm
        ci_y = page_h - (float(cfg_ci.get("y_mm", 18.2)) * mm) - p_cod_i.height
        p_cod_i.drawOn(c, ci_x, ci_y)

    # 8. Inventario / Periodo
    cfg_inv = elems.get("inventario", {})
    if cfg_inv.get("visible", True) and inv:
        f_size = float(cfg_inv.get("font_size", 6.0))
        f_name = FONT_BOLD if cfg_inv.get("font_bold", True) else FONT_REGULAR
        align = align_map.get(cfg_inv.get("align", "right"), 2)
        style_inv = ParagraphStyle(name='L_Inv', fontSize=f_size, fontName=f_name, alignment=align, leading=f_size + 1.2)
        p_inven = Paragraph(_safe_xml(inv), style_inv)
        wrap_w = float(cfg_inv.get("max_width_mm", 25.0)) * mm
        p_inven.wrapOn(c, wrap_w, 8 * mm)
        inv_x = float(cfg_inv.get("x_mm", 24.0)) * mm
        inv_y = page_h - (float(cfg_inv.get("y_mm", 21.0)) * mm) - p_inven.height
        p_inven.drawOn(c, inv_x, inv_y)


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


def generate_sample_label_pdf(layout=None, sample_data=None, output_path=None):
    """
    Genera un archivo PDF con datos de muestra usando el diseño indicado.
    Útil para el editor y diseñador de etiquetas.
    """
    if layout is None:
        layout = get_label_layout()

    if output_path is None:
        pathinit = 'labels/samples/'
        os.makedirs(pathinit, exist_ok=True)
        output_path = os.path.join(pathinit, "sample_preview.pdf")
    else:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

    config_instance = ConfigUtils()
    direccion = config_instance.load_config()
    datos_ini = datos_iniciales()
    entidad_default = str(datos_ini[1]) if (datos_ini and len(datos_ini) > 1 and datos_ini[1]) else "MUNICIPALIDAD EJEMPLO"
    inv_default = 'INVENTARIO ' + str(datos_ini[2]) if (datos_ini and len(datos_ini) > 2 and datos_ini[2]) else "INVENTARIO 2026"

    if sample_data is None:
        sample_data = {
            "entidad": entidad_default,
            "den": "COMPUTADORA PORTATIL CORE I7",
            "codint": "1052",
            "codpatr": "740899990001",
            "ubi": "ALMACEN CENTRAL - OFICINA 101",
            "inv": inv_default
        }

    w_mm = float(layout.get("label", {}).get("width_mm", 50.0))
    h_mm = float(layout.get("label", {}).get("height_mm", 25.0))

    c = canvas.Canvas(output_path)
    c.setPageSize((w_mm * mm, h_mm * mm))

    logo_reader = _cargar_logo_reader(direccion)

    draw_label_page(
        c,
        sample_data.get("den", ""),
        sample_data.get("codint", ""),
        sample_data.get("codpatr", ""),
        sample_data.get("ubi", ""),
        sample_data.get("inv", ""),
        sample_data.get("entidad", ""),
        logo_reader=logo_reader,
        layout=layout
    )
    c.showPage()
    c.save()
    return output_path


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
    inv = 'INVENTARIO ' + str(datos_ini[2]) if (datos_ini and len(datos_ini) > 2) else "INVENTARIO"
    codpatr = str(r[0][1])

    entidad = str(datos_ini[1]) if (datos_ini and len(datos_ini) > 1) else ""

    pdf = str(r[0][0]) + "_" + str(r[0][1]) + "_" + str(r[0][3])
    pdf_name = str(pdf) + ".pdf"
    pathinit = 'labels/'
    os.makedirs(pathinit, exist_ok=True)
    pathpdf = os.path.join(pathinit, pdf_name)

    layout = get_label_layout()
    w_mm = float(layout.get("label", {}).get("width_mm", 50.0))
    h_mm = float(layout.get("label", {}).get("height_mm", 25.0))

    c = canvas.Canvas(pathpdf)
    c.setPageSize((w_mm * mm, h_mm * mm))

    logo_reader = _cargar_logo_reader(direccion)

    draw_label_page(c, den, codint, codpatr, ubi, inv, entidad, logo_reader=logo_reader, layout=layout)
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

    logo_reader = _cargar_logo_reader(direccion)

    pathinit = 'labels/lotes/'
    os.makedirs(pathinit, exist_ok=True)
    if not output_name:
        import time
        output_name = f"lote_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
    if not output_name.lower().endswith('.pdf'):
        output_name += ".pdf"

    pathpdf = os.path.join(pathinit, output_name)

    layout = get_label_layout()
    w_mm = float(layout.get("label", {}).get("width_mm", 50.0))
    h_mm = float(layout.get("label", {}).get("height_mm", 25.0))

    c = canvas.Canvas(pathpdf)
    c.setPageSize((w_mm * mm, h_mm * mm))

    for item in items:
        den = str(item.get('deno', '') or item.get('DenBien', '') or '')
        codint = str(item.get('codint', '') or item.get('CodInt', '') or '')
        codpatr = str(item.get('codpat', '') or item.get('codpatr', '') or item.get('CodPat', '') or '')

        if oficina_personalizada_global and str(oficina_personalizada_global).strip():
            ubi = str(oficina_personalizada_global).strip()
        else:
            ubi = str(item.get('oficina_etiqueta', '') or item.get('oficina', '') or item.get('oficina_actual', '') or item.get('oficina_anterior', '') or '').strip()

        draw_label_page(c, den, codint, codpatr, ubi, inv, entidad, logo_reader=logo_reader, layout=layout)
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
