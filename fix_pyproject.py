content = open("pyproject.toml", encoding="utf-8").read()
old = "[tool.ruff]\nline-length = 100"
new = "[tool.ruff]\nexclude = [\"archive\"]\nline-length = 100"
if old in content:
    content = content.replace(old, new)
    open("pyproject.toml", "w", encoding="utf-8").write(content)
    print("OK")
else:
    print("NOT FOUND")
