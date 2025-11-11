import re
from ..types.sql import ConnectorType

ALLOWED_KEYWORDS: dict[ConnectorType, list[str]] = {
    "postgres": ["select", "with", "explain", "analyze", "show"],
    "mysql": ["select", "with", "explain", "analyze", "show", "describe", "desc"],
    "mariadb": ["select", "with", "explain", "analyze", "show", "describe", "desc"],
    "sqlite": ["select", "with", "explain", "analyze", "pragma"],
    "sqlserver": ["select", "with", "explain", "showplan"],
}


def strip_sql_comments(sql: str) -> str:
    lines = sql.split('\n')
    cleaned_lines = []
    for line in lines:
        comment_index = line.find('--')
        if comment_index >= 0:
            cleaned_lines.append(line[:comment_index])
        else:
            cleaned_lines.append(line)
    
    cleaned = '\n'.join(cleaned_lines)
    cleaned = re.sub(r'/\*[\s\S]*?\*/', ' ', cleaned)
    
    return cleaned.strip()


def is_readonly_sql(sql: str, connector_type: ConnectorType) -> bool:
    cleaned = strip_sql_comments(sql).lower()
    
    if not cleaned:
        return True
    
    first_word = cleaned.split()[0] if cleaned.split() else ""
    keyword_list = ALLOWED_KEYWORDS.get(connector_type, [])
    
    return first_word in keyword_list


def are_all_statements_readonly(sql: str, connector_type: ConnectorType) -> bool:
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    return all(is_readonly_sql(stmt, connector_type) for stmt in statements)

