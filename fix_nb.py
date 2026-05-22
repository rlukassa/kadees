import json

notebook_path = r"C:\Users\MSI\Desktop\kds\kadees\backend\notebooks\meiosis_simulation.ipynb"
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

for c in nb['cells']:
    if c['cell_type'] == 'code':
        source = "".join(c['source'])
        source = source.replace("risk_exposed", "riskExposed")
        source = source.replace("risk_baseline", "riskBaseline")
        source = source.replace("backend.src.models.riskModel", "backend.src.models.risk_model")
        
        lines = source.split('\n')
        # restore exact lines structure (except last empty split if any)
        if len(lines) > 0 and lines[-1] == "":
            lines = lines[:-1]
            c['source'] = [line + '\n' for line in lines[:-1]] + [lines[-1] + '\n'] if len(lines)>1 else [lines[0]+'\n']
        else:
            c['source'] = [line + '\n' for line in lines[:-1]] + [lines[-1]] if len(lines)>1 else [lines[0]]
            
        # simpler way to reconstruct:
        # splitlines(True) keeps the \n
        c['source'] = [s for s in source.splitlines(True)]

api_cell_idx = None
for i, c in enumerate(nb['cells']):
    if c['cell_type'] == 'code' and 'risk/curve' in "".join(c['source']):
        api_cell_idx = i
        break

if api_cell_idx is not None and api_cell_idx > 2:
    api_cell = nb['cells'].pop(api_cell_idx)
    nb['cells'].insert(2, api_cell)
    
with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook fixed.")
