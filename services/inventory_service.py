from datetime import datetime

class InventoryService:
    def __init__(self, db_connection):
        self.db = db_connection

    def procesar_inventariado_bien(self, api_client, record_id: int, cod_int: int, codigo_ubicacion_final: str, user_id: int) -> dict:
        """
        Ejecuta la actualización en el servidor y, si es exitosa, 
        refleja los cambios en las tablas locales 'inventory_records' y 'bienes'.
        """
        # 1. Llamar al backend en PHP
        res = api_client.update_ubicacion_final(record_id, codigo_ubicacion_final, user_id)
        status_code = res.get("status_code")
        body = res.get("data", {})

        # 2. Si el servidor responde 409 Conflict (Ya inventariado por otro usuario)
        if status_code == 409:
            return {
                "success": False,
                "message": body.get("message", "El bien ya fue inventariado por otro usuario."),
                "already_inventoried": True
            }

        # 3. Si hubo error de validación o servidor
        if status_code not in (200, 201):
            return {
                "success": False,
                "message": body.get("message", "No fue posible inventariar el bien."),
                "already_inventoried": False
            }

        # 4. Si el servidor respondió 200 OK, actualizar SQLite localmente
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = self.db.cursor()

        try:
            # Update a inventory_records
            cursor.execute("""
                UPDATE inventory_records
                SET codigo_ubicacion_final = ?,
                    inventariado = 1,
                    user_id = ?,
                    fecha_inventariado = ?,
                    fecha_servidor = ?
                WHERE id = ? OR CAST(codigo_interno AS INTEGER) = ?
            """, (codigo_ubicacion_final, user_id, now_str, now_str, record_id, cod_int))

            # Update a tabla local bienes (Inv = ubicación final)
            cursor.execute("""
                UPDATE bienes
                SET Inv = ?,
                    FechInv = ?,
                    Inventariador = ?
                WHERE CodInt = ?
            """, (codigo_ubicacion_final, now_str, str(user_id), cod_int))

            self.db.commit()
            return {
                "success": True,
                "message": "Bien inventariado correctamente.",
                "data": body.get("data")
            }

        except Exception as e:
            self.db.rollback()
            print(f"❌ Error al actualizar la base de datos local: {e}")
            return {
                "success": False,
                "message": f"Servidor actualizo correctamente, pero falló la BD local: {e}",
                "already_inventoried": False
            }