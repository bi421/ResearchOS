import re

path = 'macro_intelligence/econometrics/models.py'
with open(path, 'r') as f:
    lines = f.readlines()

fixed = 0
for i, line in enumerate(lines):
    stripped = line.rstrip('\n')
    # Fix: '        def from_dict(cls, data: Dict[str, Any]) -> RegressionResult:' -> 4 spaces
    if stripped == '        def from_dict(cls, data: Dict[str, Any]) -> RegressionResult:':
        lines[i] = '    def from_dict(cls, data: Dict[str, Any]) -> RegressionResult:\n'
        fixed += 1
        print(f'Fixed line {i+1}: def from_dict indentation')

with open(path, 'w') as f:
    f.writelines(lines)

print(f'Total fixes: {fixed}')
