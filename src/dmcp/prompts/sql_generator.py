from ..connectors.manager import ConnectorManager


async def generate_sql_prompt_handler(description: str, source_id: str | None = None) -> str:
    try:
        connector = ConnectorManager.get_current_connector(source_id)
        schemas = await connector.get_schemas()
        
        schema_info = []
        for schema in schemas[:3]:
            tables = await connector.get_tables(schema)
            schema_info.append(f"Schema: {schema}\nTables: {', '.join(tables[:10])}")
        
        prompt = f"""Generate SQL query for: {description}

Database Type: {connector.name}
Available Schemas and Tables:
{chr(10).join(schema_info)}

Please generate a SQL query that accomplishes the requested task.
Consider the database type and available schema/table structure.
"""
        return prompt
    except Exception as e:
        return f"Error generating SQL prompt: {e}"

