# utils/project_manager.py
import configparser
import os
import sys

CONFIG_PATH = "config.ini"

DEFAULT_PROJECTS = {
    "proyecto_1": {
        "id": "proyecto_1",
        "name": "Proyecto 1 (api.acontarsac.com)",
        "api_url": "https://api.acontarsac.com",
        "photos_url": "https://admin.acontarsac.com/public",
        "db_file": "orap2022.db",
    },
    "proyecto_2": {
        "id": "proyecto_2",
        "name": "Proyecto 2 (project2.acontarsac.com)",
        "api_url": "https://project2.acontarsac.com",
        "photos_url": "https://project2.acontarsac.com/public",
        "db_file": "orap_project2.db",
    },
}


class ProjectManager:
    """Gestiona múltiples proyectos/servidores permitiendo alternar entre URLs y bases de datos locales."""

    @staticmethod
    def _get_base_dir() -> str:
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    @classmethod
    def _get_config_path(cls) -> str:
        return os.path.join(cls._get_base_dir(), CONFIG_PATH)

    @classmethod
    def load_projects(cls) -> dict:
        """Carga los proyectos configurados desde config.ini. Si no existen, los crea con valores por defecto."""
        config_file = cls._get_config_path()
        config = configparser.ConfigParser()

        if os.path.exists(config_file):
            try:
                config.read(config_file, encoding="utf-8")
            except Exception:
                config.read(config_file)

        modificado = False
        if not config.has_section("Projects"):
            config.add_section("Projects")
            config.set("Projects", "active_project", "proyecto_1")
            modificado = True

        projects = {}
        for proj_id, default_data in DEFAULT_PROJECTS.items():
            sec_name = f"Project_{proj_id}"
            if not config.has_section(sec_name):
                config.add_section(sec_name)
                config.set(sec_name, "name", default_data["name"])
                config.set(sec_name, "api_url", default_data["api_url"])
                config.set(sec_name, "photos_url", default_data["photos_url"])
                config.set(sec_name, "db_file", default_data["db_file"])
                modificado = True

            projects[proj_id] = {
                "id": proj_id,
                "name": config.get(sec_name, "name", fallback=default_data["name"]),
                "api_url": config.get(sec_name, "api_url", fallback=default_data["api_url"]).rstrip("/"),
                "photos_url": config.get(sec_name, "photos_url", fallback=default_data["photos_url"]).rstrip("/"),
                "db_file": config.get(sec_name, "db_file", fallback=default_data["db_file"]),
            }

        # Leer cualquier otro proyecto adicional definido manualmente por el usuario
        for sec in config.sections():
            if sec.startswith("Project_") and sec.replace("Project_", "") not in projects:
                p_id = sec.replace("Project_", "")
                projects[p_id] = {
                    "id": p_id,
                    "name": config.get(sec, "name", fallback=p_id),
                    "api_url": config.get(sec, "api_url", fallback="https://api.acontarsac.com").rstrip("/"),
                    "photos_url": config.get(sec, "photos_url", fallback="https://admin.acontarsac.com/public").rstrip("/"),
                    "db_file": config.get(sec, "db_file", fallback=f"orap_{p_id}.db"),
                }

        if modificado:
            try:
                with open(config_file, "w", encoding="utf-8") as f:
                    config.write(f)
            except Exception as e:
                print(f"Nota: No se pudo escribir config.ini: {e}")

        return projects

    @classmethod
    def get_active_project_id(cls) -> str:
        config_file = cls._get_config_path()
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            try:
                config.read(config_file, encoding="utf-8")
            except Exception:
                config.read(config_file)
        if config.has_section("Projects"):
            return config.get("Projects", "active_project", fallback="proyecto_1")
        return "proyecto_1"

    @classmethod
    def get_active_project(cls) -> dict:
        projects = cls.load_projects()
        active_id = cls.get_active_project_id()
        if active_id in projects:
            return projects[active_id]
        return projects.get("proyecto_1", DEFAULT_PROJECTS["proyecto_1"])

    @classmethod
    def set_active_project(cls, project_id: str):
        """Guarda el proyecto activo en config.ini y actualiza la ruta de la base de datos."""
        config_file = cls._get_config_path()
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            try:
                config.read(config_file, encoding="utf-8")
            except Exception:
                config.read(config_file)

        if not config.has_section("Projects"):
            config.add_section("Projects")
        config.set("Projects", "active_project", str(project_id))

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                config.write(f)
        except Exception as e:
            print(f"Nota al guardar proyecto activo: {e}")

        # Notificar a conex.py del cambio de base de datos activa
        try:
            from db.conex import set_database_path
            set_database_path(cls.get_active_db_path())
        except Exception:
            pass

    @classmethod
    def get_active_db_path(cls) -> str:
        """Devuelve la ruta absoluta completa al archivo SQLite del proyecto activo."""
        proj = cls.get_active_project()
        base_dir = cls._get_base_dir()
        db_file = proj.get("db_file", "orap2022.db")
        db_dir = os.path.join(base_dir, "db")
        os.makedirs(db_dir, exist_ok=True)
        return os.path.normpath(os.path.join(db_dir, db_file))

    @classmethod
    def get_active_api_url(cls) -> str:
        """Devuelve la URL base de la API del proyecto activo."""
        proj = cls.get_active_project()
        return proj.get("api_url", "https://api.acontarsac.com")

    @classmethod
    def get_active_photos_url(cls) -> str:
        """Devuelve la URL base de fotos del proyecto activo."""
        proj = cls.get_active_project()
        return proj.get("photos_url", "https://admin.acontarsac.com/public")
