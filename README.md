# DMCP-DB: Python MCP Database Server

A production-ready Python implementation of the Model Context Protocol (MCP) server for universal database connectivity. Connect Cursor, Claude Desktop, and other MCP clients to PostgreSQL, MySQL, MariaDB, SQL Server, and SQLite databases.

## Features

### Database Support
- ✅ **PostgreSQL** - Full support with connection pooling
- ✅ **MySQL** - Full support with connection pooling
- ✅ **MariaDB** - Full support (MySQL-compatible)
- ✅ **SQL Server** - Full support with Azure AD auth
- ✅ **SQLite** - Full support with clone() for multi-source

### MCP Protocol
- ✅ **Resources** - Database exploration (schemas, tables, indexes, procedures)
- ✅ **Tools** - SQL execution with multi-statement support
- ✅ **Prompts** - AI-assisted SQL generation and database explanation
- ✅ **Stdio Transport** - Direct integration with Cursor/Claude Desktop

### Security Features
- ✅ **Read-Only Mode** - Restrict to SELECT queries only
- ✅ **Row Limiting** - Prevent accidental data dumps
- ✅ **Password Redaction** - Automatic password masking in logs
- ✅ **SSH Tunneling** - Secure remote database connections
- ✅ **SSL/TLS Support** - Encrypted database connections

### Configuration
- ✅ **TOML Config** - Multi-database project configuration
- ✅ **CLI Arguments** - Quick testing and single database
- ✅ **Environment Variables** - Docker and CI/CD deployment
- ✅ **.env Files** - Local development
- ✅ **Demo Mode** - Built-in sample database

## Installation

### Requirements
- Python 3.13+
- pip or uv

### Install from Source

```bash
git clone https://github.com/yourusername/dmcp-db.git
cd dmcp-db
pip install -e .
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

### Demo Mode

Try DMCP-DB with a sample SQLite database:

```bash
dmcp-db --demo
```

### Connect to PostgreSQL

```bash
dmcp-db --dsn="postgres://user:password@localhost:5432/mydb"
```

### Connect to MySQL

```bash
dmcp-db --dsn="mysql://root:password@localhost:3306/mydb"
```

### Connect to SQLite

```bash
dmcp-db --dsn="sqlite:///path/to/database.db"
```

### Multi-Database Configuration

Create `dmcp-db.toml`:

```toml
[[sources]]
id = "prod_pg"
type = "postgres"
host = "localhost"
port = 5432
user = "postgres"
password = "password"
database = "production"
readonly = true
max_rows = 1000

[[sources]]
id = "staging_mysql"
type = "mysql"
host = "localhost"
port = 3306
user = "root"
password = "secret"
database = "staging"
```

Run:

```bash
dmcp-db --config=dmcp-db.toml
```

## Cursor Integration

### Step 1: Install DMCP-DB

```bash
cd dmcp-db
pip install -e .
```

### Step 2: Configure Cursor

Open Cursor Settings → Features → MCP, or edit `~/.cursor/mcp.json` (Linux/Mac) or `%APPDATA%\Cursor\User\globalStorage\mcp.json` (Windows):

```json
{
  "mcpServers": {
    "dmcp-db": {
      "command": "python",
      "args": ["-m", "dmcp", "--demo"]
    }
  }
}
```

### Step 3: Connect to Your Database

**PostgreSQL:**
```json
{
  "mcpServers": {
    "postgres-prod": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--dsn=postgres://user:password@localhost:5432/mydb",
        "--readonly"
      ]
    }
  }
}
```

**MySQL:**
```json
{
  "mcpServers": {
    "mysql-dev": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--type=mysql",
        "--host=localhost",
        "--port=3306",
        "--user=root",
        "--password=secret",
        "--database=mydb"
      ]
    }
  }
}
```

**Multi-Database:**
```json
{
  "mcpServers": {
    "my-databases": {
      "command": "python",
      "args": [
        "-m", "dmcp",
        "--config=C:\\path\\to\\dmcp-db.toml"
      ]
    }
  }
}
```

### Step 4: Use in Cursor

1. Restart Cursor
2. Open Cursor chat
3. The MCP server will appear with a green indicator
4. Ask questions like:
   - "What tables are in the database?"
   - "Show me the schema for the users table"
   - "SELECT * FROM employees WHERE department = 'Engineering'"

## Configuration Options

### Command Line Arguments

```bash
# Database Connection
--dsn="connection-string"          # Full DSN
--type=postgres                     # Database type
--host=localhost                    # Database host
--port=5432                         # Database port
--user=myuser                       # Database user
--password=mypass                   # Database password
--database=mydb                     # Database name

# Configuration File
--config=path/to/config.toml       # TOML config file

# Demo Mode
--demo                              # Use sample database

# Transport
--transport=stdio                   # stdio (default) or http
--http-port=8080                    # HTTP server port

# Security
--readonly                          # Enable read-only mode
--max-rows=1000                     # Limit result rows

# SSH Tunnel
--ssh-host=bastion.example.com     # SSH host
--ssh-port=22                       # SSH port
--ssh-user=ubuntu                   # SSH user
--ssh-password=secret               # SSH password
--ssh-key=~/.ssh/id_rsa            # SSH private key

# Multi-Instance
--id=prod                           # Instance ID suffix
```

### Environment Variables

```bash
# Database Connection
export DSN="postgres://user:pass@localhost:5432/db"

# Or individual parameters
export DB_TYPE=postgres
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=myuser
export DB_PASSWORD=mypass
export DB_NAME=mydb

# Security
export READONLY=true
export MAX_ROWS=1000

# SSH Tunnel
export SSH_HOST=bastion.example.com
export SSH_USER=ubuntu
export SSH_KEY=~/.ssh/id_rsa
```

### .env File

Create `.env`:

```env
DSN=postgres://user:password@localhost:5432/mydb
READONLY=true
MAX_ROWS=1000
```

## MCP Resources

### List Schemas
```
db://schemas
```

### List Tables
```
db://schemas/{schema}/tables
```

### Table Structure
```
db://schemas/{schema}/tables/{table}
```

### Table Indexes
```
db://schemas/{schema}/tables/{table}/indexes
```

### Stored Procedures
```
db://schemas/{schema}/procedures
db://schemas/{schema}/procedures/{procedure}
```

## MCP Tools

### execute_sql

Execute SQL queries with multi-statement support:

```json
{
  "sql": "SELECT * FROM users WHERE id = 1",
  "source_id": "prod_pg"
}
```

## MCP Prompts

### generate_sql

Generate SQL from natural language:

```json
{
  "description": "Get all users who registered in the last 30 days"
}
```

### explain_db

Explain database structure:

```json
{
  "table_name": "users",
  "schema_name": "public"
}
```

## Security Best Practices

### Read-Only Mode

Always enable read-only mode for production databases:

```bash
dmcp-db --dsn="..." --readonly
```

### Row Limiting

Prevent accidental large data dumps:

```bash
dmcp-db --dsn="..." --max-rows=1000
```

### SSH Tunneling

Use SSH tunnels for remote databases:

```bash
dmcp-db --dsn="postgres://user:pass@localhost:5432/db" \
  --ssh-host=bastion.example.com \
  --ssh-user=ubuntu \
  --ssh-key=~/.ssh/id_rsa
```

### Password Protection

Never commit passwords. Use:
- Environment variables
- .env files (add to .gitignore)
- SSH key authentication
- Secrets management systems

## Troubleshooting

### Connection Issues

**PostgreSQL:**
```bash
# Test connection
psql -h localhost -U postgres -d mydb

# Check SSL mode
dmcp-db --dsn="postgres://...?sslmode=disable"
```

**MySQL:**
```bash
# Test connection
mysql -h localhost -u root -p mydb

# Check charset
dmcp-db --dsn="mysql://...?charset=utf8mb4"
```

**SQL Server:**
```bash
# Check ODBC driver
odbcinst -q -d

# Trust server certificate
dmcp-db --dsn="mssql://...?TrustServerCertificate=yes"
```

### MCP Server Not Appearing in Cursor

1. Check Cursor logs: Help → Show Logs
2. Verify Python path: `which python` or `where python`
3. Test server manually: `python -m dmcp --demo`
4. Check JSON syntax in mcp.json
5. Restart Cursor completely

### Permission Denied

```bash
# Linux/Mac
chmod +x $(which dmcp-db)

# Or use full Python path
"command": "/usr/bin/python3"
```

## Development

### Run from Source

```bash
cd dmcp-db
python -m dmcp --demo
```

### Run Tests

```bash
pytest
```

### Code Style

```bash
black src/
isort src/
```

## Architecture

DMCP-DB follows a modular architecture:

- **Connectors** - Database-specific implementations
- **Resources** - MCP resource handlers
- **Tools** - MCP tool handlers
- **Prompts** - MCP prompt handlers
- **Config** - Configuration system
- **Utils** - Security and utility functions

See `reference/` directory for detailed architecture documentation.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Support

- Issues: https://github.com/yourusername/dmcp-db/issues
- Documentation: https://github.com/yourusername/dmcp-db/tree/main/reference
