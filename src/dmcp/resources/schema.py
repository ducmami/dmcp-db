from ..connectors.manager import ConnectorManager
from ..utils.response_formatter import create_resource_success_response, create_resource_error_response


async def table_schema_resource_handler(
    uri: str, schema_name: str, table_name: str, source_id: str | None = None
) -> dict:
    try:
        connector = ConnectorManager.get_current_connector(source_id)
        columns = await connector.get_table_schema(table_name, schema_name)
        
        return create_resource_success_response(uri, {
            "table": table_name,
            "schema": schema_name,
            "columns": [col.model_dump() for col in columns],
            "count": len(columns)
        })
    except Exception as e:
        return create_resource_error_response(uri, str(e), "TABLE_SCHEMA_ERROR")

