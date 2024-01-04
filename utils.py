def collapsible(text: str, clickable_string: str) -> str:
    return f"""<details>
    <summary>{clickable_string}</summary>
    {text}
    </details>"""
