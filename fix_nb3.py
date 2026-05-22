import json

notebook_path = r"C:\Users\MSI\Desktop\kds\kadees\backend\notebooks\meiosis_simulation.ipynb"
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find sys cell
sys_idx = -1
api_idx = -1
for i, c in enumerate(nb['cells']):
    if c['cell_type'] == 'code':
        s = "".join(c['source'])
        if 'import sys' in s:
            sys_idx = i
        elif 'apiResponse = requests.get' in s and 'risk/curve' in s:
            api_idx = i

if sys_idx != -1 and api_idx != -1 and api_idx < sys_idx:
    api_cell = nb['cells'].pop(api_idx)
    # the sys_idx has shifted by -1
    nb['cells'].insert(sys_idx, api_cell)

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Order fixed.")
