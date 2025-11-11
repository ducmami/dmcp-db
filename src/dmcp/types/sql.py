from typing import Any, Literal
from pydantic import BaseModel

ConnectorType = Literal["postgres", "mysql", "mariadb", "sqlite", "sqlserver"]


class TableColumn(BaseModel):
    column_name: str
    data_type: str
    is_nullable: str
    column_default: str | None = None


class TableIndex(BaseModel):
    index_name: str
    column_names: list[str]
    is_unique: bool
    is_primary: bool


class StoredProcedure(BaseModel):
    procedure_name: str
    procedure_type: Literal["procedure", "function"]
    language: str
    parameter_list: str
    return_type: str | None = None
    definition: str | None = None


class SQLResult(BaseModel):
    rows: list[dict[str, Any]]
    row_count: int = 0
    columns: list[str] = []
    
    model_config = {
        "arbitrary_types_allowed": True
    }


class ExecuteOptions(BaseModel):
    max_rows: int | None = None
    readonly: bool = False

