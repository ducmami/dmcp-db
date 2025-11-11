import asyncio
from .connectors import postgres, sqlite, mysql, mariadb, sqlserver
from .server import main

if __name__ == "__main__":
    asyncio.run(main())

