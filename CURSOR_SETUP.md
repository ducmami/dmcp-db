# Cursor Setup Guide for DMCP-DB

Complete guide to integrating DMCP-DB with Cursor IDE.

## Prerequisites

- Cursor IDE installed
- Python 3.13+ installed
- DMCP-DB installed (`pip install -e .` from dmcp-db directory)

## Configuration Methods

### Method 1: Demo Mode (Quick Test)

1. Open Cursor Settings → Features → MCP
2. Click "Add MCP Server"
3. Add configuration:

```json
{
  "mcpServers": {
    "dmcp-demo": {
      "command": "python",
      "args": ["-m", "dmcp", "--demo"]
    }
  }
}
```

4. Restart Cursor
5. Open chat and ask: "What tables are in the database?"

### Method 2: Single Database (DSN)

**PostgreSQL:**
```json
{
  "mcpServers": {
    "my-postgres": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--dsn=postgres://user:password@localhost:5432/mydb",
        "--readonly",
        "--max-rows=1000"
      ]
    }
  }
}
```

**MySQL:**
```json
{
  "mcpServers": {
    "my-mysql": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--dsn=mysql://root:password@localhost:3306/mydb"
      ]
    }
  }
}
```

**SQLite:**
```json
{
  "mcpServers": {
    "my-sqlite": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--dsn=sqlite:///C:/path/to/database.db"
      ]
    }
  }
}
```

**SQL Server:**
```json
{
  "mcpServers": {
    "my-sqlserver": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--dsn=mssql://sa:YourPassword@localhost:1433/mydb"
      ]
    }
  }
}
```

### Method 3: Individual Parameters

```json
{
  "mcpServers": {
    "my-db": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--type=postgres",
        "--host=localhost",
        "--port=5432",
        "--user=myuser",
        "--password=mypassword",
        "--database=mydb",
        "--readonly"
      ]
    }
  }
}
```

### Method 4: TOML Configuration (Multi-Database)

1. Create `dmcp-db.toml`:

```toml
[[sources]]
id = "prod"
type = "postgres"
host = "prod.example.com"
port = 5432
user = "readonly_user"
password = "secret"
database = "production"
readonly = true
max_rows = 1000

[[sources]]
id = "staging"
type = "mysql"
host = "staging.example.com"
port = 3306
user = "dev"
password = "secret"
database = "staging"
max_rows = 500

[[sources]]
id = "local"
type = "sqlite"
database = "./local.db"
```

2. Configure Cursor:

```json
{
  "mcpServers": {
    "my-databases": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--config=C:/path/to/dmcp-db.toml"
      ]
    }
  }
}
```

### Method 5: Environment Variables

1. Create `.env` file:

```env
DSN=postgres://user:password@localhost:5432/mydb
READONLY=true
MAX_ROWS=1000
```

2. Configure Cursor:

```json
{
  "mcpServers": {
    "my-db": {
      "command": "python",
      "args": ["-m", "dmcp"],
      "env": {
        "DSN": "postgres://user:password@localhost:5432/mydb",
        "READONLY": "true",
        "MAX_ROWS": "1000"
      }
    }
  }
}
```

## Advanced Configurations

### With SSH Tunnel

```json
{
  "mcpServers": {
    "remote-db": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--dsn=postgres://user:pass@localhost:5432/db",
        "--ssh-host=bastion.example.com",
        "--ssh-user=ubuntu",
        "--ssh-key=C:/Users/YourName/.ssh/id_rsa",
        "--readonly"
      ]
    }
  }
}
```

### Multi-Instance (Multiple Servers)

```json
{
  "mcpServers": {
    "prod-db": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--dsn=postgres://...prod...",
        "--id=prod",
        "--readonly"
      ]
    },
    "staging-db": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--dsn=postgres://...staging...",
        "--id=staging"
      ]
    }
  }
}
```

This creates tools: `execute_sql_prod` and `execute_sql_staging`

### With Custom Python Path

```json
{
  "mcpServers": {
    "my-db": {
      "command": "C:/Users/YourName/AppData/Local/Programs/Python/Python313/python.exe",
      "args": ["-m", "dmcp", "--demo"]
    }
  }
}
```

## Usage in Cursor

### Database Exploration

Ask Cursor:
- "What databases are available?"
- "List all tables in the public schema"
- "Show me the structure of the users table"
- "What indexes does the orders table have?"
- "List all stored procedures"

### SQL Queries

Ask Cursor:
- "SELECT * FROM users WHERE created_at > '2024-01-01'"
- "Show me the top 10 customers by total orders"
- "Get the average salary by department"
- "Find all employees hired in the last 6 months"

### AI-Assisted Queries

Ask Cursor:
- "Generate a query to find duplicate email addresses"
- "Create a query to calculate monthly revenue"
- "Help me write a query to join users and orders"
- "Explain what the customers table contains"

### Multi-Database Queries

With TOML config:
- "Query the prod database for active users"
- "Show tables in the staging database"
- "Execute on local: SELECT * FROM test_data"

## Troubleshooting

### Server Not Appearing

1. **Check Cursor MCP Settings:**
   - Settings → Features → MCP
   - Look for green indicator next to server name
   - Red indicator = server failed to start

2. **View Logs:**
   - Help → Show Logs
   - Look for MCP-related errors
   - Check Python errors

3. **Test Server Manually:**
   ```bash
   python -m dmcp --demo
   ```
   Should show banner and "Ready to accept requests"

4. **Verify Python Path:**
   ```bash
   # Windows
   where python
   
   # Linux/Mac
   which python3
   ```
   Use full path in Cursor config if needed

### Connection Errors

**PostgreSQL:**
```json
{
  "args": [
    "-m", "dmcp",
    "--dsn=postgres://user:pass@localhost:5432/db?sslmode=disable"
  ]
}
```

**MySQL:**
```json
{
  "args": [
    "-m", "dmcp",
    "--dsn=mysql://root:pass@localhost:3306/db?charset=utf8mb4"
  ]
}
```

**SQL Server:**
```json
{
  "args": [
    "-m", "dmcp",
    "--dsn=mssql://sa:pass@localhost:1433/db?TrustServerCertificate=yes"
  ]
}
```

### Permission Issues

**Windows:**
- Run Cursor as Administrator
- Check firewall settings
- Verify database port is open

**Linux/Mac:**
```bash
chmod +x $(which python3)
```

### Password with Special Characters

URL-encode passwords:
- `@` → `%40`
- `#` → `%23`
- `&` → `%26`
- `=` → `%3D`

Or use individual parameters:
```json
{
  "args": [
    "--type=postgres",
    "--password=my@pass#word"
  ]
}
```

## Best Practices

### Security

1. **Always use read-only mode for production:**
   ```json
   {"args": ["--readonly"]}
   ```

2. **Limit result rows:**
   ```json
   {"args": ["--max-rows=1000"]}
   ```

3. **Use SSH tunnels for remote databases:**
   ```json
   {"args": ["--ssh-host=...", "--ssh-key=..."]}
   ```

4. **Never commit passwords:**
   - Use environment variables
   - Use .env files (add to .gitignore)
   - Use SSH key authentication

### Performance

1. **Use connection pooling (automatic)**
2. **Set appropriate max_rows limits**
3. **Use indexes for large tables**
4. **Close unused connections**

### Organization

1. **Use descriptive server names:**
   ```json
   {
     "prod-readonly": {...},
     "staging-full": {...},
     "local-dev": {...}
   }
   ```

2. **Group by environment:**
   ```json
   {
     "prod-postgres": {...},
     "prod-mysql": {...},
     "staging-postgres": {...}
   }
   ```

3. **Use TOML for multiple databases**

## Example Workflows

### Development Workflow

```json
{
  "mcpServers": {
    "dev-db": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--dsn=postgres://dev:dev@localhost:5432/dev_db"
      ]
    }
  }
}
```

### Production Read-Only

```json
{
  "mcpServers": {
    "prod-readonly": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--dsn=postgres://readonly:***@prod.example.com:5432/prod",
        "--ssh-host=bastion.example.com",
        "--ssh-user=ops",
        "--ssh-key=~/.ssh/prod_key",
        "--readonly",
        "--max-rows=100"
      ]
    }
  }
}
```

### Multi-Environment

```json
{
  "mcpServers": {
    "all-environments": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--config=/path/to/environments.toml"
      ]
    }
  }
}
```

## Support

- GitHub Issues: https://github.com/yourusername/dmcp-db/issues
- Documentation: See README.md and reference/ directory
- MCP Protocol: https://modelcontextprotocol.io

