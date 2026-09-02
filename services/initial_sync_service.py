from utils.api_client import ApiManagerAcontarSacClient
from db.conex import Database


class InitialSyncService:

    def __init__(self):

        self.api = ApiManagerAcontarSacClient(timeout=120)
        self.db = Database()

    def execute(self):

        print("Descargando información...")

        response = self.api.initial_sync(limit=20000)

        data = response["data"]

        self.save_assets(data["assets"])
        self.save_locations(data["locations"])
        self.save_personnel(data["personnel"])
        self.save_surplus(data["surplus"])
        self.save_inventory_records(data["inventory_records"])

        print("Sincronización completada")