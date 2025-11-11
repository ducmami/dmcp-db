from ..connectors.manager import ConnectorManager
from ..utils.response_formatter import create_resource_success_response, create_resource_error_response


async def indexes_resource_handler(
    uri: str, schema_name: str, table_name: str, source_id: str | None = None
) -> dict:
    try:
        connector = ConnectorManager.get_current_connector(source_id)
        indexes = await connector.get_table_indexes(table_name, schema_name)
        
        return create_resource_success_response(uri, {
            "table": table_name,
            "schema": schema_name,
            "indexes": [idx.model_dump() for idx in indexes],
            "count": len(indexes)
        })
    except Exception as e:
        return create_resource_error_response(uri, str(e), "INDEX_LIST_ERROR")

