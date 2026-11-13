import os
import json
from db.query import datos_iniciales
from utils.config_utils import ConfigUtils

CONFIG_FILE = "config_reportes.json"

# Campos por defecto para cada reporte (definición canónica)
DEFAULT_TEMPLATES = {
    1: {
        "titulo": "REPORTE DE BIENES UBICADOS",
        "subtitulo": "Inventario Patrimonial",
        "entidad": "",
        "logo_path": "",
        "mostrar_logo": True,
        "columnas": [
            {"id": "item", "label": "Nro", "campo_bd": "item", "ancho": 25, "visible": True},
            {"id": "cod_int", "label": "Código\nInterno", "campo_bd": "CodInt", "ancho": 35, "visible": True},
            {"id": "cod_pat", "label": "Código\nPatrimonial", "campo_bd": "CodPat", "ancho": 65, "visible": True},
            {"id": "denominacion", "label": "Denominación", "campo_bd": "DenBien", "ancho": 170, "visible": True},
            {"id": "detalles_tecnicos", "label": "Detalles Técnicos", "campo_bd": "detalles_tecnicos", "ancho": 180, "visible": True},
            {"id": "marca", "label": "Marca", "campo_bd": "Marca", "ancho": 55, "visible": False},
            {"id": "modelo", "label": "Modelo", "campo_bd": "Modelo", "ancho": 55, "visible": False},
            {"id": "serie", "label": "Serie", "campo_bd": "Serie", "ancho": 55, "visible": False},
            {"id": "color", "label": "Color", "campo_bd": "Color", "ancho": 45, "visible": False},
            {"id": "tipo", "label": "Tipo", "campo_bd": "Tipo", "ancho": 45, "visible": False},
            {"id": "dimension", "label": "Dimensión", "campo_bd": "Dimension", "ancho": 50, "visible": False},
            {"id": "estado", "label": "Estado", "campo_bd": "Estado", "ancho": 30, "visible": True},
            {"id": "ubicacion", "label": "Ubicación", "campo_bd": "Ubicacion", "ancho": 200, "visible": True},
        ]
    },
    2: {
        "titulo": "REPORTE DE BIENES DE OTRAS ENTIDADES",
        "subtitulo": "Inventario Patrimonial",
        "entidad": "",
        "logo_path": "",
        "mostrar_logo": True,
        "columnas": [
            {"id": "item", "label": "Item", "campo_bd": "item", "ancho": 28, "visible": True},
            {"id": "cod_pat", "label": "Cód.\nPatrimonial", "campo_bd": "CodPat", "ancho": 70, "visible": True},
            {"id": "denominacion", "label": "Denominación", "campo_bd": "denBienA", "ancho": 170, "visible": True},
            {"id": "ubicacion", "label": "Ubicación", "campo_bd": "Ubicacion", "ancho": 260, "visible": True},
            {"id": "estado", "label": "Estado", "campo_bd": "estado", "ancho": 38, "visible": True},
            {"id": "afectante", "label": "Entidad Afectante", "campo_bd": "afectante", "ancho": 200, "visible": True},
        ]
    },
    4: {
        "titulo": "REPORTE DE BIENES PARA ACTUALIZACIÓN DE VALOR NETO",
        "subtitulo": "Inventario Patrimonial",
        "entidad": "",
        "logo_path": "",
        "mostrar_logo": True,
        "columnas": [
            {"id": "item", "label": "Item", "campo_bd": "item", "ancho": 28, "visible": True},
            {"id": "cod_int", "label": "Cód.\nInterno", "campo_bd": "CodInt", "ancho": 40, "visible": True},
            {"id": "cod_pat", "label": "Cód.\nPatrimonial", "campo_bd": "CodPat", "ancho": 65, "visible": True},
            {"id": "denominacion", "label": "Denominación", "campo_bd": "DenBien", "ancho": 150, "visible": True},
            {"id": "cta_cont", "label": "Cuenta\nContable", "campo_bd": "CtaCont", "ancho": 60, "visible": True},
            {"id": "den_cta", "label": "Denominación\nCuenta", "campo_bd": "DenCta", "ancho": 140, "visible": True},
            {"id": "nro_doc", "label": "Doc. de\nAdquisición", "campo_bd": "NroDocAdq", "ancho": 65, "visible": True},
            {"id": "fec_adq", "label": "Fecha\nAdquisición", "campo_bd": "FechAdq", "ancho": 55, "visible": True},
            {"id": "val_adq", "label": "Valor\nAdquisición", "campo_bd": "ValorAdq", "ancho": 62, "visible": True},
            {"id": "dep_acum", "label": "Depreciación\nAcumulada", "campo_bd": "DepAcum", "ancho": 62, "visible": True},
            {"id": "val_neto", "label": "Valor Neto", "campo_bd": "ValNeto", "ancho": 62, "visible": True},
        ]
    },
    5: {
        "titulo": "REPORTE DE BIENES EN DESUSO O DEPÓSITOS",
        "subtitulo": "Inventario Patrimonial",
        "entidad": "",
        "logo_path": "",
        "mostrar_logo": True,
        "columnas": [
            {"id": "item", "label": "Item", "campo_bd": "item", "ancho": 28, "visible": True},
            {"id": "cod_int", "label": "Cód.\nInterno", "campo_bd": "CodInt", "ancho": 40, "visible": True},
            {"id": "cod_pat", "label": "Cód.\nPatrimonial", "campo_bd": "CodPat", "ancho": 65, "visible": True},
            {"id": "denominacion", "label": "Denominación", "campo_bd": "DenBien", "ancho": 160, "visible": True},
            {"id": "ubicacion", "label": "Ubicación", "campo_bd": "Ubicacion", "ancho": 160, "visible": True},
            {"id": "estado", "label": "Estado", "campo_bd": "Estado", "ancho": 40, "visible": True},
            {"id": "marca", "label": "Marca", "campo_bd": "Marca", "ancho": 60, "visible": True},
            {"id": "modelo", "label": "Modelo", "campo_bd": "Modelo", "ancho": 60, "visible": True},
            {"id": "serie", "label": "Serie", "campo_bd": "Serie", "ancho": 60, "visible": True},
            {"id": "color", "label": "Color", "campo_bd": "Color", "ancho": 55, "visible": True},
            {"id": "situacion", "label": "Situación", "campo_bd": "Situacion", "ancho": 45, "visible": True},
        ]
    },
    7: {
        "titulo": "REPORTE DE BIENES FALTANTES",
        "subtitulo": "Inventario Patrimonial",
        "entidad": "",
        "logo_path": "",
        "mostrar_logo": True,
        "columnas": [
            {"id": "item", "label": "Nro", "campo_bd": "item", "ancho": 25, "visible": True},
            {"id": "cod_int", "label": "Código\nInterno", "campo_bd": "CodInt", "ancho": 35, "visible": True},
            {"id": "cod_pat", "label": "Código\nPatrimonial", "campo_bd": "CodPat", "ancho": 65, "visible": True},
            {"id": "denominacion", "label": "Denominación", "campo_bd": "DenBien", "ancho": 170, "visible": True},
            {"id": "detalles_tecnicos", "label": "Detalles Técnicos", "campo_bd": "detalles_tecnicos", "ancho": 180, "visible": True},
            {"id": "marca", "label": "Marca", "campo_bd": "Marca", "ancho": 55, "visible": False},
            {"id": "modelo", "label": "Modelo", "campo_bd": "Modelo", "ancho": 55, "visible": False},
            {"id": "serie", "label": "Serie", "campo_bd": "Serie", "ancho": 55, "visible": False},
            {"id": "color", "label": "Color", "campo_bd": "Color", "ancho": 45, "visible": False},
            {"id": "tipo", "label": "Tipo", "campo_bd": "Tipo", "ancho": 45, "visible": False},
            {"id": "dimension", "label": "Dimensión", "campo_bd": "Dimension", "ancho": 50, "visible": False},
            {"id": "estado", "label": "Estado", "campo_bd": "Estado", "ancho": 30, "visible": True},
            {"id": "ubicacion", "label": "Última Ubicación", "campo_bd": "UltUbicacion", "ancho": 200, "visible": True},
        ]
    },
    8: {
        "titulo": "REPORTE DE BIENES SOBRANTES",
        "subtitulo": "Inventario Patrimonial",
        "entidad": "",
        "logo_path": "",
        "mostrar_logo": True,
        "columnas": [
            {"id": "item", "label": "Item", "campo_bd": "item", "ancho": 25, "visible": True},
            {"id": "ubicacion", "label": "Ubicación", "campo_bd": "Ubicacion", "ancho": 180, "visible": True},
            {"id": "denominacion", "label": "Denominación", "campo_bd": "den", "ancho": 180, "visible": True},
            {"id": "estado", "label": "Estado", "campo_bd": "estado", "ancho": 40, "visible": True},
            {"id": "marca", "label": "Marca", "campo_bd": "marca", "ancho": 60, "visible": True},
            {"id": "modelo", "label": "Modelo", "campo_bd": "modelo", "ancho": 60, "visible": True},
            {"id": "serie", "label": "Serie", "campo_bd": "serie", "ancho": 60, "visible": True},
            {"id": "tipo", "label": "Tipo", "campo_bd": "tipo", "ancho": 50, "visible": True},
            {"id": "color", "label": "Color", "campo_bd": "color", "ancho": 50, "visible": True},
            {"id": "dimension", "label": "Dimensión", "campo_bd": "dim", "ancho": 55, "visible": True},
        ]
    },
    9: {
        "titulo": "REPORTE DE BIENES DADOS DE BAJA SIN DISPOSICIÓN",
        "subtitulo": "Inventario Patrimonial",
        "entidad": "",
        "logo_path": "",
        "mostrar_logo": True,
        "columnas": [
            {"id": "item", "label": "Nro", "campo_bd": "item", "ancho": 28, "visible": True},
            {"id": "cod_int", "label": "Código\nInterno", "campo_bd": "CodInt", "ancho": 40, "visible": True},
            {"id": "cod_pat", "label": "Código\nPatrimonial", "campo_bd": "CodPat", "ancho": 68, "visible": True},
            {"id": "denominacion", "label": "Denominación", "campo_bd": "DenBien", "ancho": 160, "visible": True},
            {"id": "ubicacion", "label": "Ubicación", "campo_bd": "Ubicacion", "ancho": 160, "visible": True},
            {"id": "estado", "label": "Estado", "campo_bd": "Estado", "ancho": 45, "visible": True},
            {"id": "marca", "label": "Marca", "campo_bd": "Marca", "ancho": 55, "visible": True},
            {"id": "modelo", "label": "Modelo", "campo_bd": "Modelo", "ancho": 55, "visible": True},
            {"id": "serie", "label": "Serie", "campo_bd": "Serie", "ancho": 55, "visible": True},
            {"id": "color", "label": "Color", "campo_bd": "Color", "ancho": 50, "visible": True},
            {"id": "tipo", "label": "Tipo", "campo_bd": "Tipo", "ancho": 50, "visible": True},
            {"id": "resolucion", "label": "Resolución", "campo_bd": "Resolucion", "ancho": 70, "visible": True},
        ]
    },
    10: {
        "titulo": "CONCILIACIÓN DE INVENTARIO",
        "subtitulo": "Inventario Patrimonial",
        "entidad": "",
        "logo_path": "",
        "mostrar_logo": True,
        "columnas": [
            {"id": "cuenta", "label": "Cuenta", "campo_bd": "Cuenta", "ancho": 35, "visible": True},
            {"id": "subcuenta", "label": "SubCuenta", "campo_bd": "SubCuenta", "ancho": 65, "visible": True},
            {"id": "denominacion", "label": "Denominación", "campo_bd": "Denominacion", "ancho": 200, "visible": True},
            {"id": "val_reg", "label": "Registro\nPatrimonial\nValor", "campo_bd": "RegPatValor", "ancho": 65, "visible": True},
            {"id": "cant_reg", "label": "Cantidad\nRegistrados", "campo_bd": "CantReg", "ancho": 60, "visible": True},
            {"id": "val_inv", "label": "Resultado\nde Inventario\nValor", "campo_bd": "ResInvValor", "ancho": 65, "visible": True},
            {"id": "cant_inv", "label": "Cantidad\nInventariados", "campo_bd": "CantInv", "ancho": 60, "visible": True},
            {"id": "val_falt", "label": "Valor\nFaltantes", "campo_bd": "ValFalt", "ancho": 65, "visible": True},
            {"id": "cant_falt", "label": "Cantidad\nFaltantes", "campo_bd": "CantFalt", "ancho": 60, "visible": True},
        ]
    },
    11: {
        "titulo": "REPORTE DE BIENES QUE REQUIEREN ACTUALIZACIÓN TÉCNICA",
        "subtitulo": "Inventario Patrimonial",
        "entidad": "",
        "logo_path": "",
        "mostrar_logo": True,
        "columnas": [
            {"id": "item", "label": "Item", "campo_bd": "item", "ancho": 25, "visible": True},
            {"id": "cod_int", "label": "Cód.\nInterno", "campo_bd": "CodInt", "ancho": 35, "visible": True},
            {"id": "cod_pat", "label": "Cód.\nPatrimonial", "campo_bd": "CodPat", "ancho": 60, "visible": True},
            {"id": "denominacion", "label": "Denominación", "campo_bd": "Denominacion", "ancho": 140, "visible": True},
            {"id": "detalle", "label": "Detalle", "campo_bd": "Detalle", "ancho": 60, "visible": True},
            {"id": "estado", "label": "Estado", "campo_bd": "Estado", "ancho": 30, "visible": True},
            {"id": "marca", "label": "Marca", "campo_bd": "Marca", "ancho": 60, "visible": True},
            {"id": "modelo", "label": "Modelo", "campo_bd": "Modelo", "ancho": 60, "visible": True},
            {"id": "tipo", "label": "Tipo", "campo_bd": "Tipo", "ancho": 55, "visible": True},
            {"id": "serie", "label": "Serie", "campo_bd": "Serie", "ancho": 60, "visible": True},
            {"id": "color", "label": "Color", "campo_bd": "Color", "ancho": 55, "visible": True},
            {"id": "dimensiones", "label": "Dimensiones", "campo_bd": "Dimensiones", "ancho": 60, "visible": True},
            {"id": "obs", "label": "Obs", "campo_bd": "Obs", "ancho": 60, "visible": True},
        ]
    }
}


class ReportTemplateManager:
    CAMPOS_DISPONIBLES = {
        1: [
            ("item", "N° Correlativo (#)"),
            ("CodInt", "Código Interno"),
            ("CodPat", "Código Patrimonial"),
            ("DenBien", "Denominación del Bien"),
            ("detalles_tecnicos", "Detalles Técnicos (Combinados)"),
            ("Marca", "Marca"),
            ("Modelo", "Modelo"),
            ("Serie", "Serie"),
            ("Color", "Color"),
            ("Tipo", "Tipo"),
            ("Dimension", "Dimensión"),
            ("Estado", "Estado de Conservación"),
            ("Ubicacion", "Ubicación / Oficina"),
        ],
        2: [
            ("item", "N° Correlativo (#)"),
            ("CodPat", "Código Patrimonial"),
            ("denBienA", "Denominación del Bien"),
            ("Ubicacion", "Ubicación / Oficina"),
            ("estado", "Estado"),
            ("afectante", "Entidad Afectante"),
        ],
        4: [
            ("item", "N° Correlativo (#)"),
            ("CodInt", "Código Interno"),
            ("CodPat", "Código Patrimonial"),
            ("DenBien", "Denominación del Bien"),
            ("CtaCont", "Cuenta Contable"),
            ("DenCta", "Denominación Cuenta"),
            ("NroDocAdq", "Doc. de Adquisición"),
            ("FechAdq", "Fecha de Adquisición"),
            ("ValorAdq", "Valor de Adquisición"),
            ("DepAcum", "Depreciación Acumulada"),
            ("ValNeto", "Valor Neto"),
        ],
        5: [
            ("item", "N° Correlativo (#)"),
            ("CodInt", "Código Interno"),
            ("CodPat", "Código Patrimonial"),
            ("DenBien", "Denominación del Bien"),
            ("Ubicacion", "Ubicación / Oficina"),
            ("Estado", "Estado"),
            ("Marca", "Marca"),
            ("Modelo", "Modelo"),
            ("Serie", "Serie"),
            ("Color", "Color"),
            ("Situacion", "Situación"),
        ],
        7: [
            ("item", "N° Correlativo (#)"),
            ("CodInt", "Código Interno"),
            ("CodPat", "Código Patrimonial"),
            ("DenBien", "Denominación del Bien"),
            ("detalles_tecnicos", "Detalles Técnicos (Combinados)"),
            ("Marca", "Marca"),
            ("Modelo", "Modelo"),
            ("Serie", "Serie"),
            ("Color", "Color"),
            ("Tipo", "Tipo"),
            ("Dimension", "Dimensión"),
            ("Estado", "Estado"),
            ("UltUbicacion", "Última Ubicación"),
        ],
        8: [
            ("item", "N° Correlativo (#)"),
            ("Ubicacion", "Ubicación / Oficina"),
            ("den", "Denominación"),
            ("estado", "Estado"),
            ("marca", "Marca"),
            ("modelo", "Modelo"),
            ("serie", "Serie"),
            ("tipo", "Tipo"),
            ("color", "Color"),
            ("dim", "Dimensión"),
        ],
        9: [
            ("item", "N° Correlativo (#)"),
            ("CodInt", "Código Interno"),
            ("CodPat", "Código Patrimonial"),
            ("DenBien", "Denominación"),
            ("Ubicacion", "Ubicación / Oficina"),
            ("Estado", "Estado"),
            ("Marca", "Marca"),
            ("Modelo", "Modelo"),
            ("Serie", "Serie"),
            ("Color", "Color"),
            ("Tipo", "Tipo"),
            ("Resolucion", "Resolución"),
        ],
        10: [
            ("Cuenta", "Cuenta"),
            ("SubCuenta", "SubCuenta"),
            ("Denominacion", "Denominación"),
            ("RegPatValor", "Registro Patrimonial Valor"),
            ("CantReg", "Cantidad Registrados"),
            ("ResInvValor", "Resultado Inventario Valor"),
            ("CantInv", "Cantidad Inventariados"),
            ("ValFalt", "Valor Faltantes"),
            ("CantFalt", "Cantidad Faltantes"),
        ],
        11: [
            ("item", "N° Correlativo (#)"),
            ("CodInt", "Código Interno"),
            ("CodPat", "Código Patrimonial"),
            ("Denominacion", "Denominación"),
            ("Detalle", "Detalle Técnico"),
            ("Estado", "Estado"),
            ("Marca", "Marca"),
            ("Modelo", "Modelo"),
            ("Tipo", "Tipo"),
            ("Serie", "Serie"),
            ("Color", "Color"),
            ("Dimensiones", "Dimensiones"),
            ("Obs", "Observaciones"),
        ]
    }

    @classmethod
    def obtener_campos_disponibles(cls, valor):
        return cls.CAMPOS_DISPONIBLES.get(valor, cls.CAMPOS_DISPONIBLES[1])
    """Gestiona la lectura, guardado y aplicación de plantillas de reportes personalizables."""

    @staticmethod
    def _cargar_todas_las_plantillas():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @staticmethod
    def _guardar_todas_las_plantillas(data):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar plantillas de reportes: {e}")
            return False

    @classmethod
    def get_template(cls, valor):
        """Retorna la plantilla para el valor de reporte dado, fusionada con los valores por defecto."""
        todas = cls._cargar_todas_las_plantillas()
        key = str(valor)

        # Plantilla base por defecto
        base = DEFAULT_TEMPLATES.get(valor)
        if not base:
            # Plantilla genérica de respaldo si no existe en DEFAULT_TEMPLATES
            base = {
                "titulo": f"REPORTE {valor}",
                "subtitulo": "Inventario Patrimonial",
                "entidad": "",
                "logo_path": "",
                "mostrar_logo": True,
                "columnas": []
            }

        import copy
        template = copy.deepcopy(base)

        # Valores dinámicos por defecto si están vacíos
        datos_ini = datos_iniciales()
        default_entidad = str(datos_ini[1]) if (datos_ini and len(datos_ini) > 1 and datos_ini[1]) else ""
        fecha_inv = str(datos_ini[3]) if (datos_ini and len(datos_ini) > 3 and datos_ini[3]) else (str(datos_ini[2]) if (datos_ini and len(datos_ini) > 2 and datos_ini[2]) else "")
        default_sub = f"Inventario patrimonial al {fecha_inv}" if fecha_inv else "Inventario Patrimonial"

        config_inst = ConfigUtils()
        direccion = config_inst.load_config()
        default_logo = direccion[1] if (direccion and len(direccion) > 1) else ""

        if not template.get("entidad"):
            template["entidad"] = default_entidad
        if not template.get("subtitulo") or template.get("subtitulo") == "Inventario Patrimonial":
            template["subtitulo"] = default_sub
        if not template.get("logo_path"):
            template["logo_path"] = default_logo

        # Si el usuario ya personalizó este reporte en JSON, sobreescribir campos guardados
        # Normalizar atributos tipográficos y formato en columnas
        for col in template.get("columnas", []):
            if "font_size" not in col:
                col["font_size"] = 7
            if "font_name" not in col:
                col["font_name"] = "Helvetica"
            if "align" not in col:
                campo = col.get("campo_bd", "")
                col["align"] = "CENTER" if campo in ["item", "CodInt", "CodPat", "Estado", "estado", "situacion"] else "LEFT"
            if "header_bg" not in col:
                col["header_bg"] = "#DBDBDB"

        if key in todas:
            guardada = todas[key]
            if "titulo" in guardada:
                template["titulo"] = guardada["titulo"]
            if "subtitulo" in guardada:
                template["subtitulo"] = guardada["subtitulo"]
            if "entidad" in guardada:
                template["entidad"] = guardada["entidad"]
            if "logo_path" in guardada:
                template["logo_path"] = guardada["logo_path"]
            if "mostrar_logo" in guardada:
                template["mostrar_logo"] = guardada["mostrar_logo"]
            if "columnas" in guardada and guardada["columnas"]:
                template["columnas"] = guardada["columnas"]

        return template

    @classmethod
    def save_template(cls, valor, template_dict):
        """Guarda la configuración personalizada de un reporte específico."""
        todas = cls._cargar_todas_las_plantillas()
        todas[str(valor)] = template_dict
        return cls._guardar_todas_las_plantillas(todas)

    @classmethod
    def reset_template(cls, valor):
        """Restablece el reporte a su configuración original de fábrica."""
        todas = cls._cargar_todas_las_plantillas()
        key = str(valor)
        if key in todas:
            del todas[key]
            cls._guardar_todas_las_plantillas(todas)
        return cls.get_template(valor)

    @staticmethod
    def auto_ajustar_anchos(columnas_visibles, ancho_total_objetivo=760):
        """
        Escala proporcionalmente los anchos de las columnas visibles para que
        ocupen exactamente el ancho útil de la página A4 apaisada (aprox. 760 pt).
        """
        if not columnas_visibles:
            return columnas_visibles

        suma_actual = sum(c.get("ancho", 50) for c in columnas_visibles)
        if suma_actual <= 0:
            suma_actual = 1

        factor = ancho_total_objetivo / suma_actual
        acumulado = 0
        for i, col in enumerate(columnas_visibles):
            if i == len(columnas_visibles) - 1:
                # La última columna absorbe el residuo del redondeo
                col["ancho"] = max(20, round(ancho_total_objetivo - acumulado))
            else:
                nuevo_ancho = max(20, round(col.get("ancho", 50) * factor))
                col["ancho"] = nuevo_ancho
                acumulado += nuevo_ancho

        return columnas_visibles

    @classmethod
    def preparar_datos_para_pdf(cls, valor, raw_datos, template=None, incluir_metadata=False):
        """
        Toma los datos crudos de la base de datos (según valor de reporte) y aplica
        la plantilla activa:
        - Filtra sólo las columnas visibles.
        - Ordena los datos según el orden de las columnas personalizadas.
        - Retorna (encabezados, datos_filtrados, colwidths).
        """
        if not template:
            template = cls.get_template(valor)

        cols_visibles = [c for c in template.get("columnas", []) if c.get("visible", True)]
        if not cols_visibles:
            # Respaldo si todas quedaron ocultas
            cols_visibles = template.get("columnas", [])

        # Para reportes tipo 1 y 7, el raw_datos contiene:
        # 0: Item, 1: CodInt, 2: CodPat, 3: DenBien, 4: Marca, 5: Modelo,
        # 6: Serie, 7: Color, 8: Tipo, 9: Dimension, 10: Estado, 11: Ubicacion
        # Mapa de campos a índices en raw_datos
        mapa_indices = {}
        if valor in [1, 7]:
            mapa_indices = {
                "item": 0, "CodInt": 1, "CodPat": 2, "DenBien": 3,
                "Marca": 4, "Modelo": 5, "Serie": 6, "Color": 7,
                "Tipo": 8, "Dimension": 9, "Estado": 10,
                "Ubicacion": 11, "UltUbicacion": 11,
                "detalles_tecnicos": "SPECIAL_DETALLES"
            }
        elif valor == 2:
            # 0: Item, 1: CodPat, 2: denBienA, 3: Ubicacion, 4: estado, 5: afectante
            mapa_indices = {
                "item": 0, "CodPat": 1, "denBienA": 2, "Ubicacion": 3, "estado": 4, "afectante": 5
            }
        elif valor == 4:
            # 0: Item, 1: CodInt, 2: CodPat, 3: DenBien, 4: CtaCont, 5: DenCta,
            # 6: NroDocAdq, 7: FechAdq, 8: ValorAdq, 9: DepAcum, 10: ValNeto
            mapa_indices = {
                "item": 0, "CodInt": 1, "CodPat": 2, "DenBien": 3, "CtaCont": 4, "DenCta": 5,
                "NroDocAdq": 6, "FechAdq": 7, "ValorAdq": 8, "DepAcum": 9, "ValNeto": 10
            }
        elif valor == 5:
            # 0: Item, 1: CodInt, 2: CodPat, 3: DenBien, 4: Ubicacion, 5: Estado,
            # 6: Marca, 7: Modelo, 8: Serie, 9: Color, 10: Situacion
            mapa_indices = {
                "item": 0, "CodInt": 1, "CodPat": 2, "DenBien": 3, "Ubicacion": 4, "Estado": 5,
                "Marca": 6, "Modelo": 7, "Serie": 8, "Color": 9, "Situacion": 10
            }
        elif valor == 8:
            # 0: Item, 1: Ubicacion, 2: den, 3: estado, 4: marca, 5: modelo, 6: serie, 7: tipo, 8: color, 9: dim
            mapa_indices = {
                "item": 0, "Ubicacion": 1, "den": 2, "estado": 3, "marca": 4,
                "modelo": 5, "serie": 6, "tipo": 7, "color": 8, "dim": 9
            }
        elif valor == 9:
            # 0: Item, 1: CodInt, 2: CodPat, 3: DenBien, 4: Ubicacion, 5: Estado,
            # 6: Marca, 7: Modelo, 8: Serie, 9: Color, 10: Tipo, 11: Resolucion
            mapa_indices = {
                "item": 0, "CodInt": 1, "CodPat": 2, "DenBien": 3, "Ubicacion": 4, "Estado": 5,
                "Marca": 6, "Modelo": 7, "Serie": 8, "Color": 9, "Tipo": 10, "Resolucion": 11
            }
        elif valor == 10:
            mapa_indices = {
                "Cuenta": 0, "SubCuenta": 1, "Denominacion": 2, "RegPatValor": 3,
                "CantReg": 4, "ResInvValor": 5, "CantInv": 6, "ValFalt": 7, "CantFalt": 8
            }
        elif valor == 11:
            mapa_indices = {
                "item": 0, "CodInt": 1, "CodPat": 2, "Denominacion": 3, "Detalle": 4,
                "Estado": 5, "Marca": 6, "Modelo": 7, "Tipo": 8, "Serie": 9,
                "Color": 10, "Dimensiones": 11, "Obs": 12
            }

        encabezados = [c.get("label", "") for c in cols_visibles]
        colwidths = [c.get("ancho", 50) for c in cols_visibles]

        # Si no hay mapeo específico o no coincide, usar fallback directo
        if not mapa_indices:
            return (encabezados, raw_datos, colwidths, cols_visibles) if incluir_metadata else (encabezados, raw_datos, colwidths)

        datos_procesados = []
        for idx, row in enumerate(raw_datos, 1):
            norm_row = list(row)
            if valor != 10:
                if valor in [1, 7] and len(norm_row) == 11:
                    norm_row.insert(0, str(idx))
                elif valor == 2 and len(norm_row) == 5:
                    norm_row.insert(0, str(idx))
                elif valor in [4, 5] and len(norm_row) == 10:
                    norm_row.insert(0, str(idx))
                elif valor == 8 and len(norm_row) == 9:
                    norm_row.insert(0, str(idx))
                elif valor == 9 and len(norm_row) == 11:
                    norm_row.insert(0, str(idx))
                elif valor == 11 and len(norm_row) == 12:
                    norm_row.insert(0, str(idx))

            fila = []
            for col in cols_visibles:
                campo_id = col.get("campo_bd", "")
                target_idx = mapa_indices.get(campo_id, None)

                if target_idx == "SPECIAL_DETALLES":
                    marca = 'MARCA: ' + str(norm_row[4]) if len(norm_row) > 4 and norm_row[4] else ''
                    modelo = 'MODELO: ' + str(norm_row[5]) if len(norm_row) > 5 and norm_row[5] else ''
                    serie = 'SERIE: ' + str(norm_row[6]) if len(norm_row) > 6 and norm_row[6] else ''
                    color = 'COLOR: ' + str(norm_row[7]) if len(norm_row) > 7 and norm_row[7] else ''
                    tipo = 'TIPO: ' + str(norm_row[8]) if len(norm_row) > 8 and norm_row[8] else ''
                    dimension = 'DIMENSIÓN: ' + str(norm_row[9]) if len(norm_row) > 9 and norm_row[9] else ''
                    detalles = ' - '.join(filter(None, [marca, modelo, serie, color, tipo, dimension]))
                    fila.append(detalles)
                elif target_idx == 0 and campo_id == "item":
                    fila.append(str(idx))
                elif isinstance(target_idx, int) and target_idx < len(norm_row):
                    val = norm_row[target_idx]
                    fila.append(str(val) if (val is not None and str(val).strip() != "None") else "")
                else:
                    fila.append("")
            datos_procesados.append(fila)

        return (encabezados, datos_procesados, colwidths, cols_visibles) if incluir_metadata else (encabezados, datos_procesados, colwidths)
