from typing import Optional
import aiosqlite
from urllib.parse import urlparse
from .interface import Connector, DSNParser
from ..types.sql import (
    ConnectorType,
    TableColumn,
    TableIndex,
    StoredProcedure,
    SQLResult,
    ExecuteOptions,
)
from ..utils.sql_row_limiter import apply_row_limit


class SQLiteDSNParser(DSNParser):
    def parse(self, dsn: str) -> dict:
        if dsn.startswith("sqlite://"):
            parsed = urlparse(dsn)
            if parsed.hostname == "" and parsed.path == "/:memory:":
                db_path = ":memory:"
            elif parsed.path.startswith("//"):
                db_path = parsed.path[2:]
            else:
                db_path = parsed.path
            return {"db_path": db_path}
        else:
            return {"db_path": dsn}
    
    def get_sample_dsn(self) -> str:
        return "sqlite:///path/to/database.db"
    
    def is_valid_dsn(self, dsn: str) -> bool:
        return dsn.startswith("sqlite://") or dsn.endswith(".db") or dsn.endswith(".sqlite") or dsn == ":memory:"


class SQLiteConnector(Connector):
    def __init__(self):
        self.id: ConnectorType = "sqlite"
        self.name = "SQLite"
        self.dsn_parser = SQLiteDSNParser()
        self.db: Optional[aiosqlite.Connection] = None
        self.db_path: str = ":memory:"
    
    def clone(self) -> "SQLiteConnector":
        return SQLiteConnector()
    
    async def connect(self, dsn: str, init_script: Optional[str] = None) -> None:
        config = self.dsn_parser.parse(dsn)
        self.db_path = config["db_path"]
        
        try:
            self.db = await aiosqlite.connect(self.db_path)
            self.db.row_factory = aiosqlite.Row
            
            if init_script:
                await self.db.executescript(init_script)
                await self.db.commit()
            
            print("Successfully connected to SQLite database", flush=True)
        except Exception as e:
            print(f"Failed to connect to SQLite database: {e}", flush=True)
            raise
    
    async def disconnect(self) -> None:
        if self.db:
            await self.db.close()
            self.db = None
    
    async def get_schemas(self) -> list[str]:
        return ["main"]
    
    async def get_tables(self, schema: Optional[str] = None) -> list[str]:
        if not self.db:
            raise RuntimeError("Not connected to SQLite database")
        
        cursor = await self.db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        rows = await cursor.fetchall()
        return [row[0] for row in rows]
    
    async def get_table_schema(
        self, table_name: str, schema: Optional[str] = None
    ) -> list[TableColumn]:
        if not self.db:
            raise RuntimeError("Not connected to SQLite database")
        
        cursor = await self.db.execute(f"PRAGMA table_info({table_name})")
        rows = await cursor.fetchall()
        
        return [
            TableColumn(
                column_name=row[1],
                data_type=row[2],
                is_nullable="NO" if row[3] else "YES",
                column_default=row[4],
            )
            for row in rows
        ]
    
    async def table_exists(
        self, table_name: str, schema: Optional[str] = None
    ) -> bool:
        if not self.db:
            raise RuntimeError("Not connected to SQLite database")
        
        cursor = await self.db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = ?
        """, (table_name,))
        row = await cursor.fetchone()
        return row is not None
    
    async def get_table_indexes(
        self, table_name: str, schema: Optional[str] = None
    ) -> list[TableIndex]:
        if not self.db:
            raise RuntimeError("Not connected to SQLite database")
        
        cursor = await self.db.execute(f"PRAGMA index_list({table_name})")
        index_rows = await cursor.fetchall()
        
        indexes = []
        for index_row in index_rows:
            index_name = index_row[1]
            is_unique = bool(index_row[2])
            is_primary = index_row[3] == 1 if len(index_row) > 3 else False
            
            cursor = await self.db.execute(f"PRAGMA index_info({index_name})")
            col_rows = await cursor.fetchall()
            column_names = [col_row[2] for col_row in col_rows]
            
            indexes.append(
                TableIndex(
                    index_name=index_name,
                    column_names=column_names,
                    is_unique=is_unique,
                    is_primary=is_primary,
                )
            )
        
        cursor = await self.db.execute(f"PRAGMA table_info({table_name})")
        table_info = await cursor.fetchall()
        pk_columns = [row[1] for row in table_info if row[5] > 0]
        
        if pk_columns and not any(idx.is_primary for idx in indexes):
            indexes.insert(
                0,
                TableIndex(
                    index_name="PRIMARY",
                    column_names=pk_columns,
                    is_unique=True,
                    is_primary=True,
                ),
            )
        
        return indexes
    
    async def get_stored_procedures(
        self, schema: Optional[str] = None
    ) -> list[str]:
        return []
    
    async def get_stored_procedure_detail(
        self, procedure_name: str, schema: Optional[str] = None
    ) -> StoredProcedure:
        raise NotImplementedError("SQLite does not support stored procedures")
    
    async def execute_sql(
        self, sql: str, options: ExecuteOptions
    ) -> SQLResult:
        if not self.db:
            raise RuntimeError("Not connected to SQLite database")
        
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        
        if len(statements) == 1:
            processed_sql = apply_row_limit(statements[0], options.max_rows, self.id)
            cursor = await self.db.execute(processed_sql)
            rows = await cursor.fetchall()
            rows_dict = [dict(row) for row in rows]
            columns = list(rows[0].keys()) if rows else []
            await self.db.commit()
            return SQLResult(
                rows=rows_dict,
                row_count=len(rows_dict),
                columns=columns
            )
        else:
            all_rows = []
            for statement in statements:
                processed_sql = apply_row_limit(statement, options.max_rows, self.id)
                cursor = await self.db.execute(processed_sql)
                result = await cursor.fetchall()
                if result:
                    all_rows.extend([dict(row) for row in result])
            
            await self.db.commit()
            columns = list(all_rows[0].keys()) if all_rows else []
            return SQLResult(
                rows=all_rows,
                row_count=len(all_rows),
                columns=columns
            )


from .interface import ConnectorRegistry
sqlite_connector = SQLiteConnector()
ConnectorRegistry.register(sqlite_connector)

