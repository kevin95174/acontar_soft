import os
import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox as mb
from utils.report_template_manager import ReportTemplateManager
from utils.helpers import resource_path


class Window_personalizar_reporte(tk.Toplevel):
    """Ventana interactiva para personalizar títulos, imágenes, orden, visibilidad y anchos de columnas."""

    def __init__(self, parent, valor, on_save_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.valor = valor
        self.on_save_callback = on_save_callback

        self.title("Personalizar Estructura del Reporte — AcontarSoft")
        self.geometry("820x680")
        self.minsize(740, 560)
        self.configure(bg="#f8fafc")
        if parent:
            self.transient(parent)

        self._centrar_ventana(820, 680)

        # Cargar plantilla actual
        self.template = ReportTemplateManager.get_template(self.valor)
        self.columnas = [dict(c) for c in self.template.get("columnas", [])]

        # Variables de control
        self.var_titulo = tk.StringVar(value=self.template.get("titulo", ""))
        self.var_subtitulo = tk.StringVar(value=self.template.get("subtitulo", ""))
        self.var_entidad = tk.StringVar(value=self.template.get("entidad", ""))
        self.var_logo = tk.StringVar(value=self.template.get("logo_path", ""))
        self.var_mostrar_logo = tk.BooleanVar(value=self.template.get("mostrar_logo", True))

        self._construir_interfaz()
        self._cargar_columnas_en_tree()

    def _centrar_ventana(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _construir_interfaz(self):
        contenedor = tk.Frame(self, bg="#f8fafc", padx=14, pady=10)
        contenedor.pack(fill="both", expand=True)

        # 1. Cabecera Informativa
        f_header = tk.Frame(contenedor, bg="#ffffff", bd=1, relief="solid", padx=12, pady=8)
        f_header.pack(fill="x", pady=(0, 10))

        tk.Label(
            f_header,
            text="⚙️ Personalización de Reporte",
            font=("Segoe UI", 12, "bold"),
            bg="#ffffff",
            fg="#0f172a"
        ).pack(anchor="w")

        tk.Label(
            f_header,
            text="Ajusta los títulos institucionales, logotipo y personaliza qué columnas incluir, su orden y anchos.",
            font=("Segoe UI", 9),
            bg="#ffffff",
            fg="#64748b"
        ).pack(anchor="w", pady=(2, 0))

        # 2. Grupo: Títulos e Imagen
        gf_titulos = ttk.LabelFrame(contenedor, text=" 🏛️ Encabezado Institucional y Logotipo ", padding=(12, 8))
        gf_titulos.pack(fill="x", pady=(0, 10))

        gf_titulos.columnconfigure(1, weight=1)

        # Título
        ttk.Label(gf_titulos, text="Título Reporte:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(gf_titulos, textvariable=self.var_titulo, font=("Segoe UI", 9)).grid(row=0, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=4)

        # Subtítulo / Período
        ttk.Label(gf_titulos, text="Subtítulo / Período:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(gf_titulos, textvariable=self.var_subtitulo, font=("Segoe UI", 9)).grid(row=1, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=4)

        # Entidad
        ttk.Label(gf_titulos, text="Entidad / Sede:", font=("Segoe UI", 9, "bold")).grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(gf_titulos, textvariable=self.var_entidad, font=("Segoe UI", 9)).grid(row=2, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=4)

        # Logo
        ttk.Label(gf_titulos, text="Ruta del Logo:", font=("Segoe UI", 9, "bold")).grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(gf_titulos, textvariable=self.var_logo, font=("Segoe UI", 9)).grid(row=3, column=1, sticky="ew", padx=(8, 4), pady=4)
        ttk.Button(gf_titulos, text="📁 Examinar...", command=self._examinar_logo).grid(row=3, column=2, sticky="e", pady=4)

        # Checkbox mostrar logo
        ttk.Checkbutton(gf_titulos, text="Mostrar logotipo institucional en el encabezado", variable=self.var_mostrar_logo).grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(2, 4))

        # 3. Grupo: Configuración de Columnas
        gf_columnas = ttk.LabelFrame(contenedor, text=" 📊 Columnas del Reporte (Crear, Quitar, Mover y Anchos) ", padding=(12, 8))
        gf_columnas.pack(fill="both", expand=True, pady=(0, 10))

        gf_columnas.rowconfigure(0, weight=1)
        gf_columnas.columnconfigure(0, weight=1)

        # Frame tabla y scrollbar
        f_tree = tk.Frame(gf_columnas, bg="#ffffff")
        f_tree.grid(row=0, column=0, sticky="nsew")
        f_tree.rowconfigure(0, weight=1)
        f_tree.columnconfigure(0, weight=1)

        cols = ("visible", "label", "campo", "ancho")
        self.tree = ttk.Treeview(f_tree, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("visible", text="Estado")
        self.tree.heading("label", text="Encabezado de Columna")
        self.tree.heading("campo", text="Campo BD Original")
        self.tree.heading("ancho", text="Ancho PDF (pt)")

        self.tree.column("visible", width=80, anchor="center")
        self.tree.column("label", width=260, anchor="w")
        self.tree.column("campo", width=140, anchor="w")
        self.tree.column("ancho", width=100, anchor="center")

        scroll_y = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<Double-Button-1>", lambda _e: self._alternar_visibilidad())

        # Botones laterales para mover y editar
        f_btns_lat = tk.Frame(gf_columnas, bg="#f8fafc", padx=8)
        f_btns_lat.grid(row=0, column=1, sticky="ns")

        ttk.Button(f_btns_lat, text="✔ Incluir / Quitar", command=self._alternar_visibilidad).pack(fill="x", pady=3)
        ttk.Button(f_btns_lat, text="▲ Subir", command=self._mover_arriba).pack(fill="x", pady=3)
        ttk.Button(f_btns_lat, text="▼ Bajar", command=self._mover_abajo).pack(fill="x", pady=3)
        ttk.Separator(f_btns_lat, orient="horizontal").pack(fill="x", pady=6)
        ttk.Button(f_btns_lat, text="✏️ Editar Columna", command=self._editar_columna).pack(fill="x", pady=3)
        ttk.Button(f_btns_lat, text="📐 Auto-ajustar Anchos", command=self._auto_ajustar_anchos).pack(fill="x", pady=3)

        # Resumen de ancho total
        self.lbl_ancho_total = tk.Label(
            gf_columnas,
            text="Ancho total columnas visibles: 0 pt (Objetivo A4 apaisado: ~760 pt)",
            font=("Segoe UI", 9, "italic"),
            bg="#f8fafc",
            fg="#475569"
        )
        self.lbl_ancho_total.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # 4. Barra Inferior de Acciones
        f_footer = tk.Frame(contenedor, bg="#f8fafc")
        f_footer.pack(fill="x", pady=(4, 0))

        ttk.Button(f_footer, text="↺ Restablecer Predeterminados", command=self._restablecer).pack(side="left", padx=4)

        ttk.Button(f_footer, text="✖ Cancelar", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(f_footer, text="💾 Guardar Plantilla", command=self._guardar).pack(side="right", padx=4)

    # -------------------------------------------------------------------------
    # OPERACIONES SOBRE LA LISTA DE COLUMNAS
    # -------------------------------------------------------------------------
    def _cargar_columnas_en_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        ancho_total = 0
        for idx, col in enumerate(self.columnas):
            vis = col.get("visible", True)
            estado_txt = "🟢 Visible" if vis else "⚪ Oculto"
            lbl = col.get("label", "").replace("\n", " ")
            campo = col.get("campo_bd", "")
            ancho = col.get("ancho", 50)

            if vis:
                ancho_total += ancho

            self.tree.insert("", "end", iid=str(idx), values=(estado_txt, lbl, campo, ancho))

        self.lbl_ancho_total.config(
            text=f"Ancho total columnas visibles: {ancho_total} pt (Objetivo A4 apaisado: 760 pt)"
        )

    def _examinar_logo(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar Logotipo Institucional",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp"), ("Todos los archivos", "*.*")],
            parent=self
        )
        if ruta:
            self.var_logo.set(ruta)

    def _get_selected_index(self):
        sel = self.tree.selection()
        if not sel:
            mb.showinfo("Selección", "Por favor, selecciona una columna de la tabla.", parent=self)
            return None
        return int(sel[0])

    def _alternar_visibilidad(self):
        idx = self._get_selected_index()
        if idx is None:
            return
        self.columnas[idx]["visible"] = not self.columnas[idx].get("visible", True)
        self._cargar_columnas_en_tree()
        self.tree.selection_set(str(idx))

    def _mover_arriba(self):
        idx = self._get_selected_index()
        if idx is None or idx == 0:
            return
        self.columnas[idx - 1], self.columnas[idx] = self.columnas[idx], self.columnas[idx - 1]
        self._cargar_columnas_en_tree()
        self.tree.selection_set(str(idx - 1))

    def _mover_abajo(self):
        idx = self._get_selected_index()
        if idx is None or idx >= len(self.columnas) - 1:
            return
        self.columnas[idx + 1], self.columnas[idx] = self.columnas[idx], self.columnas[idx + 1]
        self._cargar_columnas_en_tree()
        self.tree.selection_set(str(idx + 1))

    def _auto_ajustar_anchos(self):
        visibles = [c for c in self.columnas if c.get("visible", True)]
        if not visibles:
            mb.showwarning("Atención", "No hay columnas visibles para ajustar.", parent=self)
            return
        ReportTemplateManager.auto_ajustar_anchos(visibles, ancho_total_objetivo=760)
        self._cargar_columnas_en_tree()
        mb.showinfo("Ajuste Completo", "Los anchos de las columnas visibles se han ajustado proporcionalmente a 760 pt.", parent=self)

    def _editar_columna(self):
        idx = self._get_selected_index()
        if idx is None:
            return

        col = self.columnas[idx]

        # Diálogo para editar etiqueta y ancho
        dlg = tk.Toplevel(self)
        dlg.title("Editar Columna")
        dlg.geometry("400x230")
        dlg.minsize(360, 200)
        dlg.transient(self)
        dlg.grab_set()

        sw = dlg.winfo_screenwidth()
        sh = dlg.winfo_screenheight()
        dlg.geometry(f"+{(sw-400)//2}+{(sh-230)//2}")

        tk.Label(dlg, text=f"Editar Columna: {col.get('campo_bd', '')}", font=("Segoe UI", 10, "bold")).pack(pady=(12, 8))

        f_form = tk.Frame(dlg, padx=14)
        f_form.pack(fill="x")
        f_form.columnconfigure(1, weight=1)

        tk.Label(f_form, text="Encabezado:").grid(row=0, column=0, sticky="w", pady=4)
        var_lbl = tk.StringVar(value=col.get("label", ""))
        etr_lbl = ttk.Entry(f_form, textvariable=var_lbl)
        etr_lbl.grid(row=0, column=1, sticky="ew", pady=4, padx=(8, 0))

        tk.Label(f_form, text="Ancho PDF (pt):").grid(row=1, column=0, sticky="w", pady=4)
        var_ancho = tk.StringVar(value=str(col.get("ancho", 50)))
        etr_ancho = ttk.Entry(f_form, textvariable=var_ancho)
        etr_ancho.grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 0))

        def _guardar_edicion():
            nvo_lbl = var_lbl.get().strip()
            try:
                nvo_ancho = int(var_ancho.get().strip())
                if nvo_ancho < 15:
                    nvo_ancho = 15
            except ValueError:
                mb.showerror("Error", "El ancho debe ser un número entero válido.", parent=dlg)
                return

            if nvo_lbl:
                col["label"] = nvo_lbl
            col["ancho"] = nvo_ancho
            dlg.destroy()
            self._cargar_columnas_en_tree()
            self.tree.selection_set(str(idx))

        f_dlg_btns = tk.Frame(dlg, pady=12)
        f_dlg_btns.pack()
        ttk.Button(f_dlg_btns, text="Guardar", command=_guardar_edicion).pack(side="left", padx=4)
        ttk.Button(f_dlg_btns, text="Cancelar", command=dlg.destroy).pack(side="left", padx=4)

    # -------------------------------------------------------------------------
    # RESTABLECER Y GUARDAR
    # -------------------------------------------------------------------------
    def _restablecer(self):
        if mb.askyesno("Confirmar", "¿Deseas restablecer esta plantilla a su diseño original de fábrica?", parent=self):
            t_orig = ReportTemplateManager.reset_template(self.valor)
            self.template = t_orig
            self.columnas = [dict(c) for c in self.template.get("columnas", [])]
            self.var_titulo.set(self.template.get("titulo", ""))
            self.var_subtitulo.set(self.template.get("subtitulo", ""))
            self.var_entidad.set(self.template.get("entidad", ""))
            self.var_logo.set(self.template.get("logo_path", ""))
            self.var_mostrar_logo.set(self.template.get("mostrar_logo", True))
            self._cargar_columnas_en_tree()
            mb.showinfo("Restablecido", "La plantilla ha sido restablecida con éxito.", parent=self)

    def _guardar(self):
        visibles = [c for c in self.columnas if c.get("visible", True)]
        if not visibles:
            mb.showwarning("Atención", "Debe haber al menos una columna visible en el reporte.", parent=self)
            return

        nueva_plantilla = {
            "titulo": self.var_titulo.get().strip(),
            "subtitulo": self.var_subtitulo.get().strip(),
            "entidad": self.var_entidad.get().strip(),
            "logo_path": self.var_logo.get().strip(),
            "mostrar_logo": self.var_mostrar_logo.get(),
            "columnas": self.columnas
        }

        ok = ReportTemplateManager.save_template(self.valor, nueva_plantilla)
        if ok:
            mb.showinfo("Éxito", "¡Plantilla de reporte guardada correctamente!", parent=self)
            if self.on_save_callback:
                self.on_save_callback(nueva_plantilla)
            self.destroy()
        else:
            mb.showerror("Error", "No se pudo guardar la plantilla.", parent=self)
