import re

path = "/mnt/c/Users/User/Desktop/ResearchOS/cpp_quant_engine/bindings/python_bindings.cpp"
with open(path, "r") as f:
    content = f.read()

original = content
content = re.sub(r"nb::cast<bool>\(([^)]+)\.is_none\(\)\)", r"\1.is_none()", content)

with open(path, "w") as f:
    f.write(content)

print("changed" if content != original else "no match")
