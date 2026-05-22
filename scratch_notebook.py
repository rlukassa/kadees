
# ---CELL---
import sys
import math
import random
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

sns.set_theme(style='darkgrid', palette='deep')
plt.rcParams['figure.dpi'] = 120
plt.rcParams['font.family'] = 'sans-serif'
pd.set_option('display.float_format', '{:.6f}'.format)

projectRoot = Path().resolve().parents[1]
sys.path.insert(0, str(projectRoot))

# ---CELL---
print(f'Kurva risiko siap dipakai: {len(riskDf)} baris, {riskDf.shape[1]} kolom')
riskDf.head(10)

# ---CELL---
apiResponse = requests.get('http://127.0.0.1:8000/api/data/syndromes', timeout=5)
apiResponse.raise_for_status()
syndromeDf = pd.DataFrame(apiResponse.json()['syndromes'])
print(f'   Data sindrom dimuat dari API backend: {len(syndromeDf)} baris')
syndromeDf

# ---CELL---
# ── Statistik deskriptif dataset risiko ──────────────────
riskDf[['maternalAge', 'totalRiskPercent', 'meiosisIRisk', 'meiosisIIRisk']].describe()

# ---CELL---
# ── Plot kurva risiko vs usia (Plotly interaktif) ─────────
fig = make_subplots(rows=1, cols=2,
    subplot_titles=('Risiko Total vs Usia Maternal (Skala Linier)',
                    'Risiko Total vs Usia Maternal (Skala Log)'))

for col, yaxisType in enumerate(['linear', 'log'], start=1):
    fig.add_trace(go.Scatter(
        x=riskDf['maternalAge'], y=riskDf['totalRiskPercent'],
        name='Risiko Total', mode='lines+markers',
        line=dict(color='#e74c3c', width=2),
        marker=dict(size=5)
    ), row=1, col=col)
    fig.update_yaxes(type=yaxisType, title_text='Risiko (%)', row=1, col=col)
    fig.update_xaxes(title_text='Usia Maternal (tahun)', row=1, col=col)

# Garis vertikal usia AMA (Advanced Maternal Age = 35)
for col in [1, 2]:
    fig.add_vline(x=35, line_dash='dash', line_color='orange',
                  annotation_text='AMA (35th)', row=1, col=col)

fig.update_layout(
    title='Kurva Risiko Aneuploidi Berdasarkan Usia Maternal',
    height=450, template='plotly_dark', showlegend=True
)
fig.show()

# ---CELL---
from backend.src.models.riskModel import MaternalAgeRiskModel
from backend.src.simulation.monte_carlo import MeiosisMonteCarloSimulator, SimulationConfig
from backend.src.models.gamete import GameteSex
import requests

apiResponse = requests.get('http://127.0.0.1:8000/api/risk/curve?ageMin=15&ageMax=50', timeout=5)
apiResponse.raise_for_status()
riskCurve = apiResponse.json()['curve']
riskDf = pd.DataFrame(riskCurve)
riskTable = {int(row['maternalAge']): float(row['totalRisk']) for row in riskCurve}
riskModel = MaternalAgeRiskModel(customTable=riskTable)
print(f'   Kurva risiko dimuat dari API backend: {len(riskDf)} titik data')

# ---CELL---
agesOfInterest = [20, 25, 30, 35, 38, 40, 42, 45]
riskProfiles = [riskModel.getRiskProfile(age).toDict() for age in agesOfInterest]
riskProfileDf = pd.DataFrame(riskProfiles)
riskProfileDf[['maternalAge', 'totalRiskPercent', 'meiosisIRisk',
               'meiosisIIRisk', 'riskCategory', 'riskRatioToBase']]

# ---CELL---
# ── Jalankan Simulasi Monte Carlo — Usia 35 tahun ─────────
# Konfigurasi: 10.000 iterasi, fokus kromosom 21 (Down syndrome)
config35 = SimulationConfig(
    maternalAge=35,
    nSimulations=10_000,
    targetChromosome=21,
    gameteSex=GameteSex.EGG,
    randomSeed=42
)
sim35 = MeiosisMonteCarloSimulator(config35, riskModel)
result35 = sim35.run()

print('=== Hasil Simulasi Monte Carlo — Usia 35 tahun ===')
print(f'  Total iterasi       : {result35.totalRuns:,}')
print(f'  Gamet aneuploid     : {result35.aneuploidCount:,}')
print(f'  Risiko observasi    : {result35.observedRisk*100:.4f}%')
print(f'  Risiko model        : {result35.modelRisk*100:.4f}%')
print(f'  ND Meiosis I        : {result35.ndMeiosisICount:,}')
print(f'  ND Meiosis II       : {result35.ndMeiosisIICount:,}')
print(f'  Waktu eksekusi      : {result35.executionTimeMs:.1f} ms')
print(f'\n  Distribusi Sindrom  :')
for syndrome, count in result35.syndromeCounts.items():
    print(f'    - {syndrome}: {count}')

# ---CELL---
# ── Age Sweep — Simulasi untuk usia 20–45 tahun ───────────
# Setiap usia disimulasikan 1.000 iterasi untuk mendapatkan tren risiko
print('Menjalankan age sweep simulasi (20–45 tahun)...')
configSweep = SimulationConfig(nSimulations=1000, maternalAge=20, randomSeed=0)
simulatorSweep = MeiosisMonteCarloSimulator(configSweep, riskModel)
sweepData = simulatorSweep.runAgeSweep(ageRange=(20, 45))

sweepDf = pd.DataFrame(sweepData)
print(f'Selesai. {len(sweepDf)} titik data.')
sweepDf.head()

# ---CELL---
# ── Grafik Perbandingan: Risiko Observasi vs Model Teoritis ─
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=sweepDf['age'], y=sweepDf['observedRisk'] * 100,
    name='Risiko Observasi (Monte Carlo)',
    mode='markers+lines', line=dict(color='#e74c3c', dash='dot'),
    marker=dict(size=6)
))
fig.add_trace(go.Scatter(
    x=sweepDf['age'], y=sweepDf['modelRisk'] * 100,
    name='Risiko Teoritis (Model Probabilistik)',
    mode='lines', line=dict(color='#2ecc71', width=2.5)
))
fig.add_vline(x=35, line_dash='dash', line_color='orange', annotation_text='AMA Threshold (35)')
fig.update_layout(
    title='Validasi: Risiko Observasi Monte Carlo vs Model Teoritis',
    xaxis_title='Usia Maternal (tahun)', yaxis_title='Probabilitas Aneuploidi (%)',
    template='plotly_dark', height=420
)
fig.show()

# ---CELL---
# ── Grafik Perbandingan: Risiko Observasi vs Model Teoritis ─
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=sweepDf['age'], y=sweepDf['observedRisk'] * 100,
    name='Risiko Observasi (Monte Carlo)',
    mode='markers+lines', line=dict(color='#e74c3c', dash='dot'),
    marker=dict(size=6)
))
fig.add_trace(go.Scatter(
    x=sweepDf['age'], y=sweepDf['modelRisk'] * 100,
    name='Risiko Teoritis (Model Probabilistik)',
    mode='lines', line=dict(color='#2ecc71', width=2.5)
))
fig.add_vline(x=35, line_dash='dash', line_color='orange', annotation_text='AMA Threshold (35)')
fig.update_layout(
    title='Validasi: Risiko Observasi Monte Carlo vs Model Teoritis',
    xaxis_title='Usia Maternal (tahun)', yaxis_title='Probabilitas Aneuploidi (%)',
    template='plotly_dark', height=420
)
fig.show()

# ---CELL---
# ── Distribusi Sindrom dari hasil simulasi ────────────────
if result35.syndromeCounts:
    syndromeDf = pd.DataFrame([
        {'sindrom': k, 'jumlah': v}
        for k, v in result35.syndromeCounts.items()
    ]).sort_values('jumlah', ascending=False)

    figSyn = px.bar(
        syndromeDf, x='sindrom', y='jumlah',
        title=f'Distribusi Prediksi Sindrom (Usia 35, n={result35.totalRuns:,})',
        color='jumlah', color_continuous_scale='Reds',
        template='plotly_dark'
    )
    figSyn.show()
else:
    print('Tidak ada gamet aneuploid yang terdeteksi pada simulasi ini.')

# ---CELL---
# ── Analisis Statistik: Wilson Confidence Interval ────────
from backend.src.simulation.statistics import SimulationStatisticsAnalyzer

statisticsAnalyzer = SimulationStatisticsAnalyzer([])
ci = statisticsAnalyzer.wilsonConfidenceInterval(
    successes=result35.aneuploidCount,
    n=result35.totalRuns,
    confidence=0.95
)
print('=== 95% Wilson Score Confidence Interval ===')
print(f'  Proporsi observasi : {ci.center*100:.4f}%')
print(f'  CI Lower           : {ci.lower*100:.4f}%')
print(f'  CI Upper           : {ci.upper*100:.4f}%')
print(f'  Margin of Error    : ±{ci.toDict()["marginOfError"]*100:.4f}%')

# ── Perbandingan observasi vs model ────────────────────────
comparison = statisticsAnalyzer.compareObservedVsModel(
    observed=result35.observedRisk,
    model=result35.modelRisk,
    n=result35.totalRuns
)
print('\n=== Validasi Model ===')
for key, value in comparison.items():
    print(f'  {key}: {value}')

# ---CELL---
# ── Relative Risk: Usia 35 vs 25 ─────────────────────────
relativeRisk = statisticsAnalyzer.relativeRisk(
    risk_exposed=result35.modelRisk,
    risk_baseline=riskModel.getRiskProfile(25).totalRisk
)
print(f'Relative Risk (usia 35 vs 25): {relativeRisk:.2f}x')
print(f'→ Wanita usia 35 memiliki risiko {relativeRisk:.1f}x lebih tinggi dari usia 25')

# ---CELL---
# ── Heatmap: Meiosis I vs II per usia ─────────────────────
# Jalankan beberapa usia dan plot proporsi ND per tahap
agesOfInterest = [25, 30, 35, 38, 40, 42, 45]
ndData = []
for age in agesOfInterest:
    config = SimulationConfig(maternalAge=age, nSimulations=3000, randomSeed=42)
    simulationResult = MeiosisMonteCarloSimulator(config, riskModel).run()
    totalNd = simulationResult.ndMeiosisICount + simulationResult.ndMeiosisIICount
    ndData.append({
        'Usia': age,
        'Meiosis I (%)': simulationResult.ndMeiosisICount / totalNd * 100 if totalNd > 0 else 0,
        'Meiosis II (%)': simulationResult.ndMeiosisIICount / totalNd * 100 if totalNd > 0 else 0,
    })

dfNd = pd.DataFrame(ndData).set_index('Usia')
plt.figure(figsize=(9, 4))
sns.heatmap(dfNd.T, annot=True, fmt='.1f', cmap='RdYlGn_r', linewidths=0.5, vmin=0, vmax=100)
plt.title('Distribusi Non-Disjunction: Meiosis I vs Meiosis II (% dari total ND)')
plt.tight_layout()
plt.show()

# ---CELL---
# ── Cetak detail gamet aneuploid sampel ──────────────────
# Data ini akan dikirim ke Three.js untuk visualisasi 3D
print(f'Total sampel gamet aneuploid: {len(result35.sampleGametes)}')
for index, gamete in enumerate(result35.sampleGametes, 1):
    gameteData = gamete.toDict()
    print(f'\n  [{index}] Gamet ID   : {gameteData["gameteId"]}')
    print(f'      Jumlah Chr  : {gameteData["chromosomeCount"]}')
    print(f'      Sindrom     : {gameteData["predictedSyndrome"]}')
    print(f'      Chr terdampak: {[c["label"] for c in gameteData["affectedChromosomes"]]}')
