from typing import Optional
from .interface import Connector, ConnectorRegistry
from ..types.config import SourceConfig
from ..types.sql import ExecuteOptions
from ..utils.ssh_tunnel import SSHTunnelManager


class ConnectorManager:
    _instance: Optional["ConnectorManager"] = None
    
    def __init__(self):
        self._connectors: dict[str, Connector] = {}
        self._execute_options: dict[str, ExecuteOptions] = {}
        self._ssh_tunnels: dict[str, SSHTunnelManager] = {}
        self._default_source_id: Optional[str] = None
    
    @classmethod
    def get_instance(cls) -> "ConnectorManager":
        if cls._instance is None:
            cls._instance = ConnectorManager()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        cls._instance = None
    
    async def connect_with_dsn(
        self, dsn: str, init_script: Optional[str] = None
    ) -> None:
        connector = ConnectorRegistry.get_connector_for_dsn(dsn)
        if not connector:
            raise ValueError(f"No connector found for DSN: {dsn}")
        
        await connector.connect(dsn, init_script)
        self._connectors["default"] = connector
        self._default_source_id = "default"
        self._execute_options["default"] = ExecuteOptions()
    
    async def connect_with_sources(self, sources: list[SourceConfig]) -> None:
        if not sources:
            raise ValueError("No sources provided")
        
        for source in sources:
            if source.dsn:
                dsn = source.dsn
            else:
                dsn = self._build_dsn_from_source(source)
            
            if source.ssh:
                tunnel = SSHTunnelManager(
                    ssh_host=source.ssh.host,
                    ssh_port=source.ssh.port,
                    ssh_user=source.ssh.user,
                    ssh_password=source.ssh.password,
                    ssh_private_key=source.ssh.private_key,
                    remote_host=source.host or "localhost",
                    remote_port=source.port or self._get_default_port(source.type),
                )
                await tunnel.start()
                self._ssh_tunnels[source.id] = tunnel
                dsn = self._rewrite_dsn_for_tunnel(dsn, tunnel.local_port)
            
            connector = ConnectorRegistry.get_connector_for_dsn(dsn)
            if not connector:
                raise ValueError(f"No connector found for source {source.id}")
            
            if hasattr(connector, 'clone') and callable(connector.clone):
                connector = connector.clone()
            
            await connector.connect(dsn, source.init_script)
            self._connectors[source.id] = connector
            
            self._execute_options[source.id] = ExecuteOptions(
                readonly=source.readonly,
                max_rows=source.max_rows
            )
        
        self._default_source_id = sources[0].id
    
    def _build_dsn_from_source(self, source: SourceConfig) -> str:
        if not source.type:
            raise ValueError(f"Source {source.id} must have 'type' or 'dsn'")
        
        user = source.user or ""
        password = source.password or ""
        host = source.host or "localhost"
        port = source.port or self._get_default_port(source.type)
        database = source.database or ""
        
        if source.type == "postgres":
            auth = f"{user}:{password}@" if user else ""
            return f"postgresql://{auth}{host}:{port}/{database}"
        elif source.type in ["mysql", "mariadb"]:
            auth = f"{user}:{password}@" if user else ""
            return f"{source.type}://{auth}{host}:{port}/{database}"
        elif source.type == "sqlite":
            return database
        elif source.type == "sqlserver":
            auth = f"{user}:{password}@" if user else ""
            return f"mssql://{auth}{host}:{port}/{database}"
        
        raise ValueError(f"Unsupported database type: {source.type}")
    
    def _get_default_port(self, db_type: Optional[str]) -> int:
        defaults = {
            "postgres": 5432,
            "mysql": 3306,
            "mariadb": 3306,
            "sqlserver": 1433,
        }
        return defaults.get(db_type, 5432)
    
    def _rewrite_dsn_for_tunnel(self, dsn: str, local_port: int) -> str:
        import re
        return re.sub(r'@[^:]+:\d+/', f'@localhost:{local_port}/', dsn)
    
    def get_connector(self, source_id: Optional[str] = None) -> Connector:
        sid = source_id or self._default_source_id
        if not sid or sid not in self._connectors:
            raise ValueError(f"No connector found for source: {sid}")
        return self._connectors[sid]
    
    def get_execute_options(self, source_id: Optional[str] = None) -> ExecuteOptions:
        sid = source_id or self._default_source_id
        return self._execute_options.get(sid, ExecuteOptions())
    
    def get_all_source_ids(self) -> list[str]:
        return list(self._connectors.keys())
    
    async def disconnect_all(self) -> None:
        for connector in self._connectors.values():
            await connector.disconnect()
        
        for tunnel in self._ssh_tunnels.values():
            await tunnel.stop()
        
        self._connectors.clear()
        self._execute_options.clear()
        self._ssh_tunnels.clear()
        self._default_source_id = None
    
    @classmethod
    def get_current_connector(cls, source_id: Optional[str] = None) -> Connector:
        instance = cls.get_instance()
        return instance.get_connector(source_id)
    
    @classmethod
    def get_current_execute_options(cls, source_id: Optional[str] = None) -> ExecuteOptions:
        instance = cls.get_instance()
        return instance.get_execute_options(source_id)

