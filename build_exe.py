"""
Script de compilacion automatizada para generar el ejecutable de AEC (Acontar Especialistas Contables).
Uso:
    python build_exe.py
"""

import os
import sys
import shutil
import subprocess

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print("=" * 60)
    print(">>> INICIANDO COMPILACION DE EJECUTABLE AEC")
    print("=" * 60)

    # 1. Rutas
    dist_dir = os.path.join(base_dir, "dist", "AEC")
    build_dir = os.path.join(base_dir, "build")
    spec_file = os.path.join(base_dir, "root.spec")

    # Detectar ejecutable de PyInstaller
    venv_pyinstaller = os.path.join(base_dir, "venv", "Scripts", "pyinstaller.exe")
    if os.path.exists(venv_pyinstaller):
        pyinstaller_cmd = venv_pyinstaller
    else:
        pyinstaller_cmd = "pyinstaller"

    print(f"[*] Utilizando PyInstaller: {pyinstaller_cmd}")

    # 2. Respaldo preventivo de la base de datos en dist si ya existe
    dist_db = os.path.join(dist_dir, "db", "orap2022.db")
    backup_db = None
    if os.path.exists(dist_db):
        backup_db = os.path.join(base_dir, "db_dist_backup.bak")
        print(f"[*] Respaldando base de datos existente de dist...")
        shutil.copy2(dist_db, backup_db)

    # 3. Limpiar carpeta temporal build
    if os.path.exists(build_dir):
        print("[*] Limpiando directorio temporal 'build'...")
        try:
            shutil.rmtree(build_dir, ignore_errors=True)
        except Exception as e_clean:
            print(f"   Advertencia al limpiar build: {e_clean}")

    # 4. Ejecutar PyInstaller
    print(f"[*] Compilando con PyInstaller usando '{spec_file}'...")
    cmd = [pyinstaller_cmd, "--noconfirm", spec_file]
    resultado = subprocess.run(cmd)

    if resultado.returncode != 0:
        print("\n[ERROR] La compilacion con PyInstaller fallo.")
        if backup_db and os.path.exists(backup_db):
            os.remove(backup_db)
        sys.exit(1)

    print("\n[OK] Compilacion de PyInstaller finalizada con exito.")

    # 5. Asegurar estructura de carpetas de ejecucion en dist/AEC
    carpetas_runtime = [
        "photos",
        "exportar",
        "labels",
        "fichas_inventario",
        "reportes",
        "report_actas",
        "db",
        "data"
    ]
    for c in carpetas_runtime:
        ruta_c = os.path.join(dist_dir, c)
        os.makedirs(ruta_c, exist_ok=True)

    # 6. Base de datos: asegurar que este la mas reciente en dist/AEC/db/orap2022.db
    src_db = os.path.join(base_dir, "db", "orap2022.db")
    target_db = os.path.join(dist_dir, "db", "orap2022.db")
    if os.path.exists(src_db):
        shutil.copy2(src_db, target_db)
        print(f"[*] Base de datos sincronizada en: {target_db}")

    if backup_db and os.path.exists(backup_db):
        try:
            os.remove(backup_db)
        except Exception:
            pass

    # 7. Copiar config.ini si no existe o actualizar
    src_config = os.path.join(base_dir, "config.ini")
    target_config = os.path.join(dist_dir, "config.ini")
    if os.path.exists(src_config):
        shutil.copy2(src_config, target_config)
        print(f"[*] Archivo config.ini copiado a: {target_config}")

    # 8. Verificar que el ejecutable AEC.exe exista
    exe_path = os.path.join(dist_dir, "AEC.exe")
    if os.path.exists(exe_path):
        tamano_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("=" * 60)
        print(f"[EXITO] EJECUTABLE GENERADO:")
        print(f"   Ruta: {exe_path}")
        print(f"   Tamano: {tamano_mb:.2f} MB")
        print("=" * 60)
        print("Para distribuir la aplicacion, simplemente copia la carpeta 'dist\\AEC'.")
    else:
        print(f"[ALERTA] No se encontro 'AEC.exe' en {dist_dir}")

if __name__ == "__main__":
    main()
