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
    }

    def __init__(self, base_url=None, timeout=30):
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = timeout

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
                "User-Agent": "PostmanRuntime/7.55.1"
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

    def update_ubicacion_final(self, record_id: int, codigo_ubicacion_final: str, user_id: int) -> dict:
        # 1. Garantizar que la sesión exista antes de llamar a post()
        if not hasattr(self, 'session') or self.session is None:
            self.session = requests.Session()
            self.session.headers.update({
                "Content-Type": "application/json",
                "Accept": "application/json"
            })

        # 🔥 2. CORRECCIÓN DE RUTA: Agregar '/api/' y usar guiones medios '-'
        url = self.base_url + self.ENDPOINTS["update_final_location"]

        payload = {
            "id": int(record_id),
            "codigo_ubicacion_final": str(codigo_ubicacion_final),
            "user_id": int(user_id)
        }

        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            
            try:
                data = response.json()
            except (json.JSONDecodeError, ValueError):
                # Si el servidor devolvió HTML (error 404, 500, etc.)
                data = {
                    "message": f"Respuesta no válida del servidor (HTTP {response.status_code}). Detalle: {response.text[:200]}"
                }

            return {
                "status_code": response.status_code,
                "data": data
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 500,
                "data": {"message": f"Error de conexión HTTP: {e}"}
            }

    def update_ultima_ubicacion(self, record_id: int, codigo_ubicacion_final: str, user_id: int) -> dict:
        """Compatibilidad semántica para actualizar la ubicación final vigente.

        El endpoint público del servidor se llama ``update_ubicacion_final``;
        ambos nombres realizan la misma operación.
        """
        return self.update_ubicacion_final(
            record_id, codigo_ubicacion_final, user_id
        )

    @staticmethod
    def _message_from_response(raw_response):
        try:
            return json.loads(raw_response).get("message", raw_response)
        except json.JSONDecodeError:
            return raw_response[:300]


def current_sync_timestamp():
    """Formato que Laravel acepta para el campo last_sync."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
