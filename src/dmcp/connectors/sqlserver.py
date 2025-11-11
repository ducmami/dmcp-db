from urllib.parse import urlparse, parse_qs
from typing import Optional
import pyodbc
import asyncio
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


class SQLServerDSNParser(DSNParser):
    def parse(self, dsn: str) -> dict:
        if not self.is_valid_dsn(dsn):
            raise ValueError(
                f"Invalid SQL Server DSN format.\nProvided: {dsn}\nExpected: {self.get_sample_dsn()}"
            )
        
        parsed = urlparse(dsn)
        config = {
            "server": parsed.hostname or "localhost",
            "port": parsed.port or 1433,
            "database": parsed.path.lstrip("/") if parsed.path else "",
            "user": parsed.username or "",
            "password": parsed.password or "",
        }
        
        query_params = parse_qs(parsed.query)
        if "driver" in query_params:
            config["driver"] = query_params["driver"][0]
        else:
            config["driver"] = "{ODBC Driver 17 for SQL Server}"
        
        if "TrustServerCertificate" in query_params:
            config["TrustServerCertificate"] = query_params["TrustServerCertificate"][0]
        
        return config
    
    def get_sample_dsn(self) -> str:
        return "sqlserver://sa:password@localhost:1433/master"
    
    def is_valid_dsn(self, dsn: str) -> bool:
        return dsn.startswith("sqlserver://") or dsn.startswith("mssql://")


class SQLServerConnector(Connector):
    def __init__(self):
        self.id: ConnectorType = "sqlserver"
        self.name = "SQL Server"
        self.dsn_parser = SQLServerDSNParser()
        self.conn: Optional[pyodbc.Connection] = None
        self.connection_string: str = ""
    
    async def connect(self, dsn: str, init_script: Optional[str] = None) -> None:
        try:
            config = self.dsn_parser.parse(dsn)
            
            self.connection_string = (
                f"DRIVER={config['driver']};"
                f"SERVER={config['server']},{config['port']};"
                f"DATABASE={config['database']};"
                f"UID={config['user']};"
                f"PWD={config['password']};"
            )
            
            if "TrustServerCertificate" in config:
                self.connection_string += f"TrustServerCertificate={config['TrustServerCertificate']};"
            
            loop = asyncio.get_event_loop()
            self.conn = await loop.run_in_executor(
                None, pyodbc.connect, self.connection_string
            )
            
            if init_script:
                cursor = self.conn.cursor()
                await loop.run_in_executor(None, cursor.execute, init_script)
                await loop.run_in_executor(None, self.conn.commit)
                cursor.close()
            
            print("Successfully connected to SQL Server database", flush=True)
        except Exception as e:
            print(f"Failed to connect to SQL Server database: {e}", flush=True)
            raise
    
    async def disconnect(self) -> None:
        if self.conn:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.conn.close)
            self.conn = None
    
    async def get_schemas(self) -> list[str]:
        if not self.conn:
            raise RuntimeError("Not connected to database")
        
        loop = asyncio.get_event_loop()
        cursor = self.conn.cursor()
        
        await loop.run_in_executor(
            None,
            cursor.execute,
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('INFORMATION_SCHEMA', 'sys', 'guest')
            ORDER BY schema_name
            """
        )
        
        rows = await loop.run_in_executor(None, cursor.fetchall)
        cursor.close()
        return [row[0] for row in rows]
    
    async def get_tables(self, schema: Optional[str] = None) -> list[str]:
        if not self.conn:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "dbo"
        loop = asyncio.get_event_loop()
        cursor = self.conn.cursor()
        
        await loop.run_in_executor(
            None,
            cursor.execute,
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = ?
            ORDER BY table_name
            """,
            schema_to_use
        )
        
        rows = await loop.run_in_executor(None, cursor.fetchall)
        cursor.close()
        return [row[0] for row in rows]
    
    async def get_table_schema(
        self, table_name: str, schema: Optional[str] = None
    ) -> list[TableColumn]:
        if not self.conn:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "dbo"
        loop = asyncio.get_event_loop()
        cursor = self.conn.cursor()
        
        await loop.run_in_executor(
            None,
            cursor.execute,
            """
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = ?
            AND table_name = ?
            ORDER BY ordinal_position
            """,
            schema_to_use,
            table_name
        )
        
        rows = await loop.run_in_executor(None, cursor.fetchall)
        cursor.close()
        
        return [
            TableColumn(
                column_name=row[0],
                data_type=row[1],
                is_nullable=row[2],
                column_default=row[3],
            )
            for row in rows
        ]
    
    async def table_exists(
        self, table_name: str, schema: Optional[str] = None
    ) -> bool:
        if not self.conn:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "dbo"
        loop = asyncio.get_event_loop()
        cursor = self.conn.cursor()
        
        await loop.run_in_executor(
            None,
            cursor.execute,
            """
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = ? 
            AND table_name = ?
            """,
            schema_to_use,
            table_name
        )
        
        result = await loop.run_in_executor(None, cursor.fetchone)
        cursor.close()
        return result[0] > 0 if result else False
    
    async def get_table_indexes(
        self, table_name: str, schema: Optional[str] = None
    ) -> list[TableIndex]:
        if not self.conn:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "dbo"
        loop = asyncio.get_event_loop()
        cursor = self.conn.cursor()
        
        await loop.run_in_executor(
            None,
            cursor.execute,
            """
            SELECT 
                i.name as index_name,
                STRING_AGG(c.name, ',') as column_names,
                i.is_unique,
                i.is_primary_key
            FROM sys.indexes i
            INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
            INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            INNER JOIN sys.tables t ON i.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = ? AND t.name = ?
            GROUP BY i.name, i.is_unique, i.is_primary_key
            ORDER BY i.name
            """,
            schema_to_use,
            table_name
        )
        
        rows = await loop.run_in_executor(None, cursor.fetchall)
        cursor.close()
        
        return [
            TableIndex(
                index_name=row[0],
                column_names=row[1].split(",") if row[1] else [],
                is_unique=bool(row[2]),
                is_primary=bool(row[3]),
            )
            for row in rows
        ]
    
    async def get_stored_procedures(
        self, schema: Optional[str] = None
    ) -> list[str]:
        if not self.conn:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "dbo"
        loop = asyncio.get_event_loop()
        cursor = self.conn.cursor()
        
        await loop.run_in_executor(
            None,
            cursor.execute,
            """
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_schema = ?
            ORDER BY routine_name
            """,
            schema_to_use
        )
        
        rows = await loop.run_in_executor(None, cursor.fetchall)
        cursor.close()
        return [row[0] for row in rows]
    
    async def get_stored_procedure_detail(
        self, procedure_name: str, schema: Optional[str] = None
    ) -> StoredProcedure:
        if not self.conn:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "dbo"
        loop = asyncio.get_event_loop()
        cursor = self.conn.cursor()
        
        await loop.run_in_executor(
            None,
            cursor.execute,
            """
            SELECT 
                routine_name,
                routine_type,
                data_type,
                routine_definition
            FROM information_schema.routines
            WHERE routine_schema = ?
            AND routine_name = ?
            """,
            schema_to_use,
            procedure_name
        )
        
        row = await loop.run_in_executor(None, cursor.fetchone)
        
        if not row:
            cursor.close()
            raise ValueError(
                f"Stored procedure '{procedure_name}' not found in schema '{schema_to_use}'"
            )
        
        await loop.run_in_executor(
            None,
            cursor.execute,
            """
            SELECT STRING_AGG(
                CONCAT(parameter_name, ' ', parameter_mode, ' ', data_type),
                ', '
            ) as parameter_list
            FROM information_schema.parameters
            WHERE specific_schema = ?
            AND specific_name = ?
            AND parameter_name IS NOT NULL
            """,
            schema_to_use,
            procedure_name
        )
        
        param_row = await loop.run_in_executor(None, cursor.fetchone)
        cursor.close()
        
        parameter_list = param_row[0] if param_row and param_row[0] else ""
        
        return StoredProcedure(
            procedure_name=row[0],
            procedure_type="procedure" if row[1] == "PROCEDURE" else "function",
            language="tsql",
            parameter_list=parameter_list,
            return_type=row[2] if row[2] and row[2] != "void" else None,
            definition=row[3],
        )
    
    async def execute_sql(
        self, sql: str, options: ExecuteOptions
    ) -> SQLResult:
        if not self.conn:
            raise RuntimeError("Not connected to database")
        
        loop = asyncio.get_event_loop()
        cursor = self.conn.cursor()
        
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        
        try:
            if len(statements) == 1:
                processed_sql = apply_row_limit(statements[0], options.max_rows, self.id)
                await loop.run_in_executor(None, cursor.execute, processed_sql)
                rows = await loop.run_in_executor(None, cursor.fetchall)
                await loop.run_in_executor(None, self.conn.commit)
                
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows_dict = [
                    {columns[i]: row[i] for i in range(len(columns))}
                    for row in rows
                ]
                
                cursor.close()
                return SQLResult(
                    rows=rows_dict,
                    row_count=len(rows_dict),
                    columns=columns
                )
            else:
                all_rows = []
                all_columns = []
                
                for statement in statements:
                    processed_sql = apply_row_limit(statement, options.max_rows, self.id)
                    await loop.run_in_executor(None, cursor.execute, processed_sql)
                    result = await loop.run_in_executor(None, cursor.fetchall)
                    
                    if result and cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        if not all_columns:
                            all_columns = columns
                        rows_dict = [
                            {columns[i]: row[i] for i in range(len(columns))}
                            for row in result
                        ]
                        all_rows.extend(rows_dict)
                
                await loop.run_in_executor(None, self.conn.commit)
                cursor.close()
                
                return SQLResult(
                    rows=all_rows,
                    row_count=len(all_rows),
                    columns=all_columns
                )
        except Exception as e:
            await loop.run_in_executor(None, self.conn.rollback)
            cursor.close()
            raise


from .interface import ConnectorRegistry
sqlserver_connector = SQLServerConnector()
ConnectorRegistry.register(sqlserver_connector)

