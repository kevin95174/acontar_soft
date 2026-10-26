import os
import json
import copy

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_PATHS = [
    os.path.join(_BASE_DIR, 'data', 'label_layout.json'),
    os.path.join(_BASE_DIR, 'label_layout.json')
]

DEFAULT_LABEL_LAYOUT = {
    "label": {
        "width_mm": 50.0,
        "height_mm": 25.0,
        "nombre": "Estándar 50x25 mm"
    },
    "elements": {
        "logo": {
            "nombre": "Logo de Entidad",
            "visible": True,
            "x_mm": 1.0,
            "y_mm": 1.0,
            "width_mm": 5.3,
            "height_mm": 5.3,
            "color_preview": "#dbeafe"
        },
        "entidad": {
            "nombre": "Nombre de Entidad",
            "visible": True,
            "x_mm": 7.0,
            "y_mm": 1.2,
            "max_width_mm": 41.0,
            "font_size": 5.5,
            "font_bold": False,
            "align": "left",
            "sample": "MUNICIPALIDAD EJEMPLO",
            "color_preview": "#e0e7ff"
        },
        "denominacion": {
            "nombre": "Denominación del Bien",
            "visible": True,
            "x_mm": 2.0,
            "y_mm": 6.8,
            "max_width_mm": 28.0,
            "max_height_mm": 7.5,
            "font_size": 5.0,
            "font_bold": False,
            "align": "left",
            "sample": "COMPUTADORA PORTATIL CORE I7",
            "color_preview": "#fef3c7"
        },
        "cod_patrimonial": {
            "nombre": "Cód. Patrimonial",
            "visible": True,
            "x_mm": 2.0,
            "y_mm": 11.2,
            "max_width_mm": 26.0,
            "font_size": 8.0,
            "font_bold": True,
            "align": "left",
            "sample": "740899990001",
            "color_preview": "#fee2e2"
        },
        "ubicacion": {
            "nombre": "Oficina / Ubicación",
            "visible": True,
            "x_mm": 2.0,
            "y_mm": 15.2,
            "max_width_mm": 28.0,
            "max_height_mm": 6.5,
            "font_size": 4.0,
            "font_bold": False,
            "align": "left",
            "sample": "ALMACEN CENTRAL - OFICINA 101",
            "color_preview": "#ecfdf5"
        },
        "cod_interno": {
            "nombre": "Cód. Interno",
            "visible": True,
            "x_mm": 2.0,
            "y_mm": 18.2,
            "max_width_mm": 20.0,
            "font_size": 11.0,
            "font_bold": True,
            "align": "left",
            "sample": "1052",
            "color_preview": "#ffedd5"
        },
        "inventario": {
            "nombre": "Inventario / Periodo",
            "visible": True,
            "x_mm": 24.0,
            "y_mm": 21.0,
            "max_width_mm": 25.0,
            "font_size": 6.0,
            "font_bold": True,
            "align": "right",
            "sample": "INVENTARIO 2026",
            "color_preview": "#f3e8ff"
        },
        "qr": {
            "nombre": "Código QR",
            "visible": True,
            "x_mm": 31.0,
            "y_mm": 3.0,
            "width_mm": 18.0,
            "height_mm": 18.0,
            "sample": "QR CODE",
            "color_preview": "#f1f5f9"
        }
    }
}


def get_default_layout():
    """Devuelve una copia profunda de la configuración predeterminada de etiqueta."""
    return copy.deepcopy(DEFAULT_LABEL_LAYOUT)


def get_layout_file_path():
    """Obtiene la ruta donde se guardará o leerá el archivo de configuración."""
    data_dir = os.path.join(_BASE_DIR, 'data')
    if os.path.exists(data_dir):
        return os.path.join(data_dir, 'label_layout.json')
    return os.path.join(_BASE_DIR, 'label_layout.json')


def get_label_layout():
    """
    Carga la configuración de etiqueta guardada.
    Si no existe o está corrupta, devuelve la predeterminada.
    """
    for path in _CONFIG_PATHS:
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)

                # Asegurar compatibilidad y fusionar claves faltantes con valores por defecto
                merged = get_default_layout()
                if "label" in loaded:
                    merged["label"].update(loaded["label"])
                if "elements" in loaded:
                    for k, v in loaded["elements"].items():
                        if k in merged["elements"]:
                            merged["elements"][k].update(v)
                        else:
                            merged["elements"][k] = v
                return merged
            except Exception as e:
                print(f"Advertencia al leer {path}: {e}. Usando diseño por defecto.")

    return get_default_layout()


def save_label_layout(layout_dict):
    """Guarda la configuración de la etiqueta en el archivo JSON."""
    target_path = get_layout_file_path()
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    try:
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(layout_dict, f, indent=4, ensure_ascii=False)
        return True, "Configuración de etiqueta guardada con éxito."
    except Exception as e:
        return False, f"Error al guardar la configuración: {e}"


def reset_label_layout():
    """Restaura la configuración a los valores por defecto."""
    default_layout = get_default_layout()
    ok, msg = save_label_layout(default_layout)
    return ok, default_layout
