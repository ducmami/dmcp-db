import re
from ..types.sql import ConnectorType


def has_limit_clause(sql: str) -> bool:
    return bool(re.search(r'\blimit\s+\d+', sql, re.IGNORECASE))


def has_top_clause(sql: str) -> bool:
    return bool(re.search(r'\btop\s+\d+', sql, re.IGNORECASE))


def adjust_existing_limit(sql: str, max_rows: int) -> str:
    def replace_limit(match):
        existing_limit = int(match.group(1))
        return f"LIMIT {min(existing_limit, max_rows)}"
    
    return re.sub(r'\blimit\s+(\d+)', replace_limit, sql, flags=re.IGNORECASE)


def adjust_existing_top(sql: str, max_rows: int) -> str:
    def replace_top(match):
        existing_top = int(match.group(1))
        return f"TOP {min(existing_top, max_rows)}"
    
    return re.sub(r'\btop\s+(\d+)', replace_top, sql, flags=re.IGNORECASE)


def apply_row_limit(sql: str, max_rows: int | None, connector_type: ConnectorType) -> str:
    if not max_rows:
        return sql
    
    trimmed = sql.strip().lower()
    
    if not (trimmed.startswith('select') or trimmed.startswith('with')):
        return sql
    
    if connector_type == "sqlserver":
        if has_top_clause(sql):
            return adjust_existing_top(sql, max_rows)
        return re.sub(
            r'\bselect\b',
            f'SELECT TOP {max_rows}',
            sql,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        if has_limit_clause(sql):
            return adjust_existing_limit(sql, max_rows)
        return f"SELECT * FROM ({sql}) AS __dmcp_limiter_subquery LIMIT {max_rows}"

