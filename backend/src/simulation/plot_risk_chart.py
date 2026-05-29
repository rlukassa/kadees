"""
Script untuk generate Grafik Risiko Aneuploidi vs Usia Maternal
================================================================
Output: File gambar PNG untuk dilampirkan di laporan

Usage:
    python backend/src/simulation/plot_risk_chart.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from backend.src.models.risk_model import MATERNAL_AGE_RISK_TABLE, MaternalAgeRiskModel


def plot_full_risk_curve(save_path: Path = None):
    """Plot kurva risiko penuh (usia 15-49)"""
    risk_model = MaternalAgeRiskModel()

    ages = list(range(15, 50))
    risks = [risk_model.interpolateRisk(age) * 100 for age in ages]

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot line utama
    ax.plot(ages, risks, 'b-', linewidth=2, label='Risiko Model')

    # Fill area
    ax.fill_between(ages, risks, alpha=0.3, color='blue')

    # Marker untuk usia penting
    critical_ages = [35, 40, 45, 49]
    for age in critical_ages:
        risk_val = risk_model.interpolateRisk(age) * 100
        ax.scatter([age], [risk_val], color='red', s=80, zorder=5)
        ax.annotate(f'{risk_val:.2f}%', (age, risk_val),
                   textcoords="offset points", xytext=(0, 10),
                   ha='center', fontsize=9, fontweight='bold')

    # Garis AMA threshold
    ax.axvline(x=35, color='red', linestyle='--', alpha=0.7, label='AMA Threshold (35 tahun)')

    # Annotations
    ax.annotate('Fase Kritis', xy=(42, 5), fontsize=12, fontweight='bold', color='red')
    ax.annotate('Peningkatan Eksponensial', xy=(40, 10), fontsize=10, style='italic')

    ax.set_xlabel('Usia Maternal (tahun)', fontsize=12)
    ax.set_ylabel('Risiko Aneuploidi (%)', fontsize=12)
    ax.set_title('Kurva Risiko Aneuploidi Berdasarkan Usia Maternal\n(Data: Hook 1981)', fontsize=14, fontweight='bold')
    ax.set_xlim(15, 49)
    ax.set_ylim(0, 16)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left')

    # Text box
    textstr = f'Total usia: 15-49\nJumlah titik data: {len(ages)}'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.98, 0.45, textstr, transform=ax.transAxes, fontsize=9,
           verticalalignment='top', horizontalalignment='right', bbox=props)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[Grafik disimpan ke: {save_path}]")

    plt.show()
    return fig


def plot_zoomed_critical_phase(save_path: Path = None):
    """Plot zoomed view pada fase kritis (usia 35-49)"""
    risk_model = MaternalAgeRiskModel()

    ages = list(range(35, 50))
    risks = [risk_model.interpolateRisk(age) * 100 for age in ages]

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot line
    ax.plot(ages, risks, 'b-', linewidth=2.5, marker='o', markersize=8, label='Risiko Model')

    # Fill area
    ax.fill_between(ages, risks, alpha=0.2, color='blue')

    # Annotations untuk setiap titik
    for i, (age, risk) in enumerate(zip(ages, risks)):
        offset = 10 if i % 2 == 0 else -15
        ax.annotate(f'{risk:.2f}%', (age, risk),
                   textcoords="offset points", xytext=(0, offset),
                   ha='center', fontsize=9, fontweight='bold')

    # Trend line (exponential fit)
    import numpy as np
    z = np.polyfit(ages, risks, 2)  # quadratic fit as approximation
    p = np.poly1d(z)
    x_smooth = np.linspace(35, 49, 100)
    ax.plot(x_smooth, p(x_smooth), 'r--', alpha=0.5, linewidth=1.5, label='Trend (quadratic fit)')

    # Highlight area
    ax.axvspan(35, 49, alpha=0.1, color='red', label='Fase Kritis')

    ax.set_xlabel('Usia Maternal (tahun)', fontsize=12)
    ax.set_ylabel('Risiko Aneuploidi (%)', fontsize=12)
    ax.set_title('ZOOMED: Fase Kritis (Usia 35-49)\nPola Peningkatan Eksponensial', fontsize=14, fontweight='bold')
    ax.set_xlim(34, 50)
    ax.set_ylim(0, 16)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left')

    # Stats box
    min_risk = min(risks)
    max_risk = max(risks)
    ratio = max_risk / min_risk

    stats_text = (
        f'Stats Fase Kritis:\n'
        f'Min: {min_risk:.2f}% (age 35)\n'
        f'Max: {max_risk:.2f}% (age 49)\n'
        f'Ratio: {ratio:.1f}x'
    )
    props = dict(boxstyle='round', facecolor='lightcoral', alpha=0.5)
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', bbox=props)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[Grafik disimpan ke: {save_path}]")

    plt.show()
    return fig


def plot_comparison_model_vs_observed(save_path: Path = None):
    """Plot perbandingan Model vs Observasi Simulasi"""
    risk_model = MaternalAgeRiskModel()

    # Data dari validation.py output
    test_data = [
        (25, 0.21, 0.11),
        (30, 0.26, 0.16),
        (35, 0.56, 0.54),
        (40, 1.58, 1.64),
        (45, 5.37, 5.61),
    ]

    ages = [d[0] for d in test_data]
    model_risks = [d[1] for d in test_data]
    observed_risks = [d[2] for d in test_data]

    x = range(len(ages))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    bars1 = ax.bar([i - width/2 for i in x], model_risks, width, label='Model Risk (%)', color='steelblue')
    bars2 = ax.bar([i + width/2 for i in x], observed_risks, width, label='Observed Risk (%)', color='darkorange')

    ax.set_xlabel('Usia Maternal (tahun)', fontsize=12)
    ax.set_ylabel('Risiko (%)', fontsize=12)
    ax.set_title('Perbandingan Model vs Observasi Simulasi\n(n=10,000 iterasi per usia)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(ages)
    ax.legend()
    ax.grid(True, axis='y', alpha=0.3)

    # Annotations
    for i, (age, m, o) in enumerate(test_data):
        ax.annotate(f'{m:.2f}%', (i - width/2, m + 0.1), ha='center', fontsize=8)
        ax.annotate(f'{o:.2f}%', (i + width/2, o + 0.1), ha='center', fontsize=8)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"[Grafik disimpan ke: {save_path}]")

    plt.show()
    return fig


if __name__ == "__main__":
    import os

    # Buat folder output
    output_dir = Path(__file__).parent.parent.parent.parent / "output_charts"
    output_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("GENERATE GRAFIK RISIKO ANEUPLOIDI")
    print("=" * 60)

    # 1. Full risk curve
    print("\n[1] Generate: Full Risk Curve (Usia 15-49)")
    plot_full_risk_curve(output_dir / "risk_curve_full.png")

    # 2. Zoomed critical phase
    print("\n[2] Generate: Zoomed Critical Phase (Usia 35-49)")
    plot_zoomed_critical_phase(output_dir / "risk_curve_zoomed_35_49.png")

    # 3. Comparison chart
    print("\n[3] Generate: Model vs Observed Comparison")
    plot_comparison_model_vs_observed(output_dir / "model_vs_observed.png")

    print("\n" + "=" * 60)
    print(f"Semua grafik disimpan di: {output_dir}")
    print("=" * 60)