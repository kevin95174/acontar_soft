import tkinter as tk
from tkinter import ttk, PhotoImage

ICONOXLS_PATH = "img/excel.png"
ICONOPDF_PATH = "img/pdf.png"

def botones(frame, 
            exportar_datos_func=None, 
            generar_pdf_func=None, 
            filtrar=None,
            lista=None,
            # Botones
            excel=True, 
            pdf=True, 
            csv=True):
    
    
    iconopdf = PhotoImage(file="img/pdf.png")
    iconobus = PhotoImage(file=ICONOPDF_PATH)
    
    if excel:
        # Crear botón de exportar a Excel
        iconoxls = PhotoImage(file="img/excel.png")    
        btnCsv = ttk.Button(frame, text="Exportar Excel", image=iconoxls, compound="left", command=exportar_datos_func)
        btnCsv.grid(row=0, column=4, padx=1, pady=5, sticky='ew')

    if csv:
        # Crear botón de exportar a Csv
        iconoxls = PhotoImage(file="img/excel.png")   
        btnCsv = ttk.Button(frame, text="Exportar csv", image=iconoxls, compound="left", command=exportar_datos_func)
        btnCsv.grid(row=0, column=4, padx=1, pady=5, sticky='ew')
    
    if pdf:
        # Crear botón de exportar a PDF
        btnPdf = ttk.Button(frame, text="Exportar PDF", image=iconopdf, compound="left", command=generar_pdf_func)
        btnPdf.grid(row=0, column=5, padx=1, pady=5, sticky='ew')

    crit = tk.StringVar()
    camp = tk.StringVar()

    lblCri = ttk.Label(frame, text="Criterio").grid(row=0, column=0, padx=5, pady=1, sticky='ew')
                
        # Combobox
    cbxCri = ttk.Combobox(frame, textvariable=crit, state="readonly", 
        values=lista).grid(row=0, column=1, padx=5, pady=1, sticky='ew')

            # Entrys
    etrCrit = ttk.Entry(frame, textvariable=camp).grid(row=0, column=2, padx=5, pady=1, sticky='ew')
                # Buttons
    btnCrit = ttk.Button(frame, text="Buscar", image=iconobus, compound="left",command=lambda:filtrar).grid(row=0, column=3, padx=5, pady=1, sticky='ew')        