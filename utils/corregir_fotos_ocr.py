"""
Corrige el nombre de las fotos leyendo el texto estampado en la propia imagen.

Cada foto trae un recuadro con:
    FECHA: 09/10/2026 09:21
    UBICACION: ...
    BIEN: PIZARRA ACRILICA
    COD. INT: 4830
    COD. PAT: 746473050010

El script lee ese texto con el OCR integrado de Windows (sin instalar programas
externos) y renombra cada archivo como:  <COD_INT>_FOTO_<indice>.<ext>

- El indice cuenta 1, 2, 3... por codigo, ordenado por la fecha/hora estampada.
- Las fotos donde no se logra leer el codigo se mueven a la subcarpeta "sin_leer".
- Primero SIMULA y muestra el resultado; solo renombra cuando se confirma.
- Se guarda un CSV con el cambio antiguo -> nuevo para poder revertir.
- Tambien separa las fotos duplicadas (contenido identico): las unicas quedan en la
  carpeta y las repetidas se mueven a la subcarpeta "duplicadas". Conviene hacerlo
  ANTES de renombrar, para que una misma foto no reciba dos numeros distintos.

Uso con interfaz (sin argumentos):
    python corregir_fotos_ocr.py

Uso por terminal:
    python corregir_fotos_ocr.py "C:/ruta/a/las/fotos"            (simulacion)
    python corregir_fotos_ocr.py "C:/ruta/a/las/fotos" --aplicar  (renombra)
    python corregir_fotos_ocr.py "C:/ruta/a/las/fotos" --duplicadas [--aplicar]

Dependencias (una sola vez, dentro del venv):
    pip install pillow winrt-runtime winrt-Windows.Media.Ocr ^
        winrt-Windows.Graphics.Imaging winrt-Windows.Storage.Streams ^
        winrt-Windows.Globalization winrt-Windows.Foundation ^
        winrt-Windows.Foundation.Collections
"""
import argparse
import asyncio
import csv
import hashlib
import os
import queue
import re
import shutil
import sys
import threading
from collections import defaultdict
from datetime import datetime

from PIL import Image, ImageOps

EXTENSIONES = {".jpg", ".jpeg", ".png"}
RE_COD_INT = re.compile(r"INT\.?\s*[:;.,]?\s*(\d{1,12})", re.IGNORECASE)
RE_FECHA = re.compile(
    r"(\d{2})\s*/\s*(\d{2})\s*/\s*(\d{4})\s+(\d{1,2})\s*[:.]\s*(\d{2})"
)

_engine = None


def _crear_motor_ocr():
    from winrt.windows.globalization import Language
    from winrt.windows.media.ocr import OcrEngine

    motor = OcrEngine.try_create_from_user_profile_languages()
    if motor is None:
        motor = OcrEngine.try_create_from_language(Language("en-US"))
    if motor is None:
        raise RuntimeError(
            "Windows no tiene ningun idioma de OCR instalado "
            "(Configuracion > Hora e idioma > Idioma y region)."
        )
    return motor


async def _ocr_imagen(img_pil):
    """Devuelve el texto reconocido de una imagen PIL."""
    global _engine
    from winrt.windows.graphics.imaging import BitmapAlphaMode, BitmapPixelFormat, SoftwareBitmap
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage.streams import DataWriter

    if _engine is None:
        _engine = _crear_motor_ocr()

    rgba = img_pil.convert("RGBA")
    # El motor de Windows rechaza imagenes mayores a OcrEngine.max_image_dimension.
    maxd = OcrEngine.max_image_dimension
    if max(rgba.size) > maxd:
        rgba.thumbnail((maxd, maxd))

    r, g, b, a = rgba.split()
    bgra = Image.merge("RGBA", (b, g, r, a))  # Windows espera orden BGRA

    writer = DataWriter()
    writer.write_bytes(bgra.tobytes())
    bitmap = SoftwareBitmap.create_copy_from_buffer(
        writer.detach_buffer(),
        BitmapPixelFormat.BGRA8,
        rgba.width,
        rgba.height,
        BitmapAlphaMode.PREMULTIPLIED,
    )
    resultado = await _engine.recognize_async(bitmap)
    return resultado.text


def _leer_texto(ruta):
    """OCR de la franja inferior (donde esta el recuadro) y, si falla, de toda la foto."""
    with Image.open(ruta) as im:
        im = ImageOps.exif_transpose(im)
        w, h = im.size
        franja = im.crop((0, int(h * 0.62), w, h))
        if franja.width < 1600:
            f = 1600 / franja.width
            franja = franja.resize((int(franja.width * f), int(franja.height * f)), Image.LANCZOS)
        texto = asyncio.run(_ocr_imagen(franja))
        if not RE_COD_INT.search(texto):
            texto += "\n" + asyncio.run(_ocr_imagen(im))
    return texto


def analizar(ruta):
    """Devuelve (cod_int, fecha_datetime) leidos del texto estampado."""
    texto = _leer_texto(ruta)
    m = RE_COD_INT.search(texto)
    cod = m.group(1) if m else None

    fecha = None
    f = RE_FECHA.search(texto)
    if f:
        d, mes, a, hh, mm = (int(x) for x in f.groups())
        try:
            fecha = datetime(a, mes, d, hh, mm)
        except ValueError:
            fecha = None
    return cod, fecha


# ---------------------------------------------------------------------------
# Logica comun (la usan la terminal y la interfaz)
# ---------------------------------------------------------------------------
def listar_fotos(carpeta):
    return sorted(
        f for f in os.listdir(carpeta)
        if os.path.isfile(os.path.join(carpeta, f)) and os.path.splitext(f)[1].lower() in EXTENSIONES
    )


def planificar(carpeta, progreso=None, cancelar=None):
    """
    Lee todas las fotos de la carpeta y calcula los nombres nuevos (sin tocar nada).

    progreso(i, total, nombre, cod, fecha, motivo): se llama tras leer cada foto.
    cancelar: threading.Event opcional para abortar.
    Devuelve (cambios, sin_leer):
        cambios  = [(original, nuevo, cod, fecha)]
        sin_leer = [(original, motivo)]
    """
    archivos = listar_fotos(carpeta)
    por_codigo = defaultdict(list)  # cod -> [(fecha, nombre_original)]
    sin_leer = []

    for i, nombre in enumerate(archivos, 1):
        if cancelar is not None and cancelar.is_set():
            break
        ruta = os.path.join(carpeta, nombre)
        cod = fecha = None
        motivo = ""
        try:
            cod, fecha = analizar(ruta)
            if not cod:
                motivo = "sin codigo legible"
        except Exception as e:
            motivo = f"error: {e}"

        if motivo:
            sin_leer.append((nombre, motivo))
        else:
            if fecha is None:
                fecha = datetime.fromtimestamp(os.path.getmtime(ruta))
            por_codigo[cod].append((fecha, nombre))
        if progreso:
            progreso(i, len(archivos), nombre, cod, fecha, motivo)

    cambios = []
    for cod, items in por_codigo.items():
        items.sort(key=lambda t: (t[0], t[1]))
        for idx, (fecha, nombre) in enumerate(items, 1):
            ext = os.path.splitext(nombre)[1].lower()
            cambios.append((nombre, f"{cod}_FOTO_{idx}{ext}", cod, fecha))
    cambios.sort(key=lambda c: c[1])
    return cambios, sin_leer


def aplicar(carpeta, cambios, sin_leer, nombre_sin_leer="sin_leer"):
    """Renombra las fotos y mueve las ilegibles. Devuelve la ruta del CSV de registro."""
    # 1) Mover las que no se pudieron leer, para que no choquen con nombres nuevos.
    if sin_leer:
        destino = os.path.join(carpeta, nombre_sin_leer)
        os.makedirs(destino, exist_ok=True)
        for nombre, _ in sin_leer:
            shutil.move(os.path.join(carpeta, nombre), os.path.join(destino, nombre))

    # 2) Renombrar en dos fases (via nombre temporal) para evitar pisar archivos.
    temporales = []
    for n, (viejo, nuevo, *_resto) in enumerate(cambios):
        tmp = f"__tmp_{n}_{viejo}"
        os.rename(os.path.join(carpeta, viejo), os.path.join(carpeta, tmp))
        temporales.append((tmp, nuevo))
    for tmp, nuevo in temporales:
        os.rename(os.path.join(carpeta, tmp), os.path.join(carpeta, nuevo))

    log = os.path.join(carpeta, "renombrado_log.csv")
    with open(log, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["original", "nuevo"])
        for viejo, nuevo, *_resto in cambios:
            w.writerow([viejo, nuevo])
        for nombre, _ in sin_leer:
            w.writerow([nombre, f"{nombre_sin_leer}/{nombre}"])
    return log


# ---------------------------------------------------------------------------
# Fotos duplicadas (contenido identico)
# ---------------------------------------------------------------------------
def _hash_archivo(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def buscar_duplicadas(carpeta, progreso=None, cancelar=None):
    """
    Busca fotos con contenido identico (mismo SHA-256) en la carpeta.

    En cada grupo se conserva la primera por orden alfabetico del nombre.
    progreso(i, total, nombre): se llama tras revisar cada foto candidata.
    Devuelve [(conservada, [duplicadas])] solo para los grupos con repetidas.
    """
    archivos = listar_fotos(carpeta)
    por_tamano = defaultdict(list)
    for nombre in archivos:
        por_tamano[os.path.getsize(os.path.join(carpeta, nombre))].append(nombre)

    # Solo hace falta calcular hash de archivos que comparten tamano con otro.
    candidatos = [n for grupo in por_tamano.values() if len(grupo) > 1 for n in grupo]
    por_hash = defaultdict(list)
    for i, nombre in enumerate(candidatos, 1):
        if cancelar is not None and cancelar.is_set():
            break
        por_hash[_hash_archivo(os.path.join(carpeta, nombre))].append(nombre)
        if progreso:
            progreso(i, len(candidatos), nombre)

    grupos = []
    for nombres in por_hash.values():
        if len(nombres) > 1:
            nombres.sort()
            grupos.append((nombres[0], nombres[1:]))
    grupos.sort(key=lambda g: g[0])
    return grupos


def mover_duplicadas(carpeta, grupos, nombre_dest="duplicadas"):
    """Mueve las duplicadas a una subcarpeta. Devuelve la ruta del CSV de registro."""
    destino = os.path.join(carpeta, nombre_dest)
    os.makedirs(destino, exist_ok=True)
    filas = []
    for conservada, duplicadas in grupos:
        for nombre in duplicadas:
            final = nombre
            base, ext = os.path.splitext(nombre)
            n = 1
            while os.path.exists(os.path.join(destino, final)):
                final = f"{base}_{n}{ext}"
                n += 1
            shutil.move(os.path.join(carpeta, nombre), os.path.join(destino, final))
            filas.append((nombre, f"{nombre_dest}/{final}", conservada))

    log = os.path.join(carpeta, "duplicadas_log.csv")
    with open(log, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["original", "movida_a", "foto_que_se_conserva"])
        w.writerows(filas)
    return log


# ---------------------------------------------------------------------------
# Terminal
# ---------------------------------------------------------------------------
def main_cli(args):
    carpeta = os.path.abspath(args.carpeta)
    if not os.path.isdir(carpeta):
        sys.exit(f"No existe la carpeta: {carpeta}")
    print(f"{len(listar_fotos(carpeta))} fotos encontradas en {carpeta}\n")

    if args.duplicadas:
        grupos = buscar_duplicadas(carpeta, lambda i, t, n: print(f"[{i}/{t}] {n}"))
        total = sum(len(d) for _, d in grupos)
        print(f"\n--- RESUMEN ---\nGrupos con repetidas: {len(grupos)} | Fotos duplicadas: {total}")
        for conservada, duplicadas in grupos:
            print(f"  se conserva {conservada}")
            for d in duplicadas:
                print(f"      duplicada: {d}  ->  duplicadas/")
        if not args.aplicar:
            print("\nSimulacion: no se modifico nada. Agrega --aplicar para mover las duplicadas.")
        elif grupos:
            print(f"\nListo. Registro guardado en {mover_duplicadas(carpeta, grupos)}")
        return

    def progreso(i, total, nombre, cod, fecha, motivo):
        if motivo:
            print(f"[{i}/{total}] {nombre}: {motivo}")
        else:
            print(f"[{i}/{total}] {nombre}: COD. INT {cod}  {fecha:%d/%m/%Y %H:%M}")

    cambios, sin_leer = planificar(carpeta, progreso)

    print("\n--- RESUMEN ---")
    print(f"A renombrar: {len(cambios)} | Sin leer: {len(sin_leer)}")
    for viejo, nuevo, *_resto in cambios:
        print(f"  {viejo}  ->  {nuevo}")
    for nombre, _ in sin_leer:
        print(f"  {nombre}  ->  {args.sin_leer}/")

    if not args.aplicar:
        print("\nSimulacion: no se modifico nada. Agrega --aplicar para renombrar.")
        return
    log = aplicar(carpeta, cambios, sin_leer, args.sin_leer)
    print(f"\nListo. Registro guardado en {log}")


# ---------------------------------------------------------------------------
# Interfaz grafica (tkinter, incluido con Python)
# ---------------------------------------------------------------------------
def main_gui():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("Herramientas de fotos de inventario")
    root.geometry("900x560")
    root.minsize(700, 400)

    ruta_var = tk.StringVar()
    estado_var = tk.StringVar(value="Elige la carpeta con las fotos y pulsa Analizar.")
    cola = queue.Queue()
    cancelar = threading.Event()
    plan = {"carpeta": None, "cambios": [], "sin_leer": []}

    # --- Selector de carpeta ---
    fila1 = ttk.Frame(root, padding=(10, 10, 10, 4))
    fila1.pack(fill="x")
    ttk.Label(fila1, text="Carpeta:").pack(side="left")
    ttk.Entry(fila1, textvariable=ruta_var).pack(side="left", fill="x", expand=True, padx=6)

    def examinar():
        d = filedialog.askdirectory(title="Carpeta con las fotos")
        if d:
            ruta_var.set(os.path.normpath(d))

    ttk.Button(fila1, text="Examinar...", command=examinar).pack(side="left")

    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=4, pady=(4, 0))
    tab1 = ttk.Frame(nb)
    tab2 = ttk.Frame(nb)
    nb.add(tab1, text="Renombrar por OCR")
    nb.add(tab2, text="Duplicadas")

    # --- Botones ---
    fila2 = ttk.Frame(tab1, padding=(10, 4))
    fila2.pack(fill="x")
    btn_analizar = ttk.Button(fila2, text="1. Analizar (no cambia nada)")
    btn_analizar.pack(side="left")
    btn_aplicar = ttk.Button(fila2, text="2. Aplicar cambios", state="disabled")
    btn_aplicar.pack(side="left", padx=6)
    btn_cancelar = ttk.Button(fila2, text="Cancelar", state="disabled", command=cancelar.set)
    btn_cancelar.pack(side="left")

    # --- Tabla ---
    cuerpo = ttk.Frame(tab1, padding=(10, 4))
    cuerpo.pack(fill="both", expand=True)
    cols = ("original", "nuevo", "cod", "fecha")
    tabla = ttk.Treeview(cuerpo, columns=cols, show="headings", selectmode="browse")
    for c, titulo, ancho in (
        ("original", "Nombre actual", 300),
        ("nuevo", "Nombre nuevo", 220),
        ("cod", "Cod. interno", 90),
        ("fecha", "Fecha en la foto", 130),
    ):
        tabla.heading(c, text=titulo)
        tabla.column(c, width=ancho, anchor="w")
    tabla.tag_configure("sin", foreground="#b00020")
    sb = ttk.Scrollbar(cuerpo, orient="vertical", command=tabla.yview)
    tabla.configure(yscrollcommand=sb.set)
    tabla.pack(side="left", fill="both", expand=True)
    sb.pack(side="left", fill="y")

    # --- Barra inferior ---
    pie = ttk.Frame(tab1, padding=(10, 4, 10, 10))
    pie.pack(fill="x")
    barra = ttk.Progressbar(pie, mode="determinate")
    barra.pack(fill="x")
    ttk.Label(pie, textvariable=estado_var).pack(anchor="w", pady=(4, 0))

    def poner_ocupado(ocupado):
        btn_analizar.config(state="disabled" if ocupado else "normal")
        btn_cancelar.config(state="normal" if ocupado else "disabled")
        if ocupado:
            btn_aplicar.config(state="disabled")

    def trabajo(carpeta):
        try:
            def progreso(i, total, nombre, cod, fecha, motivo):
                cola.put(("prog", i, total, nombre, cod, fecha, motivo))
            cambios, sin_leer = planificar(carpeta, progreso, cancelar)
            cola.put(("fin", carpeta, cambios, sin_leer, cancelar.is_set()))
        except Exception as e:  # p. ej. falta el motor OCR
            cola.put(("error", str(e)))

    def analizar_click():
        carpeta = ruta_var.get().strip()
        if not os.path.isdir(carpeta):
            messagebox.showwarning("Carpeta", "Elige una carpeta valida.")
            return
        if not listar_fotos(carpeta):
            messagebox.showinfo("Carpeta", "No hay fotos .jpg/.jpeg/.png en esa carpeta.")
            return
        cancelar.clear()
        tabla.delete(*tabla.get_children())
        barra["value"] = 0
        estado_var.set("Leyendo fotos...")
        poner_ocupado(True)
        threading.Thread(target=trabajo, args=(carpeta,), daemon=True).start()

    def revisar_cola():
        try:
            while True:
                msg = cola.get_nowait()
                if msg[0] == "prog":
                    _, i, total, nombre, cod, fecha, motivo = msg
                    barra["maximum"] = total
                    barra["value"] = i
                    estado_var.set(f"Leyendo {i} de {total}: {nombre}")
                elif msg[0] == "fin":
                    _, carpeta, cambios, sin_leer, cancelado = msg
                    mostrar_plan(carpeta, cambios, sin_leer, cancelado)
                elif msg[0] == "error":
                    poner_ocupado(False)
                    estado_var.set("Error.")
                    messagebox.showerror("Error", msg[1])
        except queue.Empty:
            pass
        root.after(100, revisar_cola)

    def mostrar_plan(carpeta, cambios, sin_leer, cancelado):
        tabla.delete(*tabla.get_children())
        for viejo, nuevo, cod, fecha in cambios:
            tabla.insert("", "end", values=(viejo, nuevo, cod, f"{fecha:%d/%m/%Y %H:%M}"))
        for nombre, motivo in sin_leer:
            tabla.insert("", "end", values=(nombre, "-> carpeta sin_leer", "", motivo), tags=("sin",))
        poner_ocupado(False)
        if cancelado:
            estado_var.set("Analisis cancelado.")
            return
        plan.update(carpeta=carpeta, cambios=cambios, sin_leer=sin_leer)
        estado_var.set(
            f"Listo: {len(cambios)} fotos a renombrar, {len(sin_leer)} sin leer (en rojo). "
            "Revisa la lista y pulsa 'Aplicar cambios'."
        )
        if cambios or sin_leer:
            btn_aplicar.config(state="normal")

    def aplicar_click():
        n, m = len(plan["cambios"]), len(plan["sin_leer"])
        if not messagebox.askyesno(
            "Confirmar",
            f"Se renombraran {n} fotos y se moveran {m} a 'sin_leer'.\n\n"
            "Se guardara un registro (renombrado_log.csv) para poder revertir.\n"
            "¿Continuar?",
        ):
            return
        try:
            log = aplicar(plan["carpeta"], plan["cambios"], plan["sin_leer"])
        except Exception as e:
            messagebox.showerror("Error al renombrar", str(e))
            return
        btn_aplicar.config(state="disabled")
        plan.update(cambios=[], sin_leer=[])
        estado_var.set("Cambios aplicados.")
        messagebox.showinfo("Listo", f"Fotos renombradas.\n\nRegistro: {log}")

    # ===================== Pestana 2: duplicadas =====================
    estado2_var = tk.StringVar(
        value="Busca fotos con contenido identico; las repetidas se mueven a la carpeta 'duplicadas'."
    )
    cola2 = queue.Queue()
    cancelar2 = threading.Event()
    plan2 = {"carpeta": None, "grupos": []}

    fila_d = ttk.Frame(tab2, padding=(10, 8, 10, 4))
    fila_d.pack(fill="x")
    btn_buscar = ttk.Button(fila_d, text="1. Buscar duplicadas (no cambia nada)")
    btn_buscar.pack(side="left")
    btn_mover = ttk.Button(fila_d, text="2. Mover duplicadas", state="disabled")
    btn_mover.pack(side="left", padx=6)
    btn_cancelar2 = ttk.Button(fila_d, text="Cancelar", state="disabled", command=cancelar2.set)
    btn_cancelar2.pack(side="left")

    cuerpo_d = ttk.Frame(tab2, padding=(10, 4))
    cuerpo_d.pack(fill="both", expand=True)
    tabla2 = ttk.Treeview(cuerpo_d, columns=("conserva", "dup"), show="headings", selectmode="browse")
    tabla2.heading("conserva", text="Foto que se conserva")
    tabla2.heading("dup", text="Duplicada (se mueve a 'duplicadas')")
    tabla2.column("conserva", width=380, anchor="w")
    tabla2.column("dup", width=380, anchor="w")
    sb2 = ttk.Scrollbar(cuerpo_d, orient="vertical", command=tabla2.yview)
    tabla2.configure(yscrollcommand=sb2.set)
    tabla2.pack(side="left", fill="both", expand=True)
    sb2.pack(side="left", fill="y")

    pie_d = ttk.Frame(tab2, padding=(10, 4, 10, 10))
    pie_d.pack(fill="x")
    barra2 = ttk.Progressbar(pie_d, mode="determinate")
    barra2.pack(fill="x")
    ttk.Label(pie_d, textvariable=estado2_var).pack(anchor="w", pady=(4, 0))

    def ocupado2(ocupado):
        btn_buscar.config(state="disabled" if ocupado else "normal")
        btn_cancelar2.config(state="normal" if ocupado else "disabled")
        if ocupado:
            btn_mover.config(state="disabled")

    def trabajo2(carpeta):
        try:
            def progreso(i, total, nombre):
                cola2.put(("prog", i, total, nombre))
            grupos = buscar_duplicadas(carpeta, progreso, cancelar2)
            cola2.put(("fin", carpeta, grupos, cancelar2.is_set()))
        except Exception as e:
            cola2.put(("error", str(e)))

    def buscar_click():
        carpeta = ruta_var.get().strip()
        if not os.path.isdir(carpeta):
            messagebox.showwarning("Carpeta", "Elige una carpeta valida.")
            return
        if not listar_fotos(carpeta):
            messagebox.showinfo("Carpeta", "No hay fotos .jpg/.jpeg/.png en esa carpeta.")
            return
        cancelar2.clear()
        tabla2.delete(*tabla2.get_children())
        barra2["value"] = 0
        estado2_var.set("Comparando fotos...")
        ocupado2(True)
        threading.Thread(target=trabajo2, args=(carpeta,), daemon=True).start()

    def revisar_cola2():
        try:
            while True:
                msg = cola2.get_nowait()
                if msg[0] == "prog":
                    _, i, total, nombre = msg
                    barra2["maximum"] = total
                    barra2["value"] = i
                    estado2_var.set(f"Comparando {i} de {total}: {nombre}")
                elif msg[0] == "fin":
                    _, carpeta, grupos, cancelado = msg
                    tabla2.delete(*tabla2.get_children())
                    for conservada, duplicadas in grupos:
                        for d in duplicadas:
                            tabla2.insert("", "end", values=(conservada, d))
                    ocupado2(False)
                    if cancelado:
                        estado2_var.set("Busqueda cancelada.")
                    else:
                        total = sum(len(d) for _, d in grupos)
                        plan2.update(carpeta=carpeta, grupos=grupos)
                        if total:
                            estado2_var.set(
                                f"{total} fotos duplicadas en {len(grupos)} grupos. "
                                "Revisa la lista y pulsa 'Mover duplicadas'."
                            )
                            btn_mover.config(state="normal")
                        else:
                            estado2_var.set("No hay fotos duplicadas: todas son unicas.")
                elif msg[0] == "error":
                    ocupado2(False)
                    estado2_var.set("Error.")
                    messagebox.showerror("Error", msg[1])
        except queue.Empty:
            pass
        root.after(100, revisar_cola2)

    def mover_click():
        total = sum(len(d) for _, d in plan2["grupos"])
        if not messagebox.askyesno(
            "Confirmar",
            f"Se moveran {total} fotos duplicadas a la carpeta 'duplicadas'.\n"
            "Las fotos unicas se quedan donde estan.\n\n"
            "Se guardara un registro (duplicadas_log.csv).\n¿Continuar?",
        ):
            return
        try:
            log = mover_duplicadas(plan2["carpeta"], plan2["grupos"])
        except Exception as e:
            messagebox.showerror("Error al mover", str(e))
            return
        btn_mover.config(state="disabled")
        plan2.update(grupos=[])
        tabla2.delete(*tabla2.get_children())
        estado2_var.set("Duplicadas movidas.")
        messagebox.showinfo("Listo", f"Duplicadas movidas.\n\nRegistro: {log}")

    btn_buscar.config(command=buscar_click)
    btn_mover.config(command=mover_click)
    root.after(100, revisar_cola2)

    btn_analizar.config(command=analizar_click)
    btn_aplicar.config(command=aplicar_click)
    root.after(100, revisar_cola)
    root.mainloop()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carpeta", nargs="?", help="Carpeta con las fotos (si se omite, se abre la interfaz)")
    ap.add_argument("--aplicar", action="store_true", help="Renombrar de verdad (por defecto solo simula)")
    ap.add_argument("--sin-leer", default="sin_leer", help="Subcarpeta para fotos sin codigo legible")
    ap.add_argument("--duplicadas", action="store_true",
                    help="En vez de renombrar, separar las fotos duplicadas (contenido identico)")
    args = ap.parse_args()

    if args.carpeta is None:
        main_gui()
    else:
        main_cli(args)


if __name__ == "__main__":
    main()
