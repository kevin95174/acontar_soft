import unittest
from unittest.mock import Mock, patch

from utils.api_client import ApiManagerAcontarSacClient


class UpdateUbicacionFinalClientTests(unittest.TestCase):
    @patch("utils.api_client.requests.Session.post")
    def test_uses_canonical_inventory_endpoint_and_payload(self, post):
        response = Mock(status_code=200)
        response.json.return_value = {
            "success": True,
            "message": "Bien inventariado correctamente.",
            "data": {"id": 15},
        }
        post.return_value = response

        result = ApiManagerAcontarSacClient(
            base_url="https://example.test/"
        ).update_ubicacion_final(15, "  OF-01  ", 8)

        self.assertEqual(200, result["status_code"])
        self.assertEqual(
            "https://example.test/query/response/update_ubicacion_final",
            post.call_args.args[0],
        )
        self.assertEqual(
            {"id": 15, "codigo_ubicacion_final": "  OF-01  ", "user_id": 8},
            post.call_args.kwargs["json"],
        )

    @patch("utils.api_client.requests.Session.post")
    def test_returns_conflict_body_without_raising(self, post):
        response = Mock(status_code=409)
        response.json.return_value = {
            "success": False,
            "message": "El bien ya fue inventariado por otro usuario.",
        }
        post.return_value = response

        result = ApiManagerAcontarSacClient().update_ubicacion_final(15, "OF-01", 8)

        self.assertEqual(409, result["status_code"])
        self.assertFalse(result["data"]["success"])

    def test_get_photo_url_construction(self):
        client = ApiManagerAcontarSacClient()
        base = "https://admin.acontarsac.com/public"

        # Caso 1: Ruta relativa estándar uploads/photos/...
        self.assertEqual(
            f"{base}/uploads/photos/39_20261021_093818_361b1711.jpg",
            client.get_photo_url("uploads/photos/39_20261021_093818_361b1711.jpg")
        )

        # Caso 2: Solo nombre de archivo
        self.assertEqual(
            f"{base}/uploads/photos/39_20261021_093818_361b1711.jpg",
            client.get_photo_url("39_20261021_093818_361b1711.jpg")
        )

        # Caso 3: Path con separador Windows
        self.assertEqual(
            f"{base}/uploads/photos/39_20261021_093818_361b1711.jpg",
            client.get_photo_url("uploads\\photos\\39_20261021_093818_361b1711.jpg")
        )

        # Caso 4: URL absoluta ya existente
        full_url = "https://admin.acontarsac.com/public/uploads/photos/39_20261021_093818_361b1711.jpg"
        self.assertEqual(full_url, client.get_photo_url(full_url))

        # Caso 5: Vacío
        self.assertEqual("", client.get_photo_url(""))
        self.assertEqual("", client.get_photo_url(None))


if __name__ == "__main__":
    unittest.main()
