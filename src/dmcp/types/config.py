from typing import Any
from pydantic import BaseModel, Field
from .sql import ConnectorType


class SSHConfig(BaseModel):
    host: str
    port: int = 22
    user: str
    password: str | None = None
    private_key: str | None = None
    private_key_password: str | None = None


class SourceConfig(BaseModel):
    id: str
    type: ConnectorType | None = None
    dsn: str | None = None
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    database: str | None = None
    readonly: bool = False
    max_rows: int | None = None
    ssh: SSHConfig | None = None
    init_script: str | None = None
    
    model_config = {
        "extra": "allow"
    }


class TOMLConfig(BaseModel):
    sources: list[SourceConfig] = Field(default_factory=list)
    transport: str = "stdio"
    port: int = 8080
    
    model_config = {
        "extra": "allow"
    }

