import sys
import os

def resource_path(relative_path: str) -> str:
    """ Obtiene la ruta absoluta a un recurso, compatible con dev y PyInstaller """
    try:
        # PyInstaller crea una carpeta temporal o ajusta el path de recursos en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)