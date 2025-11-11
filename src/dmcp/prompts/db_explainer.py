from ..connectors.manager import ConnectorManager


async def explain_db_prompt_handler(
    table_name: str | None = None,
    schema_name: str | None = None,
    source_id: str | None = None
) -> str:
    try:
        connector = ConnectorManager.get_current_connector(source_id)
        
        if table_name:
            columns = await connector.get_table_schema(table_name, schema_name)
            indexes = await connector.get_table_indexes(table_name, schema_name)
            
            column_info = "\n".join([
                f"  - {col.column_name}: {col.data_type} "
                f"({'NOT NULL' if col.is_nullable == 'NO' else 'NULL'}) "
                f"(default: {col.column_default or 'none'})"
                for col in columns
            ])
            
            index_info = "\n".join([
                f"  - {idx.index_name}: {', '.join(idx.column_names)} "
                f"({'UNIQUE' if idx.is_unique else 'NON-UNIQUE'}) "
                f"({'PRIMARY KEY' if idx.is_primary else ''})"
                for idx in indexes
            ])
            
            prompt = f"""Explain the database table: {table_name}
Schema: {schema_name or 'default'}

Columns:
{column_info}

Indexes:
{index_info}

Please explain the purpose and structure of this table, including:
- What data it stores
- Key relationships indicated by indexes
- Any notable constraints or defaults
"""
            return prompt
        else:
            schemas = await connector.get_schemas()
            
            db_info = []
            for schema in schemas[:5]:
                tables = await connector.get_tables(schema)
                db_info.append(f"Schema: {schema}\n  Tables: {', '.join(tables)}")
            
            prompt = f"""Explain the database structure:

Database Type: {connector.name}

{chr(10).join(db_info)}

Please provide an overview of this database structure, including:
- The purpose of each schema
- Main tables and their likely relationships
- Overall database organization
"""
            return prompt
    except Exception as e:
        return f"Error generating explanation prompt: {e}"

