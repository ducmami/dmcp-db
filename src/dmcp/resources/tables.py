from ..connectors.manager import ConnectorManager
from ..utils.response_formatter import create_resource_success_response, create_resource_error_response


async def tables_resource_handler(uri: str, schema_name: str, source_id: str | None = None) -> dict:
    try:
        connector = ConnectorManager.get_current_connector(source_id)
        tables = await connector.get_tables(schema_name)
        
        return create_resource_success_response(uri, {
            "tables": tables,
            "schema": schema_name,
            "count": len(tables)
        })
    except Exception as e:
        return create_resource_error_response(uri, str(e), "TABLE_LIST_ERROR")

