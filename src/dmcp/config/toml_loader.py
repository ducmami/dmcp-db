import tomllib
from pathlib import Path
from ..types.config import TOMLConfig, SourceConfig, SSHConfig


def load_toml_config(config_path: str) -> TOMLConfig:
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, "rb") as f:
        data = tomllib.load(f)
    
    sources = []
    if "sources" in data:
        for source_data in data["sources"]:
            ssh_config = None
            if "ssh" in source_data:
                ssh_data = source_data["ssh"]
                ssh_config = SSHConfig(
                    host=ssh_data["host"],
                    port=ssh_data.get("port", 22),
                    user=ssh_data["user"],
                    password=ssh_data.get("password"),
                    private_key=ssh_data.get("private_key"),
                    private_key_password=ssh_data.get("private_key_password"),
                )
            
            source = SourceConfig(
                id=source_data["id"],
                type=source_data.get("type"),
                dsn=source_data.get("dsn"),
                host=source_data.get("host"),
                port=source_data.get("port"),
                user=source_data.get("user"),
                password=source_data.get("password"),
                database=source_data.get("database"),
                readonly=source_data.get("readonly", False),
                max_rows=source_data.get("max_rows"),
                ssh=ssh_config,
                init_script=source_data.get("init_script"),
            )
            sources.append(source)
    
    return TOMLConfig(
        sources=sources,
        transport=data.get("transport", "stdio"),
        port=data.get("port", 8080),
    )

