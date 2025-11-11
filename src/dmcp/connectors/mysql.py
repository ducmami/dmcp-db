from urllib.parse import urlparse, parse_qs
from typing import Optional
import aiomysql
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


class MySQLDSNParser(DSNParser):
    def parse(self, dsn: str) -> dict:
        if not self.is_valid_dsn(dsn):
            raise ValueError(
                f"Invalid MySQL DSN format.\nProvided: {dsn}\nExpected: {self.get_sample_dsn()}"
            )
        
        parsed = urlparse(dsn)
        config = {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 3306,
            "db": parsed.path.lstrip("/") if parsed.path else "",
            "user": parsed.username or "",
            "password": parsed.password or "",
        }
        
        query_params = parse_qs(parsed.query)
        if "charset" in query_params:
            config["charset"] = query_params["charset"][0]
        
        return config
    
    def get_sample_dsn(self) -> str:
        return "mysql://root:password@localhost:3306/mydb"
    
    def is_valid_dsn(self, dsn: str) -> bool:
        return dsn.startswith("mysql://")


class MySQLConnector(Connector):
    def __init__(self):
        self.id: ConnectorType = "mysql"
        self.name = "MySQL"
        self.dsn_parser = MySQLDSNParser()
        self.pool: Optional[aiomysql.Pool] = None
    
    async def connect(self, dsn: str, init_script: Optional[str] = None) -> None:
        try:
            config = self.dsn_parser.parse(dsn)
            self.pool = await aiomysql.create_pool(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password=config["password"],
                db=config["db"],
                charset=config.get("charset", "utf8mb4"),
                autocommit=False,
            )
            
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT 1")
            
            if init_script:
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute(init_script)
                    await conn.commit()
            
            print("Successfully connected to MySQL database", flush=True)
        except Exception as e:
            print(f"Failed to connect to MySQL database: {e}", flush=True)
            raise
    
    async def disconnect(self) -> None:
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
    
    async def get_schemas(self) -> list[str]:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
                    ORDER BY schema_name
                """)
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    
    async def get_tables(self, schema: Optional[str] = None) -> list[str]:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if schema:
                    await cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                        ORDER BY table_name
                    """, (schema,))
                else:
                    await cursor.execute("SELECT DATABASE()")
                    result = await cursor.fetchone()
                    current_db = result[0] if result else None
                    if not current_db:
                        raise RuntimeError("No database selected")
                    await cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                        ORDER BY table_name
                    """, (current_db,))
                
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    
    async def get_table_schema(
        self, table_name: str, schema: Optional[str] = None
    ) -> list[TableColumn]:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if schema:
                    schema_to_use = schema
                else:
                    await cursor.execute("SELECT DATABASE()")
                    result = await cursor.fetchone()
                    schema_to_use = result[0] if result else None
                
                await cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = %s
                    AND table_name = %s
                    ORDER BY ordinal_position
                """, (schema_to_use, table_name))
                
                rows = await cursor.fetchall()
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
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if schema:
                    schema_to_use = schema
                else:
                    await cursor.execute("SELECT DATABASE()")
                    result = await cursor.fetchone()
                    schema_to_use = result[0] if result else None
                
                await cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_name = %s
                """, (schema_to_use, table_name))
                
                result = await cursor.fetchone()
                return result[0] > 0 if result else False
    
    async def get_table_indexes(
        self, table_name: str, schema: Optional[str] = None
    ) -> list[TableIndex]:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if schema:
                    schema_to_use = schema
                else:
                    await cursor.execute("SELECT DATABASE()")
                    result = await cursor.fetchone()
                    schema_to_use = result[0] if result else None
                
                await cursor.execute("""
                    SELECT 
                        index_name,
                        GROUP_CONCAT(column_name ORDER BY seq_in_index) as column_names,
                        MAX(CASE WHEN non_unique = 0 THEN 1 ELSE 0 END) as is_unique,
                        MAX(CASE WHEN index_name = 'PRIMARY' THEN 1 ELSE 0 END) as is_primary
                    FROM information_schema.statistics
                    WHERE table_schema = %s
                    AND table_name = %s
                    GROUP BY index_name
                    ORDER BY index_name
                """, (schema_to_use, table_name))
                
                rows = await cursor.fetchall()
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
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if schema:
                    schema_to_use = schema
                else:
                    await cursor.execute("SELECT DATABASE()")
                    result = await cursor.fetchone()
                    schema_to_use = result[0] if result else None
                
                await cursor.execute("""
                    SELECT routine_name
                    FROM information_schema.routines
                    WHERE routine_schema = %s
                    ORDER BY routine_name
                """, (schema_to_use,))
                
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
    
    async def get_stored_procedure_detail(
        self, procedure_name: str, schema: Optional[str] = None
    ) -> StoredProcedure:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                if schema:
                    schema_to_use = schema
                else:
                    await cursor.execute("SELECT DATABASE()")
                    result = await cursor.fetchone()
                    schema_to_use = result[0] if result else None
                
                await cursor.execute("""
                    SELECT 
                        routine_name,
                        routine_type,
                        data_type,
                        routine_definition
                    FROM information_schema.routines
                    WHERE routine_schema = %s
                    AND routine_name = %s
                """, (schema_to_use, procedure_name))
                
                row = await cursor.fetchone()
                if not row:
                    raise ValueError(
                        f"Stored procedure '{procedure_name}' not found in schema '{schema_to_use}'"
                    )
                
                await cursor.execute("""
                    SELECT GROUP_CONCAT(
                        CONCAT(parameter_name, ' ', parameter_mode, ' ', data_type)
                        SEPARATOR ', '
                    ) as parameter_list
                    FROM information_schema.parameters
                    WHERE specific_schema = %s
                    AND specific_name = %s
                    AND parameter_name IS NOT NULL
                """, (schema_to_use, procedure_name))
                
                param_row = await cursor.fetchone()
                parameter_list = param_row[0] if param_row and param_row[0] else ""
                
                return StoredProcedure(
                    procedure_name=row[0],
                    procedure_type="procedure" if row[1] == "PROCEDURE" else "function",
                    language="sql",
                    parameter_list=parameter_list,
                    return_type=row[2] if row[2] and row[2] != "void" else None,
                    definition=row[3],
                )
    
    async def execute_sql(
        self, sql: str, options: ExecuteOptions
    ) -> SQLResult:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                statements = [s.strip() for s in sql.split(";") if s.strip()]
                
                if len(statements) == 1:
                    processed_sql = apply_row_limit(statements[0], options.max_rows, self.id)
                    await cursor.execute(processed_sql)
                    rows = await cursor.fetchall()
                    await conn.commit()
                    columns = list(rows[0].keys()) if rows else []
                    return SQLResult(
                        rows=rows,
                        row_count=len(rows),
                        columns=columns
                    )
                else:
                    all_rows = []
                    await conn.begin()
                    try:
                        for statement in statements:
                            processed_sql = apply_row_limit(statement, options.max_rows, self.id)
                            await cursor.execute(processed_sql)
                            result = await cursor.fetchall()
                            if result:
                                all_rows.extend(result)
                        await conn.commit()
                    except Exception:
                        await conn.rollback()
                        raise
                    
                    columns = list(all_rows[0].keys()) if all_rows else []
                    return SQLResult(
                        rows=all_rows,
                        row_count=len(all_rows),
                        columns=columns
                    )


from .interface import ConnectorRegistry
mysql_connector = MySQLConnector()
ConnectorRegistry.register(mysql_connector)

