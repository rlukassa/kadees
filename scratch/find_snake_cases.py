import os
import re

src_dir = r"c:\Users\MSI\Desktop\kds\kadees\backend\src"
snake_case_pat = re.compile(r'\b[a-z0-9]+_[a-z0-9_]+\b')

# Exclude double underscores (dunder methods like __init__)
dunder_pat = re.compile(r'^__.*__$')

findings = {}

for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            matches = snake_case_pat.findall(content)
            filtered = [m for m in matches if not dunder_pat.match(m)]
            if filtered:
                findings[os.path.relpath(path, src_dir)] = sorted(list(set(filtered)))

for rel_path, words in findings.items():
    print(f"{rel_path}:")
    for w in words:
        print(f"  - {w}")
