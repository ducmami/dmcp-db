from .mysql import MySQLConnector, MySQLDSNParser
from .interface import DSNParser
from ..types.sql import ConnectorType


class MariaDBDSNParser(MySQLDSNParser):
    def get_sample_dsn(self) -> str:
        return "mariadb://root:password@localhost:3306/mydb"
    
    def is_valid_dsn(self, dsn: str) -> bool:
        return dsn.startswith("mariadb://")


class MariaDBConnector(MySQLConnector):
    def __init__(self):
        super().__init__()
        self.id: ConnectorType = "mariadb"
        self.name = "MariaDB"
        self.dsn_parser = MariaDBDSNParser()


from .interface import ConnectorRegistry
mariadb_connector = MariaDBConnector()
ConnectorRegistry.register(mariadb_connector)

