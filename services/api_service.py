import requests

class ApiService:

    BASE_URL = "https://api.acontarsac.com"

    def __init__(self):
        self.timeout = 60

    def initial_sync(self):
        url = f"{self.BASE_URL}/initial_sync"
        response = requests.post(
            url,
            json={},
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()


    def sync_changes(self, last_sync):
        url = f"{self.BASE_URL}/sync_changes"
        response = requests.post(
            url,
            json={
                "last_sync": last_sync
            },
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()


    def login(self, usuario, password):
        url = f"{self.BASE_URL}/validate_credentials"
        response = requests.post(
            url,
            json={
                "usuario": usuario,
                "password": password
            },
            timeout=self.timeout
        )   
        response.raise_for_status()
        return response.json()

    def update_ubicacion_final(self, record_id: int, codigo_ubicacion_final: str, user_id: int):
        """Envía la actualización de ubicación final al servidor."""
        url = f"{self.BASE_URL}/query/response/update_ubicacion_final"
        payload = {
            "id": int(record_id),
            "codigo_ubicacion_final": str(codigo_ubicacion_final),
            "user_id": int(user_id)
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )
            
            try:
                data = response.json()
            except ValueError:
                data = {"message": response.text}

            return {
                "status_code": response.status_code,
                "data": data
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 500,
                "data": {"message": f"Error de conexión con el servidor: {e}"}
            }
