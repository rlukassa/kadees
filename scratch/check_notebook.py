import json
import re

notebook_path = r"c:\Users\MSI\Desktop\kds\kadees\backend\notebooks\meiosis_simulation.ipynb"
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

snake_cases = [
    "is_aneuploid",
    "to_dict",
    "predict_syndrome",
    "get_aneuploidy_type",
    "get_affected_chromosomes",
    "interpolate_risk",
    "classify_risk",
    "get_risk_profile",
    "get_risk_curve",
    "compare_ages",
    "snake_to_camel",
    "camelize_dict",
    "load_maternal_age_risk",
    "load_syndrome_reference",
    "load_maternal_age_rows",
    "wilson_confidence_interval",
    "relative_risk",
    "descriptive_stats",
    "compare_observed_vs_model",
    "run_age_sweep"
]

found = {}
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        for sc in snake_cases:
            if sc in source:
                if sc not in found:
                    found[sc] = []
                found[sc].append(i)

print("Found snake_case method/function occurrences:")
for sc, cell_idxs in found.items():
    print(f"- {sc}: cells {cell_idxs}")
