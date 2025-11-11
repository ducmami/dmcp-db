from urllib.parse import urlparse, parse_qs
from typing import Optional
import asyncpg
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


class PostgresDSNParser(DSNParser):
    def parse(self, dsn: str) -> dict:
        if not self.is_valid_dsn(dsn):
            raise ValueError(
                f"Invalid PostgreSQL DSN format.\nProvided: {dsn}\nExpected: {self.get_sample_dsn()}"
            )
        
        parsed = urlparse(dsn)
        config = {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "database": parsed.path.lstrip("/") if parsed.path else "",
            "user": parsed.username or "",
            "password": parsed.password or "",
        }
        
        query_params = parse_qs(parsed.query)
        if "sslmode" in query_params:
            sslmode = query_params["sslmode"][0]
            if sslmode == "disable":
                config["ssl"] = False
            elif sslmode == "require":
                config["ssl"] = "require"
            else:
                config["ssl"] = True
        
        return config
    
    def get_sample_dsn(self) -> str:
        return "postgres://postgres:password@localhost:5432/postgres?sslmode=require"
    
    def is_valid_dsn(self, dsn: str) -> bool:
        return dsn.startswith("postgres://") or dsn.startswith("postgresql://")


class PostgresConnector(Connector):
    def __init__(self):
        self.id: ConnectorType = "postgres"
        self.name = "PostgreSQL"
        self.dsn_parser = PostgresDSNParser()
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self, dsn: str, init_script: Optional[str] = None) -> None:
        try:
            config = self.dsn_parser.parse(dsn)
            self.pool = await asyncpg.create_pool(
                host=config["host"],
                port=config["port"],
                database=config["database"],
                user=config["user"],
                password=config["password"],
                ssl=config.get("ssl"),
            )
            
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            if init_script:
                async with self.pool.acquire() as conn:
                    await conn.execute(init_script)
            
            print("Successfully connected to PostgreSQL database", flush=True)
        except Exception as e:
            print(f"Failed to connect to PostgreSQL database: {e}", flush=True)
            raise
    
    async def disconnect(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def get_schemas(self) -> list[str]:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                ORDER BY schema_name
            """)
            return [row["schema_name"] for row in rows]
    
    async def get_tables(self, schema: Optional[str] = None) -> list[str]:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "public"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = $1
                ORDER BY table_name
            """, schema_to_use)
            return [row["table_name"] for row in rows]
    
    async def get_table_schema(
        self, table_name: str, schema: Optional[str] = None
    ) -> list[TableColumn]:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "public"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    column_name, 
                    data_type, 
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = $1
                AND table_name = $2
                ORDER BY ordinal_position
            """, schema_to_use, table_name)
            
            return [
                TableColumn(
                    column_name=row["column_name"],
                    data_type=row["data_type"],
                    is_nullable=row["is_nullable"],
                    column_default=row["column_default"],
                )
                for row in rows
            ]
    
    async def table_exists(
        self, table_name: str, schema: Optional[str] = None
    ) -> bool:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "public"
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = $1 
                    AND table_name = $2
                )
            """, schema_to_use, table_name)
            return result
    
    async def get_table_indexes(
        self, table_name: str, schema: Optional[str] = None
    ) -> list[TableIndex]:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "public"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    i.relname as index_name,
                    array_agg(a.attname) as column_names,
                    ix.indisunique as is_unique,
                    ix.indisprimary as is_primary
                FROM 
                    pg_class t,
                    pg_class i,
                    pg_index ix,
                    pg_attribute a,
                    pg_namespace ns
                WHERE 
                    t.oid = ix.indrelid
                    AND i.oid = ix.indexrelid
                    AND a.attrelid = t.oid
                    AND a.attnum = ANY(ix.indkey)
                    AND t.relkind = 'r'
                    AND t.relname = $1
                    AND ns.oid = t.relnamespace
                    AND ns.nspname = $2
                GROUP BY 
                    i.relname, 
                    ix.indisunique,
                    ix.indisprimary
                ORDER BY 
                    i.relname
            """, table_name, schema_to_use)
            
            return [
                TableIndex(
                    index_name=row["index_name"],
                    column_names=list(row["column_names"]),
                    is_unique=row["is_unique"],
                    is_primary=row["is_primary"],
                )
                for row in rows
            ]
    
    async def get_stored_procedures(
        self, schema: Optional[str] = None
    ) -> list[str]:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "public"
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT routine_name
                FROM information_schema.routines
                WHERE routine_schema = $1
                ORDER BY routine_name
            """, schema_to_use)
            return [row["routine_name"] for row in rows]
    
    async def get_stored_procedure_detail(
        self, procedure_name: str, schema: Optional[str] = None
    ) -> StoredProcedure:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        schema_to_use = schema or "public"
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    routine_name as procedure_name,
                    routine_type,
                    CASE WHEN routine_type = 'PROCEDURE' THEN 'procedure' ELSE 'function' END as procedure_type,
                    external_language as language,
                    data_type as return_type,
                    routine_definition as definition
                FROM information_schema.routines
                WHERE routine_schema = $1
                AND routine_name = $2
            """, schema_to_use, procedure_name)
            
            if not row:
                raise ValueError(
                    f"Stored procedure '{procedure_name}' not found in schema '{schema_to_use}'"
                )
            
            param_rows = await conn.fetch("""
                SELECT string_agg(
                    parameter_name || ' ' || 
                    parameter_mode || ' ' || 
                    data_type,
                    ', '
                ) as parameter_list
                FROM information_schema.parameters
                WHERE specific_schema = $1
                AND specific_name = $2
                AND parameter_name IS NOT NULL
            """, schema_to_use, procedure_name)
            
            parameter_list = param_rows[0]["parameter_list"] if param_rows else ""
            
            definition = row["definition"]
            if not definition:
                try:
                    oid_row = await conn.fetchrow("""
                        SELECT p.oid, p.prosrc
                        FROM pg_proc p
                        JOIN pg_namespace n ON p.pronamespace = n.oid
                        WHERE p.proname = $1
                        AND n.nspname = $2
                    """, procedure_name, schema_to_use)
                    
                    if oid_row:
                        def_result = await conn.fetchval(
                            "SELECT pg_get_functiondef($1)", oid_row["oid"]
                        )
                        definition = def_result if def_result else oid_row["prosrc"]
                except Exception:
                    pass
            
            return StoredProcedure(
                procedure_name=row["procedure_name"],
                procedure_type=row["procedure_type"],
                language=row["language"] or "sql",
                parameter_list=parameter_list or "",
                return_type=row["return_type"] if row["return_type"] != "void" else None,
                definition=definition,
            )
    
    async def execute_sql(
        self, sql: str, options: ExecuteOptions
    ) -> SQLResult:
        if not self.pool:
            raise RuntimeError("Not connected to database")
        
        async with self.pool.acquire() as conn:
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            
            if len(statements) == 1:
                processed_sql = apply_row_limit(statements[0], options.max_rows, self.id)
                rows = await conn.fetch(processed_sql)
                rows_dict = [dict(row) for row in rows]
                columns = list(rows[0].keys()) if rows else []
                return SQLResult(
                    rows=rows_dict,
                    row_count=len(rows_dict),
                    columns=columns
                )
            else:
                all_rows = []
                async with conn.transaction():
                    for statement in statements:
                        processed_sql = apply_row_limit(statement, options.max_rows, self.id)
                        result = await conn.fetch(processed_sql)
                        if result:
                            all_rows.extend([dict(row) for row in result])
                
                columns = list(all_rows[0].keys()) if all_rows else []
                return SQLResult(
                    rows=all_rows,
                    row_count=len(all_rows),
                    columns=columns
                )


from .interface import ConnectorRegistry
postgres_connector = PostgresConnector()
ConnectorRegistry.register(postgres_connector)

