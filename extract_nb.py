import json

notebook_path = r"C:\Users\MSI\Desktop\kds\kadees\backend\notebooks\meiosis_simulation.ipynb"
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

with open(r"C:\Users\MSI\Desktop\kds\kadees\scratch_notebook.py", "w", encoding='utf-8') as out:
    for c in nb['cells']:
        if c['cell_type'] == 'code':
            out.write("\n# ---CELL---\n")
            out.write("".join(c['source']))
