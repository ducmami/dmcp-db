import os
import sys
import argparse
from typing import Optional
from dotenv import load_dotenv
from ..types.config import SourceConfig, SSHConfig


def load_env_files() -> None:
    is_development = os.getenv("PYTHON_ENV") == "development"
    
    if is_development:
        if os.path.exists(".env.local"):
            load_dotenv(".env.local")
    
    if os.path.exists(".env"):
        load_dotenv(".env")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DMCP-DB: Python MCP Database Server")
    
    parser.add_argument("--dsn", help="Database DSN connection string")
    parser.add_argument("--type", choices=["postgres", "mysql", "mariadb", "sqlite", "sqlserver"], help="Database type")
    parser.add_argument("--host", help="Database host")
    parser.add_argument("--port", type=int, help="Database port")
    parser.add_argument("--user", help="Database user")
    parser.add_argument("--password", help="Database password")
    parser.add_argument("--database", help="Database name")
    
    parser.add_argument("--config", help="Path to TOML configuration file")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode with sample database")
    
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio", help="Transport mode")
    parser.add_argument("--http-port", type=int, default=8080, help="HTTP server port")
    
    parser.add_argument("--readonly", action="store_true", help="Enable read-only mode")
    parser.add_argument("--max-rows", type=int, help="Maximum rows to return")
    parser.add_argument("--id", help="Instance ID for multi-instance support")
    
    parser.add_argument("--ssh-host", help="SSH tunnel host")
    parser.add_argument("--ssh-port", type=int, default=22, help="SSH tunnel port")
    parser.add_argument("--ssh-user", help="SSH tunnel user")
    parser.add_argument("--ssh-password", help="SSH tunnel password")
    parser.add_argument("--ssh-key", help="SSH private key path")
    parser.add_argument("--ssh-passphrase", help="SSH private key passphrase")
    
    return parser.parse_args()


def build_dsn_from_params(
    db_type: Optional[str],
    host: Optional[str],
    port: Optional[int],
    user: Optional[str],
    password: Optional[str],
    database: Optional[str]
) -> Optional[str]:
    if not db_type:
        return None
    
    if db_type == "sqlite":
        return database if database else None
    
    if not all([host, user, password, database]):
        return None
    
    default_ports = {
        "postgres": 5432,
        "mysql": 3306,
        "mariadb": 3306,
        "sqlserver": 1433,
    }
    
    port = port or default_ports.get(db_type, 5432)
    
    if db_type in ["postgres", "mysql", "mariadb"]:
        return f"{db_type}://{user}:{password}@{host}:{port}/{database}"
    elif db_type == "sqlserver":
        return f"mssql://{user}:{password}@{host}:{port}/{database}"
    
    return None


def resolve_config() -> dict:
    load_env_files()
    args = parse_args()
    
    config = {
        "dsn": None,
        "sources": [],
        "transport": args.transport,
        "http_port": args.http_port,
        "readonly": args.readonly,
        "max_rows": args.max_rows,
        "instance_id": args.id,
        "demo": args.demo,
        "config_file": args.config,
    }
    
    if args.config and os.path.exists(args.config):
        config["config_file"] = args.config
        return config
    
    if os.path.exists("dmcp-db.toml"):
        config["config_file"] = "dmcp-db.toml"
        return config
    
    if args.demo:
        config["demo"] = True
        return config
    
    if args.dsn:
        config["dsn"] = args.dsn
    elif args.type:
        dsn = build_dsn_from_params(
            args.type, args.host, args.port, args.user, args.password, args.database
        )
        if dsn:
            config["dsn"] = dsn
    else:
        env_dsn = os.getenv("DSN")
        if env_dsn:
            config["dsn"] = env_dsn
        else:
            dsn = build_dsn_from_params(
                os.getenv("DB_TYPE"),
                os.getenv("DB_HOST"),
                int(os.getenv("DB_PORT")) if os.getenv("DB_PORT") else None,
                os.getenv("DB_USER"),
                os.getenv("DB_PASSWORD"),
                os.getenv("DB_NAME")
            )
            if dsn:
                config["dsn"] = dsn
    
    if args.ssh_host:
        config["ssh"] = SSHConfig(
            host=args.ssh_host,
            port=args.ssh_port,
            user=args.ssh_user or "",
            password=args.ssh_password,
            private_key=args.ssh_key,
            private_key_password=args.ssh_passphrase,
        )
    
    return config

