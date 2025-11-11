from pydantic import BaseModel


class SSHTunnelConfig(BaseModel):
    ssh_host: str
    ssh_port: int = 22
    ssh_user: str
    ssh_password: str | None = None
    ssh_private_key: str | None = None
    ssh_private_key_password: str | None = None
    remote_host: str
    remote_port: int
    local_port: int | None = None

