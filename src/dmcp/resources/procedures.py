from ..connectors.manager import ConnectorManager
from ..utils.response_formatter import create_resource_success_response, create_resource_error_response


async def procedures_resource_handler(uri: str, schema_name: str, source_id: str | None = None) -> dict:
    try:
        connector = ConnectorManager.get_current_connector(source_id)
        procedures = await connector.get_stored_procedures(schema_name)
        
        return create_resource_success_response(uri, {
            "procedures": procedures,
            "schema": schema_name,
            "count": len(procedures)
        })
    except Exception as e:
        return create_resource_error_response(uri, str(e), "PROCEDURE_LIST_ERROR")


async def procedure_detail_resource_handler(
    uri: str, schema_name: str, procedure_name: str, source_id: str | None = None
) -> dict:
    try:
        connector = ConnectorManager.get_current_connector(source_id)
        procedure = await connector.get_stored_procedure_detail(procedure_name, schema_name)
        
        return create_resource_success_response(uri, {
            "procedure": procedure.model_dump(),
            "schema": schema_name
        })
    except Exception as e:
        return create_resource_error_response(uri, str(e), "PROCEDURE_DETAIL_ERROR")

