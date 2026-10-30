import tkinter as tk
from tkinter import filedialog, messagebox
import pdfplumber
import pandas as pd
from reportlab.lib.pagesizes import landscape, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os

def seleccionar_archivo():
    archivo = filedialog.askopenfilename(
        title="Selecciona el archivo PDF",
        filetypes=[("Archivos PDF", "*.pdf")]
    )
    if archivo:
        entry_ruta.delete(0, tk.END)
        entry_ruta.insert(0, archivo)

def procesar_pdf():
    ruta_pdf = entry_ruta.get()
    if not ruta_pdf or not os.path.exists(ruta_pdf):
        messagebox.showerror("Error", "Por favor, selecciona un archivo PDF válido.")
        return

    try:
        # 1. Extraer tablas del PDF
        messagebox.showinfo("Procesando", "Extrayendo tablas del PDF. Esto puede tardar unos segundos...")
        todas_las_tablas = []
        
        with pdfplumber.open(ruta_pdf) as pdf:
            for pagina in pdf.pages:
                tablas = pagina.extract_tables()
                for tabla in tablas:
                    if tabla and len(tabla) > 1: # Asegurar que no esté vacía
                        todas_las_tablas.append(tabla)

        if not todas_las_tablas:
            messagebox.showerror("Error", "No se encontraron tablas en el PDF.")
            return

        # 2. Procesar los datos (Unificar y agregar columna)
        # Nota: Esto es una simplificación. En un PDF real, las columnas pueden variar.
        # Asumiremos que la primera fila de la primera tabla tiene los encabezados.
        
        encabezados = todas_las_tablas[0][0]
        datos = []
        
        # Buscar el índice de la columna "Reg" o "Reg Siaf" para insertar antes
        idx_reg = -1
        for i, h in enumerate(encabezados):
            if h and ("reg" in str(h).lower() or "siaf" in str(h).lower()):
                idx_reg = i
                break
        
        if idx_reg == -1:
            messagebox.showwarning("Advertencia", "No se encontró la columna 'Reg' o 'Reg Siaf'. Se agregará al final.")
            idx_reg = len(encabezados)

        # Insertar nuevo encabezado
        nuevos_encabezados = encabezados[:idx_reg] + ["prueba"] + encabezados[idx_reg:]
        
        # Procesar filas
        for tabla in todas_las_tablas:
            for fila in tabla[1:]: # Saltar encabezados de cada tabla
                if len(fila) > 0 and any(fila): # Ignorar filas vacías
                    # Asegurar que la fila tenga la misma longitud que los encabezados
                    fila_ajustada = list(fila) + [""] * (len(encabezados) - len(fila))
                    
                    # Insertar el valor "test" (o vacío si es B09574)
                    valor_prueba = "test"
                    # Buscar si el código interno es B09574 en cualquier celda de la fila
                    if any("B09574" in str(celda) for celda in fila_ajustada):
                        valor_prueba = ""
                    
                    nueva_fila = fila_ajustada[:idx_reg] + [valor_prueba] + fila_ajustada[idx_reg:]
                    datos.append(nueva_fila)

        # 3. Generar el nuevo PDF con ReportLab
        ruta_salida = filedialog.asksaveasfilename(
            title="Guardar nuevo PDF como",
            defaultextension=".pdf",
            filetypes=[("Archivos PDF", "*.pdf")],
            initialfile="reporte_editado.pdf"
        )
        
        if not ruta_salida:
            return # El usuario canceló

        doc = SimpleDocTemplate(ruta_salida, pagesize=landscape(letter), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        elements = []
        
        styles = getSampleStyleSheet()
        titulo = Paragraph("Reporte Editado con Columna 'prueba'", styles['Title'])
        elements.append(titulo)
        elements.append(Spacer(1, 12))

        # Crear la tabla para ReportLab
        data_para_tabla = [nuevos_encabezados] + datos
        
        # Ajustar el tamaño de las columnas (opcional, para que se vea bien)
        # Esto es un cálculo simple, puede necesitar ajustes según el contenido
        col_widths = [max(len(str(item)) for item in col) * 6 for col in zip(*data_para_tabla)]
        
        # Limitar el ancho máximo para evitar desbordes
        max_ancho = (landscape(letter)[0] - 40) / len(nuevos_encabezados)
        col_widths = [min(w, max_ancho) for w in col_widths]

        t = Table(data_para_tabla, colWidths=col_widths, repeatRows=1)
        
        # Estilo de la tabla
        estilo_tabla = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 6), # Fuente más pequeña para los datos
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ])
        
        # Resaltar la fila de B09574 si existe (opcional)
        for i, fila in enumerate(datos):
            if any("B09574" in str(celda) for celda in fila):
                estilo_tabla.add('BACKGROUND', (0, i+1), (-1, i+1), colors.lightcoral)
        
        t.setStyle(estilo_tabla)
        elements.append(t)

        doc.build(elements)
        
        messagebox.showinfo("Éxito", f"PDF generado exitosamente en:\n{ruta_salida}")

    except Exception as e:
        messagebox.showerror("Error", f"Ocurrió un error al procesar el PDF:\n{str(e)}")

# --- Configuración de la Interfaz Gráfica ---
ventana = tk.Tk()
ventana.title("Editor de PDF - Agregar Columna")
ventana.geometry("600x200")
ventana.resizable(False, False)

frame = tk.Frame(ventana, padx=20, pady=20)
frame.pack(expand=True, fill="both")

tk.Label(frame, text="Selecciona el archivo PDF a editar:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))

frame_ruta = tk.Frame(frame)
frame_ruta.pack(fill="x", pady=(0, 15))

entry_ruta = tk.Entry(frame_ruta, width=60)
entry_ruta.pack(side="left", padx=(0, 10), fill="x", expand=True)

btn_buscar = tk.Button(frame_ruta, text="Buscar...", command=seleccionar_archivo, bg="#e0e0e0")
btn_buscar.pack(side="right")

btn_procesar = tk.Button(frame, text="Procesar y Generar Nuevo PDF", command=procesar_pdf, bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), pady=10)
btn_procesar.pack(fill="x")

tk.Label(frame, text="Nota: El programa extrae las tablas y genera un nuevo PDF limpio.\nEl formato visual puede variar respecto al original.", font=("Arial", 8, "italic"), fg="gray").pack(pady=(15, 0))

ventana.mainloop()