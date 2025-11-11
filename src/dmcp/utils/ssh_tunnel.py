import asyncio
from typing import Optional
from sshtunnel import SSHTunnelForwarder
import os


class SSHTunnelManager:
    def __init__(
        self,
        ssh_host: str,
        ssh_port: int,
        ssh_user: str,
        ssh_password: Optional[str] = None,
        ssh_private_key: Optional[str] = None,
        remote_host: str = "localhost",
        remote_port: int = 5432,
    ):
        self.ssh_host = ssh_host
        self.ssh_port = ssh_port
        self.ssh_user = ssh_user
        self.ssh_password = ssh_password
        self.ssh_private_key = ssh_private_key
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.tunnel: Optional[SSHTunnelForwarder] = None
        self.local_port: Optional[int] = None
    
    async def start(self) -> None:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._start_sync)
    
    def _start_sync(self) -> None:
        ssh_kwargs = {
            "ssh_address_or_host": (self.ssh_host, self.ssh_port),
            "ssh_username": self.ssh_user,
            "remote_bind_address": (self.remote_host, self.remote_port),
        }
        
        if self.ssh_password:
            ssh_kwargs["ssh_password"] = self.ssh_password
        elif self.ssh_private_key:
            if os.path.exists(os.path.expanduser(self.ssh_private_key)):
                ssh_kwargs["ssh_pkey"] = os.path.expanduser(self.ssh_private_key)
            else:
                ssh_kwargs["ssh_pkey"] = self.ssh_private_key
        else:
            for key_file in ["~/.ssh/id_rsa", "~/.ssh/id_ed25519", "~/.ssh/id_ecdsa"]:
                expanded = os.path.expanduser(key_file)
                if os.path.exists(expanded):
                    ssh_kwargs["ssh_pkey"] = expanded
                    break
        
        self.tunnel = SSHTunnelForwarder(**ssh_kwargs)
        self.tunnel.start()
        self.local_port = self.tunnel.local_bind_port
    
    async def stop(self) -> None:
        if self.tunnel:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.tunnel.stop)
            self.tunnel = None

