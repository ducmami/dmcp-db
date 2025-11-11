from ..connectors.manager import ConnectorManager
from ..utils.response_formatter import create_tool_success_response, create_tool_error_response
from ..utils.allowed_keywords import are_all_statements_readonly
from ..types.sql import ExecuteOptions


async def execute_sql_tool_handler(
    sql: str,
    source_id: str | None = None,
    readonly: bool = False
) -> dict:
    try:
        connector = ConnectorManager.get_current_connector(source_id)
        options = ConnectorManager.get_current_execute_options(source_id)
        
        if readonly or options.readonly:
            if not are_all_statements_readonly(sql, connector.id):
                return create_tool_error_response(
                    f"Read-only mode is enabled. Only read operations allowed.",
                    "READONLY_VIOLATION"
                )
        
        result = await connector.execute_sql(sql, options)
        
        return create_tool_success_response({
            "rows": result.rows,
            "row_count": result.row_count,
            "columns": result.columns,
            "source_id": source_id or "(default)"
        })
    except Exception as e:
        return create_tool_error_response(str(e), "EXECUTION_ERROR")

