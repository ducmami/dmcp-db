# DMCP-DB Quick Start Guide

Get up and running with DMCP-DB in 5 minutes.

## Step 1: Install (1 minute)

```bash
cd dmcp-db
pip install -e .
```

## Step 2: Test with Demo Mode (1 minute)

```bash
python -m dmcp --demo
```

You should see:
```
 ____  __  __  ____ ____        ____  ____  
(  _ \(  \/  )/ ___|  _ \      |  _ \| __ ) 
 | | | )    (| |   | |_) |_____| | | |  _ \ 
 | |_| | |\/| | |___|  __/|_____| |_| | |_) |
 |____/|_|  |_|\____|_|        |____/|____/ 
                                             
v0.1.0 [DEMO] - Python MCP Database Server

✓ Connected to demo SQLite database
✓ MCP Server initialized
✓ Transport: stdio
✓ Ready to accept requests
```

Press Ctrl+C to stop.

## Step 3: Connect to Your Database (2 minutes)

### PostgreSQL
```bash
python -m dmcp --dsn="postgres://user:password@localhost:5432/mydb"
```

### MySQL
```bash
python -m dmcp --dsn="mysql://root:password@localhost:3306/mydb"
```

### SQLite
```bash
python -m dmcp --dsn="sqlite:///path/to/database.db"
```

### SQL Server
```bash
python -m dmcp --dsn="mssql://sa:password@localhost:1433/mydb"
```

## Step 4: Add to Cursor (1 minute)

1. Open Cursor
2. Go to Settings → Features → MCP
3. Add this configuration:

```json
{
  "mcpServers": {
    "my-database": {
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

4. Restart Cursor
5. Open chat and ask: "What tables are in the database?"

## Step 5: Try It Out!

Ask Cursor:
- "List all tables"
- "Show me the structure of the users table"
- "SELECT * FROM employees WHERE department = 'Engineering'"
- "Generate a query to find the top 10 customers by revenue"

## Common Use Cases

### Read-Only Production Access
```bash
python -m dmcp \
  --dsn="postgres://readonly:***@prod.example.com:5432/prod" \
  --readonly \
  --max-rows=100
```

### Multiple Databases

Create `dmcp-db.toml`:
```toml
[[sources]]
id = "prod"
type = "postgres"
host = "prod.example.com"
database = "production"
user = "readonly"
password = "secret"
readonly = true

[[sources]]
id = "staging"
type = "mysql"
host = "staging.example.com"
database = "staging"
user = "dev"
password = "secret"
```

Run:
```bash
python -m dmcp --config=dmcp-db.toml
```

### With SSH Tunnel
```bash
python -m dmcp \
  --dsn="postgres://user:pass@localhost:5432/db" \
  --ssh-host=bastion.example.com \
  --ssh-user=ubuntu \
  --ssh-key=~/.ssh/id_rsa
```

## Troubleshooting

### "Module not found"
```bash
# Make sure you're in the dmcp-db directory
cd dmcp-db
pip install -e .
```

### "Connection refused"
```bash
# Check database is running
# PostgreSQL:
pg_isready -h localhost -p 5432

# MySQL:
mysqladmin ping -h localhost

# Test connection manually first
```

### "MCP server not appearing in Cursor"
1. Check Cursor logs: Help → Show Logs
2. Verify Python path: `which python` or `where python`
3. Test manually: `python -m dmcp --demo`
4. Restart Cursor completely

## Next Steps

- Read [README.md](README.md) for full documentation
- See [CURSOR_SETUP.md](CURSOR_SETUP.md) for advanced Cursor configuration
- Check [reference/](reference/) for architecture details
- Review [dmcp-db.toml.example](dmcp-db.toml.example) for multi-database setup

## Need Help?

- GitHub Issues: https://github.com/yourusername/dmcp-db/issues
- Documentation: README.md and CURSOR_SETUP.md
- MCP Protocol: https://modelcontextprotocol.io

## Security Reminder

⚠️ **Always use `--readonly` for production databases!**

```bash
python -m dmcp --dsn="..." --readonly --max-rows=1000
```

This prevents accidental data modification and limits result sizes.

---

**You're ready to go!** 🚀

Start exploring your databases with AI assistance in Cursor.

