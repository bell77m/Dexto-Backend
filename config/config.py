import configparser

class Config:
    def __init__(self, conf_path: str):
        self.conf_path = conf_path

    def load_db_config(self) -> dict[str, str]:
        try:
            conf = configparser.ConfigParser()
            conf.read(self.conf_path)

            return {
                'host': conf.get('Database', 'host', fallback='localhost'),
                'port': conf.get('Database', 'port', fallback='3306'),
                'user': conf.get('Database', 'user', fallback='root'),
                'password': conf.get('Database', 'password', fallback=''),
                'database': conf.get('Database', 'database', fallback='your_database_name') 
            }
        except Exception as e:
            print(f"❌ Error loading DB config: {str(e)}")
            return {}

    def load_server_config(self) -> dict[str, str]:
        try:
            conf = configparser.ConfigParser()
            conf.read(self.conf_path)

            return {
                'host': conf.get('Server', 'host', fallback='127.0.0.1'),
                'port': conf.get('Server', 'port', fallback='8000'),
            }
        except Exception as e:
            print(f"❌ Error loading Server config: {str(e)}")
            return {}
