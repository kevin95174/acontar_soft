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
            "https://example.test/api/inventory/update_ubicacion_final",
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


if __name__ == "__main__":
    unittest.main()
