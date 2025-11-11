#!/usr/bin/env python3
import asyncio
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, Prompt, TextContent

from .connectors.manager import ConnectorManager
from .connectors.interface import ConnectorRegistry
from .config.env import resolve_config
from .config.toml_loader import load_toml_config
from .config.demo_loader import get_demo_dsn, get_demo_init_script
from .resources import (
    schemas_resource_handler,
    tables_resource_handler,
    table_schema_resource_handler,
    indexes_resource_handler,
    procedures_resource_handler,
    procedure_detail_resource_handler,
)
from .tools import execute_sql_tool_handler
from .prompts import generate_sql_prompt_handler, explain_db_prompt_handler
from .utils.dsn_obfuscate import redact_dsn
from . import __version__


SERVER_NAME = "DMCP-DB MCP Server"
SERVER_VERSION = __version__


def generate_banner(version: str, modes: list[str] = []) -> str:
    mode_text = f" [{' | '.join(modes)}]" if modes else ""
    
    return f"""
 ____  __  __  ____ ____        ____  ____  
(  _ \(  \/  )/ ___|  _ \      |  _ \| __ ) 
 | | | )    (| |   | |_) |_____| | | |  _ \ 
 | |_| | |\/| | |___|  __/|_____| |_| | |_) |
 |____/|_|  |_|\____|_|        |____/|____/ 
                                             
v{version}{mode_text} - Python MCP Database Server
"""


async def main():
    try:
        config = resolve_config()
        
        modes = []
        if config.get("readonly"):
            modes.append("READ-ONLY")
        if config.get("demo"):
            modes.append("DEMO")
        if config.get("instance_id"):
            modes.append(f"ID:{config['instance_id']}")
        
        print(generate_banner(SERVER_VERSION, modes), file=sys.stderr)
        
        manager = ConnectorManager.get_instance()
        
        if config.get("config_file"):
            toml_config = load_toml_config(config["config_file"])
            await manager.connect_with_sources(toml_config.sources)
            print(f"✓ Loaded {len(toml_config.sources)} source(s) from TOML config", file=sys.stderr)
        elif config.get("demo"):
            dsn = get_demo_dsn()
            init_script = get_demo_init_script()
            await manager.connect_with_dsn(dsn, init_script)
            print("✓ Connected to demo SQLite database", file=sys.stderr)
        elif config.get("dsn"):
            dsn = config["dsn"]
            await manager.connect_with_dsn(dsn)
            print(f"✓ Connected to database: {redact_dsn(dsn)}", file=sys.stderr)
        else:
            available_connectors = ConnectorRegistry.get_all_sample_dsns()
            sample_formats = "\n".join([
                f"  - {conn_id}: {dsn}"
                for conn_id, dsn in available_connectors.items()
            ])
            
            print(f"""
ERROR: Database connection configuration is required.

Please provide configuration in one of these ways:

1. Demo mode: --demo
2. TOML config: --config=path/to/dmcp-db.toml or ./dmcp-db.toml
3. Command line: --dsn="your-connection-string"
4. Environment variable: export DSN="your-connection-string"
5. .env file: DSN=your-connection-string

Example DSN formats:
{sample_formats}
""", file=sys.stderr)
            sys.exit(1)
        
        server = Server(SERVER_NAME)
        
        @server.list_resources()
        async def list_resources():
            return [
                Resource(
                    uri="db://schemas",
                    name="Database Schemas",
                    mimeType="application/json",
                    description="List all database schemas"
                )
            ]
        
        @server.read_resource()
        async def read_resource(uri: str):
            if uri == "db://schemas":
                result = await schemas_resource_handler(uri)
                return result["contents"]
            elif uri.startswith("db://schemas/") and "/tables/" in uri:
                parts = uri.replace("db://schemas/", "").split("/")
                if len(parts) == 2:
                    schema_name = parts[0]
                    result = await tables_resource_handler(uri, schema_name)
                    return result["contents"]
                elif len(parts) == 4 and parts[2] == "indexes":
                    schema_name, _, table_name, _ = parts
                    result = await indexes_resource_handler(uri, schema_name, table_name)
                    return result["contents"]
                elif len(parts) == 3:
                    schema_name, _, table_name = parts
                    result = await table_schema_resource_handler(uri, schema_name, table_name)
                    return result["contents"]
            elif uri.startswith("db://schemas/") and "/procedures/" in uri:
                parts = uri.replace("db://schemas/", "").split("/")
                if len(parts) == 2:
                    schema_name = parts[0]
                    result = await procedures_resource_handler(uri, schema_name)
                    return result["contents"]
                elif len(parts) == 3:
                    schema_name, _, proc_name = parts
                    result = await procedure_detail_resource_handler(uri, schema_name, proc_name)
                    return result["contents"]
            
            return [TextContent(type="text", text='{"success": false, "error": "Resource not found"}')]
        
        @server.list_tools()
        async def list_tools():
            tool_name = "execute_sql"
            if config.get("instance_id"):
                tool_name = f"execute_sql_{config['instance_id']}"
            
            return [
                Tool(
                    name=tool_name,
                    description="Execute SQL query on the database",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "sql": {
                                "type": "string",
                                "description": "SQL query to execute"
                            },
                            "source_id": {
                                "type": "string",
                                "description": "Database source ID (for multi-database)"
                            }
                        },
                        "required": ["sql"]
                    }
                )
            ]
        
        @server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name.startswith("execute_sql"):
                sql = arguments.get("sql", "")
                source_id = arguments.get("source_id")
                readonly = config.get("readonly", False)
                result = await execute_sql_tool_handler(sql, source_id, readonly)
                return result["content"]
            
            return [TextContent(type="text", text='{"success": false, "error": "Tool not found"}')]
        
        @server.list_prompts()
        async def list_prompts():
            return [
                Prompt(
                    name="generate_sql",
                    description="Generate SQL query from natural language description",
                    arguments=[
                        {
                            "name": "description",
                            "description": "Natural language description of the query",
                            "required": True
                        }
                    ]
                ),
                Prompt(
                    name="explain_db",
                    description="Explain database structure or specific table",
                    arguments=[
                        {
                            "name": "table_name",
                            "description": "Table name to explain (optional)",
                            "required": False
                        },
                        {
                            "name": "schema_name",
                            "description": "Schema name (optional)",
                            "required": False
                        }
                    ]
                )
            ]
        
        @server.get_prompt()
        async def get_prompt(name: str, arguments: dict):
            if name == "generate_sql":
                description = arguments.get("description", "")
                prompt_text = await generate_sql_prompt_handler(description)
                return [TextContent(type="text", text=prompt_text)]
            elif name == "explain_db":
                table_name = arguments.get("table_name")
                schema_name = arguments.get("schema_name")
                prompt_text = await explain_db_prompt_handler(table_name, schema_name)
                return [TextContent(type="text", text=prompt_text)]
            
            return [TextContent(type="text", text="Prompt not found")]
        
        print(f"✓ MCP Server initialized", file=sys.stderr)
        print(f"✓ Transport: {config.get('transport', 'stdio')}", file=sys.stderr)
        print(f"✓ Ready to accept requests", file=sys.stderr)
        print("", file=sys.stderr)
        
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
        
    except KeyboardInterrupt:
        print("\n\n✓ Shutting down gracefully...", file=sys.stderr)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
    finally:
        manager = ConnectorManager.get_instance()
        await manager.disconnect_all()
        print("✓ Disconnected from database(s)", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())

