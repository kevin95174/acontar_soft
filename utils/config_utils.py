import configparser
import os

class ConfigUtils:
    def __init__(self, config_path='config.ini'):
        self.config_path = config_path
        self.config = configparser.ConfigParser()

    def load_config(self):
        if os.path.exists(self.config_path):
            self.config.read(self.config_path)
            if 'Settings' in self.config:
                img_label_path = self.config['Settings'].get('img_label_path', '')
                img_ficha_path = self.config['Settings'].get('img_ficha_path', '')
                lista = [img_label_path, img_ficha_path]
                return lista
        return '', ''
