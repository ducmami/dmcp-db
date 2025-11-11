from abc import ABC, abstractmethod
from typing import Optional
from ..types.sql import (
    ConnectorType,
    TableColumn,
    TableIndex,
    StoredProcedure,
    SQLResult,
    ExecuteOptions,
)


class DSNParser(ABC):
    @abstractmethod
    def parse(self, dsn: str) -> dict:
        pass
    
    @abstractmethod
    def get_sample_dsn(self) -> str:
        pass
    
    @abstractmethod
    def is_valid_dsn(self, dsn: str) -> bool:
        pass


class Connector(ABC):
    def __init__(self):
        self.id: ConnectorType
        self.name: str
        self.dsn_parser: DSNParser
    
    def clone(self) -> "Connector":
        raise NotImplementedError("clone() not implemented for this connector")
    
    @abstractmethod
    async def connect(self, dsn: str, init_script: Optional[str] = None) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def get_schemas(self) -> list[str]:
        pass
    
    @abstractmethod
    async def get_tables(self, schema: Optional[str] = None) -> list[str]:
        pass
    
    @abstractmethod
    async def get_table_schema(
        self, table_name: str, schema: Optional[str] = None
    ) -> list[TableColumn]:
        pass
    
    @abstractmethod
    async def table_exists(
        self, table_name: str, schema: Optional[str] = None
    ) -> bool:
        pass
    
    @abstractmethod
    async def get_table_indexes(
        self, table_name: str, schema: Optional[str] = None
    ) -> list[TableIndex]:
        pass
    
    @abstractmethod
    async def get_stored_procedures(
        self, schema: Optional[str] = None
    ) -> list[str]:
        pass
    
    @abstractmethod
    async def get_stored_procedure_detail(
        self, procedure_name: str, schema: Optional[str] = None
    ) -> StoredProcedure:
        pass
    
    @abstractmethod
    async def execute_sql(
        self, sql: str, options: ExecuteOptions
    ) -> SQLResult:
        pass


class ConnectorRegistry:
    _connectors: dict[ConnectorType, Connector] = {}
    
    @classmethod
    def register(cls, connector: Connector) -> None:
        cls._connectors[connector.id] = connector
    
    @classmethod
    def get_connector(cls, connector_id: ConnectorType) -> Optional[Connector]:
        return cls._connectors.get(connector_id)
    
    @classmethod
    def get_connector_for_dsn(cls, dsn: str) -> Optional[Connector]:
        dsn_lower = dsn.lower()
        if dsn_lower.startswith("postgres://") or dsn_lower.startswith("postgresql://"):
            return cls._connectors.get("postgres")
        elif dsn_lower.startswith("mysql://"):
            return cls._connectors.get("mysql")
        elif dsn_lower.startswith("mariadb://"):
            return cls._connectors.get("mariadb")
        elif dsn_lower.startswith("sqlite://") or dsn_lower.endswith(".db") or dsn_lower.endswith(".sqlite"):
            return cls._connectors.get("sqlite")
        elif dsn_lower.startswith("sqlserver://") or dsn_lower.startswith("mssql://"):
            return cls._connectors.get("sqlserver")
        return None
    
    @classmethod
    def get_available_connectors(cls) -> list[ConnectorType]:
        return list(cls._connectors.keys())
    
    @classmethod
    def get_sample_dsn(cls, connector_type: ConnectorType) -> Optional[str]:
        connector = cls._connectors.get(connector_type)
        return connector.dsn_parser.get_sample_dsn() if connector else None
    
    @classmethod
    def get_all_sample_dsns(cls) -> dict[ConnectorType, str]:
        return {
            conn_id: conn.dsn_parser.get_sample_dsn()
            for conn_id, conn in cls._connectors.items()
        }

