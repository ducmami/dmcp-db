import os
from typing import Optional


def parse_ssh_config(host: str) -> dict[str, str]:
    ssh_config_path = os.path.expanduser("~/.ssh/config")
    
    if not os.path.exists(ssh_config_path):
        return {}
    
    config = {}
    current_host = None
    
    with open(ssh_config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            
            key, value = parts[0].lower(), parts[1]
            
            if key == 'host':
                if value == host:
                    current_host = host
                else:
                    current_host = None
            elif current_host == host:
                config[key] = value
    
    return config


def get_ssh_config_value(host: str, key: str) -> Optional[str]:
    config = parse_ssh_config(host)
    return config.get(key.lower())

