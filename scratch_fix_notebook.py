import json
import re

notebook_path = r"C:\Users\MSI\Desktop\kds\kadees\backend\notebooks\meiosis_simulation.ipynb"

with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

replacements = {
    r'\bto_dict\b': 'toDict',
    r'\brun_age_sweep\b': 'runAgeSweep',
    r'\bget_risk_profile\b': 'getRiskProfile',
    r'\bget_risk_curve\b': 'getRiskCurve',
    r'\bcompare_ages\b': 'compareAges',
    r'\bclassify_risk\b': 'classifyRisk',
    r'\binterpolate_risk\b': 'interpolateRisk',
    r'\bis_aneuploid\b': 'isAneuploid',
    r'\bpredict_syndrome\b': 'predictSyndrome',
    r'\bget_aneuploidy_type\b': 'getAneuploidyType',
    r'\bget_affected_chromosomes\b': 'getAffectedChromosomes',
    r'\bmark_nondisjunction\b': 'markNondisjunction',
    r'\bis_sex_chromosome\b': 'isSexChromosome',
    r'\bwilson_confidence_interval\b': 'wilsonConfidenceInterval',
    r'\brelative_risk\b': 'relativeRisk',
    r'\bdescriptive_stats\b': 'descriptiveStats',
    r'\bcompare_observed_vs_model\b': 'compareObservedVsModel',
    r'\bload_maternal_age_risk\b': 'loadMaternalAgeRisk',
    r'\bload_syndrome_reference\b': 'loadSyndromeReference',
    r'\bload_maternal_age_rows\b': 'loadMaternalAgeRows',
    r'\bcamelize_dict\b': 'camelizeDict',
    r'\bsnake_to_camel\b': 'snakeToCamel',
    r'\brisk_model\b': 'riskModel',
    r'\bmaternal_age\b': 'maternalAge',
    r'\bn_simulations\b': 'nSimulations',
    r'\btarget_chromosome\b': 'targetChromosome',
    r'\bgamete_sex\b': 'gameteSex',
    r'\brandom_seed\b': 'randomSeed',
    r'\baneuploid_count\b': 'aneuploidCount',
    r'\bnormal_count\b': 'normalCount',
    r'\btotal_runs\b': 'totalRuns',
    r'\bobserved_risk\b': 'observedRisk',
    r'\bmodel_risk\b': 'modelRisk',
    r'\bsyndrome_counts\b': 'syndromeCounts',
}

for cell in nb.get('cells', []):
    if cell.get('cell_type') in ('code', 'markdown'):
        new_source = []
        for line in cell.get('source', []):
            new_line = line
            for old, new in replacements.items():
                new_line = re.sub(old, new, new_line)
            new_source.append(new_line)
        cell['source'] = new_source

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)

print("Notebook modified successfully.")
