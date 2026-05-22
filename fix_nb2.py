import json

notebook_path = r"C:\Users\MSI\Desktop\kds\kadees\backend\notebooks\meiosis_simulation.ipynb"
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for c in nb['cells']:
    if c['cell_type'] == 'code':
        source = "".join(c['source'])
        if 'projectRoot = Path().resolve().parents[1]' in source:
            source = source.replace('projectRoot = Path().resolve().parents[1]', 
                                    "projectRoot = Path().resolve()\nif projectRoot.name == 'notebooks':\n    projectRoot = projectRoot.parents[1]")
            c['source'] = [s for s in source.splitlines(True)]

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook path fixed.")
