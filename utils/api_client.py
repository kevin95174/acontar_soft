"""Cliente HTTP para el contrato de ApiManagerAcontarSac."""

import json
import ssl
import urllib.error
import urllib.request
from datetime import datetime

import requests


class ApiConnectionError(Exception):
    """La API no se pudo alcanzar o devolvió una respuesta no válida."""


class ApiManagerAcontarSacClient:
    BASE_URL = "https://api.acontarsac.com"
    PHOTOS_BASE_URL = "https://admin.acontarsac.com/public"

    ENDPOINTS = {
        "ping": "/query/response/ping",
        "initial_sync": "/query/response/initial_sync",
        "records_by_office": "/query/response/get_records_by_office",
        "dashboard": "/query/response/dashboard",
        "sync_records": "/query/response/sync_records",
        "sync_changes": "/query/response/sync_changes",
        # Esta es la ruta publicada actualmente por el servidor Laravel.
        "update_final_location": "/query/response/update_ubicacion_final",
        "uninventory_record": "/query/response/uninventory_record",
        "update_technical_details": "/query/response/update_technical_details",
        "create_location": "/query/response/create_or_update_location",
        "create_personnel": "/query/response/create_or_update_personnel",
        "create_surplus": "/query/response/create_or_update_surplus",
        "login": "/query/response/login",
        "validate_credentials": "/query/response/validate_credentials",
        "upload_photo": "/query/response/upload_photo",
    }

    def __init__(self, base_url=None, photos_base_url=None, timeout=30):
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.photos_base_url = (photos_base_url or self.PHOTOS_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = None

    def _ensure_session(self):
        """Garantiza que exista una sesión HTTP configurada con cabeceras JSON."""
        if not hasattr(self, "session") or self.session is None:
            self.session = requests.Session()
            self.session.headers.update({
                "Content-Type": "application/json",
                "Accept": "application/json",
            })

    def _post_json(self, endpoint_key: str, payload: dict) -> dict:
        """Envía una petición POST con JSON y devuelve {'status_code': int, 'data': dict}."""
        self._ensure_session()
        endpoint = self.ENDPOINTS.get(endpoint_key, endpoint_key)
        url = self.base_url + endpoint

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            try:
                data = response.json()
            except (json.JSONDecodeError, ValueError):
                data = {
                    "message": (
                        f"Respuesta no válida del servidor (HTTP {response.status_code}). "
                        f"Detalle: {response.text[:200]}"
                    )
                }
            return {
                "status_code": response.status_code,
                "data": data,
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 500,
                "data": {"message": f"Error de conexión HTTP: {e}"},
            }

    def get_photo_url(self, ruta_foto: str) -> str:
        """Devuelve la URL completa para descargar o visualizar la foto desde el servidor."""
        if not ruta_foto:
            return ""
        if ruta_foto.startswith("http://") or ruta_foto.startswith("https://"):
            return ruta_foto

        clean = ruta_foto.replace("\\", "/").lstrip("/")
        base = self.photos_base_url.rstrip("/")

        if clean.startswith("uploads/"):
            return f"{base}/{clean}"
        elif clean.startswith("photos/"):
            return f"{base}/uploads/{clean}"
        else:
            return f"{base}/uploads/photos/{clean}"

    def request(self, endpoint, payload=None):
        """Envía JSON y devuelve el sobre {success, message, data} de Laravel."""
        url = self.base_url + endpoint

        print("URL:", url)
        print("PAYLOAD:", payload)

        body = json.dumps(payload or {}).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "PostmanRuntime/7.55.1",
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
                context=ssl.create_default_context(),
            ) as response:
                raw_response = response.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            raw_response = error.read().decode("utf-8", errors="replace")
            raise ApiConnectionError(
                f"HTTP {error.code}: {self._message_from_response(raw_response)}"
            ) from error
        except (urllib.error.URLError, TimeoutError) as error:
            raise ApiConnectionError(f"No fue posible conectar: {error}") from error

        try:
            response_data = json.loads(raw_response)
        except json.JSONDecodeError as error:
            raise ApiConnectionError("La API no devolvió JSON válido.") from error

        if not isinstance(response_data, dict) or "success" not in response_data:
            raise ApiConnectionError("La respuesta no cumple el contrato de la API.")
        if not response_data["success"]:
            raise ApiConnectionError(response_data.get("message", "La API rechazó la solicitud."))
        return response_data

    def ping(self):
        return self.request(self.ENDPOINTS["ping"])

    def initial_sync(self, limit=10):
        return self.request(self.ENDPOINTS["initial_sync"], {"limit": limit})

    def sync_changes(self, last_sync, limit=10):
        return self.request(
            self.ENDPOINTS["sync_changes"],
            {"last_sync": last_sync, "limit": limit},
        )

    def sync_records(self, records):
        return self.request(self.ENDPOINTS["sync_records"], {"records": records})

    def dashboard(self):
        return self.request(self.ENDPOINTS["dashboard"])

    def validate_credentials(self, usuario, password):
        """Valida credenciales en el servidor central."""
        return self.request(self.ENDPOINTS["validate_credentials"], {"usuario": usuario, "password": password})

    def login(self, usuario, password):
        """Autentica credenciales en la API Laravel."""
        return self.validate_credentials(usuario, password)

    def upload_photo(self, record_id: int, user_id: int, file_path: str) -> dict:
        """Sube una fotografía de un bien al servidor."""
        url = self.base_url + self.ENDPOINTS.get("upload_photo", "/query/response/upload_photo")
        try:
            with open(file_path, "rb") as f:
                files = {"photo": f}
                data = {"id": int(record_id), "user_id": int(user_id)}
                resp = requests.post(url, data=data, files=files, timeout=60)
                try:
                    payload = resp.json()
                except Exception:
                    payload = {"message": resp.text[:200]}
                return {"status_code": resp.status_code, "data": payload}
        except Exception as e:
            return {"status_code": 500, "data": {"message": str(e)}}

    def update_ubicacion_final(self, record_id: int, codigo_ubicacion_final: str, user_id: int) -> dict:
        """Actualiza la ubicación final inventariada de un bien en el servidor."""
        payload = {
            "id": int(record_id),
            "codigo_ubicacion_final": str(codigo_ubicacion_final),
            "user_id": int(user_id),
        }
        return self._post_json("update_final_location", payload)

    def update_ultima_ubicacion(self, record_id: int, codigo_ubicacion_final: str, user_id: int) -> dict:
        """Compatibilidad semántica para actualizar la ubicación final vigente."""
        return self.update_ubicacion_final(record_id, codigo_ubicacion_final, user_id)

    def uninventory_record(self, record_id: int, user_id: int = 1) -> dict:
        """Des-inventaría un bien en el servidor, limpiando su ubicación final."""
        payload = {
            "id": int(record_id),
            "user_id": int(user_id or 1),
        }
        return self._post_json("uninventory_record", payload)

    def update_technical_details(self, payload: dict) -> dict:
        """Actualiza las especificaciones técnicas (marca, modelo, serie, color, estado, etc.) de un bien."""
        return self._post_json("update_technical_details", payload)

    def create_or_update_location(self, payload: dict) -> dict:
        """
        Crea o actualiza una ubicación en el servidor (POST /query/response/create_or_update_location).
        Si se incluye 'id' (int), el servidor actualiza el registro existente;
        si se omite o envía None/null, crea un nuevo registro.
        """
        def _opt_str(val):
            if val is None:
                return None
            s = str(val).strip()
            return s if s != "" else None

        raw_id = payload.get("id")
        clean_id = None
        if raw_id is not None and str(raw_id).strip() != "":
            try:
                clean_id = int(raw_id)
            except (ValueError, TypeError):
                clean_id = None

        request_body = {
            "id": clean_id,
            "codigo_ubicacion": str(payload.get("codigo_ubicacion") or "").strip(),
            "local": _opt_str(payload.get("local")),
            "area": _opt_str(payload.get("area")),
            "oficina": _opt_str(payload.get("oficina")),
            "piso": _opt_str(payload.get("piso")),
            "direccion": _opt_str(payload.get("direccion")),
            "codigo_personal": _opt_str(payload.get("codigo_personal")),
        }
        return self._post_json("create_location", request_body)

    def create_or_update_personnel(self, payload: dict) -> dict:
        """Crea o actualiza un registro de personal/responsable en el servidor."""
        return self._post_json("create_personnel", payload)

    def create_or_update_surplus(self, payload: dict) -> dict:
        """Crea o actualiza un bien sobrante en el servidor."""
        return self._post_json("create_surplus", payload)

    @staticmethod
    def _message_from_response(raw_response):
        try:
            return json.loads(raw_response).get("message", raw_response)
        except json.JSONDecodeError:
            return raw_response[:300]


def current_sync_timestamp():
    """Formato que Laravel acepta para el campo last_sync."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
