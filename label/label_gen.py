import os
import io
import re
import time
import traceback
import configparser
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

try:
    import win32print
except ImportError:
    win32print = None

try:
    import win32ui
    import win32con
except ImportError:
    win32ui = None
    win32con = None

try:
    import fitz
except ImportError:
    fitz = None

from PIL import ImageWin


def obtener_impresoras_sistema():
    """
    Retorna (lista_impresoras, impresora_predeterminada) detectadas en Windows.
    """
    impresoras = []
    predeterminada = ""
    if win32print is None:
        print("[PRINT][WARN] El módulo win32print no está disponible para listar impresoras.")
        return impresoras, predeterminada

    try:
        predeterminada = str(win32print.GetDefaultPrinter() or "").strip()
    except Exception as e:
        print(f"[PRINT][WARN] No se pudo obtener la impresora predeterminada: {e}")

    try:
        flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
        for info in win32print.EnumPrinters(flags):
            # info es una tupla (flags, description, name, comment)
            nombre = str(info[2] if len(info) > 2 else "").strip()
            if nombre and nombre not in impresoras:
                impresoras.append(nombre)
    except Exception as e:
        print(f"[PRINT][ERROR] Error enumerando impresoras del sistema: {e}")

    if predeterminada and predeterminada not in impresoras:
        impresoras.insert(0, predeterminada)

    return impresoras, predeterminada


def obtener_impresora_configurada(config_path='config.ini'):
    """
    Obtiene el nombre de la impresora guardada en config.ini.
    Si no hay ninguna guardada o no existe en el sistema, retorna la predeterminada de Windows.
    """
    impresoras, predeterminada = obtener_impresoras_sistema()
    guardada = ""
    try:
        if os.path.exists(config_path):
            cfg = configparser.ConfigParser()
            cfg.read(config_path)
            if 'Settings' in cfg:
                guardada = cfg['Settings'].get('printer_name', '').strip()
    except Exception as e:
        print(f"[PRINT][WARN] No se pudo leer printer_name desde {config_path}: {e}")

    if guardada and (not impresoras or guardada in impresoras):
        return guardada
    return predeterminada or (impresoras[0] if impresoras else "")


def guardar_impresora_configurada(nombre_impresora, config_path='config.ini'):
    """
    Guarda la impresora seleccionada en la sección [Settings] de config.ini.
    """
    nombre = str(nombre_impresora or "").strip()
    try:
        cfg = configparser.ConfigParser()
        if os.path.exists(config_path):
            cfg.read(config_path)
        if 'Settings' not in cfg:
            cfg['Settings'] = {}
        cfg['Settings']['printer_name'] = nombre
        with open(config_path, 'w') as f:
            cfg.write(f)
        print(f"[PRINT] Impresora configurada guardada en {config_path}: '{nombre}'")
        return True
    except Exception as e:
        print(f"[PRINT][ERROR] No se pudo guardar la impresora en {config_path}: {e}")
        traceback.print_exc()
        return False

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


def _sanitize_filename(texto):
    """Limpia caracteres inválidos en nombres de archivo para Windows."""
    limpio = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '_', str(texto or '').strip())
    limpio = re.sub(r'\s+', '_', limpio)
    return limpio or "etiqueta"


def _guardar_canvas_seguro(c, pathpdf):
    """Guarda el PDF y, si el archivo está bloqueado por otro proceso/visor, usa un nombre alternativo."""
    try:
        c.save()
        print(f"[LABEL] PDF generado correctamente en: {os.path.abspath(pathpdf)}")
        return pathpdf
    except PermissionError as perm_err:
        base, ext = os.path.splitext(pathpdf)
        alt_path = f"{base}_{int(time.time() * 1000)}{ext}"
        print(f"[LABEL][WARN] Permiso denegado al guardar '{pathpdf}' ({perm_err}). Intentando ruta alternativa: '{alt_path}'")
        c._filename = alt_path
        c.save()
        print(f"[LABEL] PDF guardado en ruta alternativa: {os.path.abspath(alt_path)}")
        return alt_path
    except Exception as e:
        print(f"[LABEL][ERROR] Falló al guardar el archivo PDF '{pathpdf}': {e}")
        traceback.print_exc()
        raise


def imprimir_pdf_silencioso_gdi(pathpdf, impresora=None):
    """
    Imprime un archivo PDF de forma 100% silenciosa y directa al spooler de Windows
    usando win32ui (GDI) + PyMuPDF (fitz) + PIL.ImageWin.
    NO abre visores externos de PDF (Edge, Acrobat Reader, navegador, etc.).
    """
    if win32ui is None or win32print is None or fitz is None:
        raise RuntimeError("Los modulos win32ui, win32print o fitz no estan disponibles para impresion directa.")

    abs_pdf = os.path.abspath(pathpdf)
    if not os.path.exists(abs_pdf):
        raise FileNotFoundError(f"El archivo PDF a imprimir no existe: {abs_pdf}")

    _, impresora_default = obtener_impresoras_sistema()
    impresora_destino = str(impresora or "").strip() or obtener_impresora_configurada() or impresora_default

    print(f"[PRINT_GDI] Iniciando impresion silenciosa directa en '{impresora_destino}' para '{abs_pdf}'")

    doc = fitz.open(abs_pdf)
    if doc.page_count == 0:
        print("[PRINT_GDI][WARN] El documento PDF no contiene paginas.")
        return False

    hDC = win32ui.CreateDC()
    if impresora_destino:
        hDC.CreatePrinterDC(impresora_destino)
    else:
        hDC.CreatePrinterDC()

    try:
        dpi_x = hDC.GetDeviceCaps(win32con.LOGPIXELSX) or 203
        dpi_y = hDC.GetDeviceCaps(win32con.LOGPIXELSY) or 203
        horz_res = hDC.GetDeviceCaps(win32con.HORZRES)
        vert_res = hDC.GetDeviceCaps(win32con.VERTRES)

        doc_title = os.path.splitext(os.path.basename(abs_pdf))[0]
        hDC.StartDoc(doc_title)
        try:
            for page in doc:
                hDC.StartPage()
                # Renderizar al DPI nativo de la impresora para maxima fidelidad
                pix = page.get_pixmap(dpi=dpi_x)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                dib = ImageWin.Dib(img)

                # Ajustar al area fisica si es necesario
                dest_w = pix.width
                dest_h = pix.height
                if horz_res > 0 and vert_res > 0:
                    scale = min(1.0, horz_res / float(pix.width), vert_res / float(pix.height))
                    dest_w = int(pix.width * scale)
                    dest_h = int(pix.height * scale)

                dib.draw(hDC.GetHandleOutput(), (0, 0, dest_w, dest_h))
                hDC.EndPage()
        finally:
            hDC.EndDoc()

        print(f"[PRINT_GDI] Impresion directa completada con exito ({doc.page_count} pag) en '{impresora_destino}'.")
        return True
    finally:
        try:
            hDC.DeleteDC()
        except Exception:
            pass


def _enviar_pdf_a_impresora(pathpdf, impresora=None):
    """
    Envia un archivo PDF a la impresora seleccionada (o predeterminada).
    Prioriza la impresion silenciosa directa por GDI (sin abrir ninguna ventana ni visor PDF).
    """
    abs_pdf = os.path.abspath(pathpdf)
    abs_dir = os.path.dirname(abs_pdf)
    pdf_filename = os.path.basename(abs_pdf)

    print(f"[PRINT] Preparando impresion de: {abs_pdf}")
    if not os.path.exists(abs_pdf):
        err_msg = f"El archivo PDF a imprimir no existe: {abs_pdf}"
        print(f"[PRINT][ERROR] {err_msg}")
        raise FileNotFoundError(err_msg)

    _, impresora_default = obtener_impresoras_sistema()
    impresora_destino = str(impresora or "").strip() or obtener_impresora_configurada() or impresora_default

    print(f"[PRINT] Impresora destino: '{impresora_destino}' | Predeterminada Windows: '{impresora_default}'")

    # 1. METODO PRINCIPAL: Impresion directa GDI silenciosa (sin abrir visores ni navegadores)
    err_gdi_msg = ""
    try:
        imprimir_pdf_silencioso_gdi(abs_pdf, impresora=impresora_destino)
        return True
    except Exception as e_gdi:
        err_gdi_msg = str(e_gdi)
        print(f"[PRINT][WARN] Impresion directa GDI fallo ({err_gdi_msg}). Probando metodos alternativos...")
        traceback.print_exc()

    # 2. METODO SECUNDARIO (Fallback): ShellExecute solo si el metodo silencioso fallo
    errores_intentos = [f"GDI: {err_gdi_msg}"]

    if impresora_destino:
        try:
            print(f"[PRINT] Intento fallback printto hacia {impresora_destino}")
            dest_arg = f'"{impresora_destino}"'
            res = win32api.ShellExecute(0, "printto", abs_pdf, dest_arg, abs_dir, 0)
            return True
        except Exception as e_pto:
            msg_pto = f"Intento printto ('{impresora_destino}') fallo: {e_pto}"
            print(f"[PRINT][WARN] {msg_pto}")
            errores_intentos.append(msg_pto)

    try:
        try:
            print(f"[PRINT] Intento fallback 'print' ruta absoluta -> ShellExecute('print', '{abs_pdf}')")
            res = win32api.ShellExecute(0, "print", abs_pdf, None, abs_dir, 0)
            return True
        except Exception as e1:
            errores_intentos.append(f"print abs: {e1}")

        try:
            res = win32api.ShellExecute(0, "print", pdf_filename, None, abs_dir, 0)
            return True
        except Exception as e2:
            errores_intentos.append(f"print rel: {e2}")
    finally:
        pass

    detalle_errores = " | ".join(errores_intentos)
    print(f"[PRINT][ERROR CRITICO] Todos los metodos de impresion fallaron para '{abs_pdf}'. Detalles: {detalle_errores}")
    raise RuntimeError(
        f"No se pudo enviar el PDF a la impresora '{impresora_destino or 'sin impresora'}'.\n"
        f"Detalle tecnico: {detalle_errores}"
    )


def build_label(valor, codigo, codact, oficina_personalizada=None, bien_data=None, impresora=None):
    print(
        f"[LABEL][build_label] Iniciando -> valor={valor}, codigo='{codigo}', "
        f"codact='{codact}', oficina_personalizada='{oficina_personalizada}', impresora='{impresora}'"
    )
    try:
        config_instance = ConfigUtils()
        direccion = config_instance.load_config()
    except Exception as cfg_err:
        print(f"[LABEL][WARN] Error al cargar configuración de imagen: {cfg_err}")
        direccion = None

    try:
        datos_ini = datos_iniciales()
    except Exception as ini_err:
        print(f"[LABEL][WARN] Error obteniendo datos_iniciales(): {ini_err}")
        datos_ini = None

    r = data_label(codigo)
    # Si no se encontró por el código pasado (ej. CodPat era 'NO CATALOGADO' o vacío) y tenemos bien_data, intentar con codint/codpat alternativo
    if not r and isinstance(bien_data, dict):
        alt_cod = str(bien_data.get("codint") or bien_data.get("CodInt") or bien_data.get("codpat") or bien_data.get("CodPat") or "").strip()
        if alt_cod and alt_cod != str(codigo).strip():
            print(f"[LABEL][build_label] Reintentando búsqueda en BD con código alternativo: '{alt_cod}'")
            r = data_label(alt_cod)

    if r and len(r) > 0:
        codint = str(r[0][0] or "")
        codpatr = str(r[0][1] or "")
        den = str(r[0][2] or "")
        inv_acta = str(r[0][3] or "")
    elif isinstance(bien_data, dict) and (bien_data.get("codint") or bien_data.get("codpat") or bien_data.get("deno")):
        print(f"[LABEL][WARN] No se halló en data_label('{codigo}'), usando datos en memoria de bien_data: {bien_data}")
        codint = str(bien_data.get("codint") or bien_data.get("CodInt") or "")
        codpatr = str(bien_data.get("codpat") or bien_data.get("CodPat") or "")
        den = str(bien_data.get("deno") or bien_data.get("DenBien") or "")
        inv_acta = str(bien_data.get("inv") or bien_data.get("acta_ant") or codact or "")
    else:
        err_msg = f"No se encontraron datos de etiqueta en la base de datos para el código: '{codigo}'"
        print(f"[LABEL][ERROR] {err_msg}")
        raise ValueError(err_msg)

    if oficina_personalizada is not None and str(oficina_personalizada).strip():
        ubi = str(oficina_personalizada).strip()
    else:
        try:
            j = data_label_ubi(codact)
            ubi = str(j[0][0]) if (j and len(j) > 0 and len(j[0]) > 0 and j[0][0] is not None) else ""
        except Exception as ubi_err:
            print(f"[LABEL][WARN] Error consultando oficina para acta '{codact}': {ubi_err}")
            ubi = ""

    inv = 'INVENTARIO ' + str(datos_ini[2]) if (datos_ini and len(datos_ini) > 2 and datos_ini[2] is not None) else "INVENTARIO"
    entidad = str(datos_ini[1]) if (datos_ini and len(datos_ini) > 1 and datos_ini[1] is not None) else ""

    pdf_raw = f"{codint}_{codpatr}_{inv_acta}"
    pdf_name = _sanitize_filename(pdf_raw) + ".pdf"
    pathinit = 'labels/'
    os.makedirs(pathinit, exist_ok=True)
    pathpdf = os.path.join(pathinit, pdf_name)

    try:
        layout = get_label_layout()
        w_mm = float(layout.get("label", {}).get("width_mm", 50.0))
        h_mm = float(layout.get("label", {}).get("height_mm", 25.0))

        c = canvas.Canvas(pathpdf)
        c.setPageSize((w_mm * mm, h_mm * mm))

        logo_reader = _cargar_logo_reader(direccion)

        draw_label_page(c, den, codint, codpatr, ubi, inv, entidad, logo_reader=logo_reader, layout=layout)
        c.showPage()
        pathpdf = _guardar_canvas_seguro(c, pathpdf)
    except Exception as gen_err:
        print(f"[LABEL][ERROR] Error construyendo el PDF de la etiqueta ({pathpdf}): {gen_err}")
        traceback.print_exc()
        raise

    if valor == 1:
        _enviar_pdf_a_impresora(pathpdf, impresora=impresora)

    return pathpdf


def build_label_batch(items, valor=0, output_name=None, oficina_personalizada_global=None, impresora=None):
    """
    Genera un único archivo PDF con múltiples páginas de etiquetas (una por cada ítem).
    Permite enviar a la impresora térmica todo el lote de una sola vez si valor == 1.
    """
    print(
        f"[LABEL][build_label_batch] Iniciando lote -> items={len(items) if items else 0}, "
        f"valor={valor}, output_name='{output_name}', impresora='{impresora}'"
    )
    if not items:
        print("[LABEL][ERROR] Lista de items vacía en build_label_batch")
        raise ValueError("No hay elementos para generar etiquetas.")

    try:
        config_instance = ConfigUtils()
        direccion = config_instance.load_config()
    except Exception as cfg_err:
        print(f"[LABEL][WARN] Error al cargar configuración en lote: {cfg_err}")
        direccion = None

    try:
        datos_ini = datos_iniciales()
    except Exception as ini_err:
        print(f"[LABEL][WARN] Error obteniendo datos_iniciales() en lote: {ini_err}")
        datos_ini = None

    entidad = str(datos_ini[1]) if (datos_ini and len(datos_ini) > 1 and datos_ini[1] is not None) else ""
    inv = 'INVENTARIO ' + str(datos_ini[2]) if (datos_ini and len(datos_ini) > 2 and datos_ini[2] is not None) else "INVENTARIO"

    logo_reader = _cargar_logo_reader(direccion)

    pathinit = 'labels/lotes/'
    os.makedirs(pathinit, exist_ok=True)
    if not output_name:
        output_name = f"lote_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
    if not output_name.lower().endswith('.pdf'):
        output_name += ".pdf"

    base_name = _sanitize_filename(os.path.splitext(os.path.basename(output_name))[0]) + ".pdf"
    pathpdf = os.path.join(pathinit, base_name)

    try:
        layout = get_label_layout()
        w_mm = float(layout.get("label", {}).get("width_mm", 50.0))
        h_mm = float(layout.get("label", {}).get("height_mm", 25.0))

        c = canvas.Canvas(pathpdf)
        c.setPageSize((w_mm * mm, h_mm * mm))

        for idx, item in enumerate(items):
            try:
                den = str(item.get('deno', '') or item.get('DenBien', '') or '')
                codint = str(item.get('codint', '') or item.get('CodInt', '') or '')
                codpatr = str(item.get('codpat', '') or item.get('codpatr', '') or item.get('CodPat', '') or '')

                if oficina_personalizada_global and str(oficina_personalizada_global).strip():
                    ubi = str(oficina_personalizada_global).strip()
                else:
                    ubi = str(item.get('oficina_etiqueta', '') or item.get('oficina', '') or item.get('oficina_actual', '') or item.get('oficina_anterior', '') or '').strip()

                draw_label_page(c, den, codint, codpatr, ubi, inv, entidad, logo_reader=logo_reader, layout=layout)
                c.showPage()
            except Exception as item_err:
                print(f"[LABEL][ERROR] Error dibujando etiqueta del ítem #{idx + 1} ({item}): {item_err}")
                traceback.print_exc()
                raise

        pathpdf = _guardar_canvas_seguro(c, pathpdf)
    except Exception as batch_err:
        print(f"[LABEL][ERROR] Error al generar/guardar PDF del lote '{pathpdf}': {batch_err}")
        traceback.print_exc()
        mb.showerror(message=f"Ha ocurrido un error al guardar el PDF del lote:\n{batch_err}", title="Error")
        return None

    if valor == 1:
        try:
            _enviar_pdf_a_impresora(pathpdf, impresora=impresora)
        except Exception as print_err:
            print(f"[LABEL][ERROR] Error al imprimir lote '{pathpdf}': {print_err}")
            traceback.print_exc()
            mb.showerror(message=f"Ha ocurrido un error al enviar el lote a la impresora:\n{print_err}", title="Error")
            return None

    return pathpdf
