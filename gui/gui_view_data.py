import os
import sqlite3
import tkinter as tk
from tkinter import ttk


class Window_view_data(tk.Toplevel):
    """Ventana para visualizar las tablas sincronizadas en SQLite."""

    def __init__(self, root=None):
        super().__init__(root)
        self.root = root
        self.title("Visor de Datos Sincronizados - AcontarSoft")
        self.geometry("1000x600")
        self.minsize(800, 450)

        # Ruta a SQLite
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_db = os.path.join(base_dir, "..", "db", "orap2022.db")
        self.db_path = getattr(self.root, "db_path", os.path.normpath(default_db))

        self._build_ui()
        self.cargar_datos_pestana_actual()

    def _build_ui(self):
        # Panel superior de búsqueda
        frame_search = ttk.Frame(self, padding=10)
        frame_search.pack(fill="x")

        ttk.Label(frame_search, text="🔍 Buscar:").pack(side="left", padx=(0, 5))
        self.txt_search = ttk.Entry(frame_search, width=35)
        self.txt_search.pack(side="left", padx=(0, 5))
        self.txt_search.bind("<KeyRelease>", lambda e: self.filtrar_tabla())

        self.lbl_count = ttk.Label(frame_search, text="Registros: 0", font=("Arial", 9, "bold"))
        self.lbl_count.pack(side="right")

        # Pestañas por tabla
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.cargar_datos_pestana_actual())

        # Configuración de tablas y sus columnas visibles
        self.tab_configs = {
            "assets": {
                "title": "📦 Bienes Patrimoniales",
                "columns": ["id", "codigo_patrimonial", "denominacion", "marca", "modelo", "serie", "estado_conservacion"],
                "headers": ["ID", "Cód. Patrimonial", "Denominación", "Marca", "Modelo", "Serie", "Estado"]
            },
            "inventory_records": {
                "title": "📋 Inventario Tomado",
                "columns": ["id", "codigo_patrimonial", "denominacion", "codigo_ubicacion_final", "inventariado", "fecha_inventariado"],
                "headers": ["ID", "Cód. Patrimonial", "Denominación", "Ubicación Final", "Estado Sync", "Fecha"]
            },
            "locations": {
                "title": "🏢 Ubicaciones / Oficinas",
                "columns": ["id", "codigo_ubicacion", "local", "area", "oficina", "piso"],
                "headers": ["ID", "Cód. Ubicación", "Local", "Área", "Oficina", "Piso"]
            },
            "personnel": {
                "title": "👤 Personal",
                "columns": ["id", "codigo_personal", "nombres", "apellidos", "cargo", "oficina"],
                "headers": ["ID", "Cód. Personal", "Nombres", "Apellidos", "Cargo", "Oficina"]
            },
            "surplus": {
                "title": "➕ Sobrantes",
                "columns": ["id", "denominacion", "marca", "modelo", "serie", "codigo_ubicacion"],
                "headers": ["ID", "Denominación", "Marca", "Modelo", "Serie", "Ubicación"]
            }
        }

        self.tables = {}
        for table_key, cfg in self.tab_configs.items():
            frame_tab = ttk.Frame(self.notebook)
            self.notebook.add(frame_tab, text=cfg["title"])

            # Crear Treeview con Scrollbars
            tree = ttk.Treeview(frame_tab, columns=cfg["columns"], show="headings", selectmode="browse")
            
            scrollbar_y = ttk.Scrollbar(frame_tab, orient="vertical", command=tree.yview)
            scrollbar_x = ttk.Scrollbar(frame_tab, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

            scrollbar_y.pack(side="right", fill="y")
            scrollbar_x.pack(side="bottom", fill="x")
            tree.pack(fill="both", expand=True)

            # Asignar encabezados
            for col, head in zip(cfg["columns"], cfg["headers"]):
                tree.heading(col, text=head)
                tree.column(col, width=120, anchor="w")

            self.tables[table_key] = tree

    def _get_active_table_key(self):
        index = self.notebook.index(self.notebook.select())
        return list(self.tab_configs.keys())[index]

    def cargar_datos_pestana_actual(self):
        table_key = self._get_active_table_key()
        tree = self.tables[table_key]
        cfg = self.tab_configs[table_key]

        # Limpiar filas anteriores
        for item in tree.get_children():
            tree.delete(item)

        cols_str = ", ".join(cfg["columns"])
        filter_text = self.txt_search.get().strip()

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = f"SELECT {cols_str} FROM {table_key}"
            params = []

            if filter_text:
                # Filtrar en todas las columnas configuradas
                where_clauses = [f"{col} LIKE ?" for col in cfg["columns"]]
                query += " WHERE " + " OR ".join(where_clauses)
                params = [f"%{filter_text}%"] * len(cfg["columns"])

            query += " LIMIT 500"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                tree.insert("", "end", values=row)

            self.lbl_count.config(text=f"Registros cargados: {len(rows)}")

        except Exception as e:
            self.lbl_count.config(text=f"Error al leer BD: {e}")

    def filtrar_tabla(self):
        self.cargar_datos_pestana_actual()