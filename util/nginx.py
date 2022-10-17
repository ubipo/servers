DirectiveValue = str | dict[str, str] | tuple[str, dict[str, str]]
Directive = tuple[str, DirectiveValue]


def directive_value_to_str(value: DirectiveValue):
    if isinstance(value, str):
        # e.g. ssl_protocols TLSv1.2 TLSv1.3;
        return f"{value};"
    elif isinstance(value, bool):
        # e.g. ssl_stapling on;
        return directive_value_to_str("on" if value else "off")
    elif isinstance(value, dict):
        # e.g. server { ... }
        return directive_value_to_str(("", value))
    elif isinstance(value, tuple):
        # e.g. location /static { ... }
        tag, block_directives = value
        block_lines = "\n".join(map(directive_to_str, block_directives))
        indented_lines = "\n".join(f"    {line}" for line in block_lines.splitlines())
        return f"{tag}{' ' if tag else ''}{{\n{indented_lines}\n}}"

    return directive_value_to_str(str(value))


def directive_to_str(directive: Directive):
    if len(directive) == 3:
        key, tag, value = directive
        return f"{key} {directive_value_to_str((tag, value))}"
    key, value = directive
    return f"{key} {directive_value_to_str(value)}"


def create_nginx_config(*directives: Directive) -> str:
    return "\n".join(map(directive_to_str, directives))
