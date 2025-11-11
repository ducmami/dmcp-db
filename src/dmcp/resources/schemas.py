from ..connectors.manager import ConnectorManager
from ..utils.response_formatter import create_resource_success_response, create_resource_error_response


async def schemas_resource_handler(uri: str, source_id: str | None = None) -> dict:
    try:
        connector = ConnectorManager.get_current_connector(source_id)
        schemas = await connector.get_schemas()
        
        return create_resource_success_response(uri, {
            "schemas": schemas,
            "count": len(schemas)
        })
    except Exception as e:
        return create_resource_error_response(uri, str(e), "SCHEMA_LIST_ERROR")

