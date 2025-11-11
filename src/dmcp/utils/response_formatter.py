import json
from typing import Any


def create_resource_success_response(uri: str, data: Any) -> dict[str, Any]:
    return {
        "contents": [
            {
                "uri": uri,
                "text": json.dumps({"success": True, "data": data}),
                "mimeType": "application/json"
            }
        ]
    }


def create_resource_error_response(uri: str, error: str, code: str = "ERROR") -> dict[str, Any]:
    return {
        "contents": [
            {
                "uri": uri,
                "text": json.dumps({"success": False, "error": error, "code": code}),
                "mimeType": "application/json"
            }
        ]
    }


def create_tool_success_response(data: Any) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"success": True, "data": data})
            }
        ]
    }


def create_tool_error_response(error: str, code: str = "ERROR") -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({"success": False, "error": error, "code": code})
            }
        ],
        "isError": True
    }

