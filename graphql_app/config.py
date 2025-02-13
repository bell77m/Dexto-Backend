import configparser
from typing import Dict


class Config:

    __conf_path = ""
    def __init__(self, __conf_path):
        self.__conf_path = __conf_path


    def load_db_config(self) -> dict[str, str]:
        try:
            conf = configparser.ConfigParser()
            conf.read(self.__conf_path)
            db_host = conf.get('Database', 'host')
            db_port = conf.get('Database', 'port')
            db_user = conf.get('Database', 'user')
            db_pass = conf.get('Database', 'password')
            config_value = {
                'host': db_host,
                'user': db_user,
                'password': db_pass,
                'port': db_port,
            }
            return config_value

        except configparser.Error as e:
            print(f"Error: {e.message}")

