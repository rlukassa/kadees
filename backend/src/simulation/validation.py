"""
Validation Script untuk Model Simulasi Monte Carlo Non-Disjunction
=================================================================
Script ini menghitung metric akurasi model terhadap data empiris Hook (1981)

Sumber data:
- Hook EB (1981). Tabel empiris kelainan kromosom berdasarkan usia maternal
- Morris JK et al. (2002). Revised estimates of maternal age specific live birth
  prevalence of Down's syndrome
- ACMG (2016). Noninvasive prenatal screening for fetal aneuploidy

Usage:
    python -m backend.src.simulation.validation
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from backend.src.models.risk_model import MATERNAL_AGE_RISK_TABLE, MaternalAgeRiskModel
from backend.src.simulation.monte_carlo import SimulationConfig, MeiosisMonteCarloSimulator


def calculate_correlation_metrics(ages: list, model_values: list, observed_values: list) -> dict:
    """
    Hitung metrik korelasi dan error antara nilai model dan observasi.

    Args:
        ages: List usia maternal
        model_values: List nilai risiko dari model
        observed_values: List nilai risiko dari data observasi

    Returns:
        Dict containing Pearson correlation, RMSE, MAE, dll.
    """
    import math

    n = len(ages)

    # Calculate means
    model_mean = sum(model_values) / n
    observed_mean = sum(observed_values) / n

    # Pearson Correlation Coefficient
    numerator = sum((m - model_mean) * (o - observed_mean) for m, o in zip(model_values, observed_values))

    model_var = sum((m - model_mean) ** 2 for m in model_values)
    obs_var = sum((o - observed_mean) ** 2 for o in observed_values)

    denominator = math.sqrt(model_var * obs_var)

    correlation = numerator / denominator if denominator != 0 else 0

    # Coefficient of Determination (R-squared)
    ss_res = sum((o - m) ** 2 for o, m in zip(observed_values, model_values))
    ss_tot = sum((o - observed_mean) ** 2 for o in observed_values)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0

    # RMSE (Root Mean Square Error)
    mse = ss_res / n
    rmse = math.sqrt(mse)

    # MAE (Mean Absolute Error)
    mae = sum(abs(o - m) for o, m in zip(observed_values, model_values)) / n

    # MAPE (Mean Absolute Percentage Error)
    # Only for non-zero observed values
    non_zero_pairs = [(o, m) for o, m in zip(observed_values, model_values) if o != 0]
    if non_zero_pairs:
        mape = sum(abs(o - m) / o for o, m in non_zero_pairs) / len(non_zero_pairs) * 100
    else:
        mape = 0

    return {
        "n_samples": n,
        "pearson_correlation": round(correlation, 6),
        "p_value": None,  # Would need scipy for p-value
        "r_squared": round(r_squared, 6),
        "rmse": round(rmse, 6),
        "rmse_percent": round(rmse * 100, 4),
        "mae": round(mae, 6),
        "mape_percent": round(mape, 4),
    }


def validate_against_hook_table():
    """
    Validasi model risk terhadap tabel Hook (1981).
    Karena model menggunakan data Hook sebagai ground truth,
    korelasi expected = 1.0 (atau sangat dekat).
    """
    print("=" * 70)
    print("VALIDASI MODEL TERHADAP TABEL HOOK (1981)")
    print("=" * 70)

    risk_model = MaternalAgeRiskModel()

    # Ambil semua usia dari tabel Hook
    ages = sorted(MATERNAL_AGE_RISK_TABLE.keys())

    model_risks = []
    hook_risks = []

    print(f"\n{'Usia':<6} {'Model Risk (%)':<16} {'Hook Risk (%)':<16} {'Deviasi (%)':<12}")
    print("-" * 50)

    for age in ages:
        model_risk = risk_model.interpolateRisk(age)
        hook_risk = MATERNAL_AGE_RISK_TABLE[age]

        model_risks.append(model_risk)
        hook_risks.append(hook_risk)

        deviation = (model_risk - hook_risk) * 100

        # Highlight usia penting
        marker = ""
        if age in [35, 40, 45, 49]:
            marker = " <-- AMA"

        print(f"{age:<6} {model_risk*100:>12.4f}%     {hook_risk*100:>12.4f}%     {deviation:>+10.4f}%{marker}")

    # Calculate metrics
    metrics = calculate_correlation_metrics(ages, model_risks, hook_risks)

    print("\n" + "-" * 50)
    print("METRIK VALIDASI:")
    print("-" * 50)
    print(f"  Pearson Correlation:  {metrics['pearson_correlation']:.6f}")
    print(f"  R-squared:            {metrics['r_squared']:.6f}")
    print(f"  RMSE:                 {metrics['rmse']:.6f} ({metrics['rmse_percent']:.4f}%)")
    print(f"  MAE:                  {metrics['mae']:.6f}")
    print(f"  MAPE:                 {metrics['mape_percent']:.4f}%")

    return metrics


def validate_simulation_convergence(n_simulations: int = 10000, test_ages: list = None):
    """
    Validasi apakah simulasi Monte Carlo konvergen ke nilai model teoritis.

    Args:
        n_simulations: Jumlah iterasi per simulasi
        test_ages: List usia yang akan diuji
    """
    if test_ages is None:
        test_ages = [25, 30, 35, 40, 45]

    print("\n" + "=" * 70)
    print(f"VALIDASI KONVERGENSI SIMULASI (n={n_simulations:,} iterasi)")
    print("=" * 70)

    results_summary = []

    print(f"\n{'Usia':<6} {'Model (%)':<12} {'Observed (%)':<14} {'Deviasi (%)':<12} {'CI 95%':<20}")
    print("-" * 70)

    for age in test_ages:
        # Run simulation
        config = SimulationConfig(
            maternalAge=age,
            nSimulations=n_simulations,
            randomSeed=42,  # Fixed seed for reproducibility
        )

        simulator = MeiosisMonteCarloSimulator(config)
        result = simulator.run()

        observed = result.observedRisk * 100
        model = result.modelRisk * 100
        deviation = observed - model

        # Wilson CI
        wilson_ci = result.toDict()["results"]["wilson_ci"]
        ci_str = f"[{wilson_ci['lower']*100:.3f}%, {wilson_ci['upper']*100:.3f}%]"

        marker = ""
        if age == 35:
            marker = " <-- AMA"

        print(f"{age:<6} {model:>10.4f}%   {observed:>10.4f}%     {deviation:>+10.4f}%   {ci_str}{marker}")

        results_summary.append({
            "age": age,
            "model_risk": model,
            "observed_risk": observed,
            "deviation": deviation,
            "within_ci": wilson_ci["lower"] <= result.modelRisk <= wilson_ci["upper"],
        })

    print("\n" + "-" * 70)
    print("SUMMARY:")
    all_within = all(r["within_ci"] for r in results_summary)
    avg_deviation = sum(abs(r["deviation"]) for r in results_summary) / len(results_summary)

    print(f"  All predictions within 95% CI: {'YES' if all_within else 'NO'}")
    print(f"  Average absolute deviation:   {avg_deviation:.4f}%")

    return results_summary


def generate_validation_report(output_path: Path = None):
    """
    Generate laporan validasi lengkap dan simpan ke file.
    """
    import json
    from datetime import datetime

    report = {
        "title": "Validasi Model Monte Carlo Non-Disjunction",
        "timestamp": datetime.now().isoformat(),
        "section_1": {},
        "section_2": {},
    }

    # Section 1: Hook Table Validation
    print("\n" + "=" * 70)
    print("SECTION 1: Validasi terhadap Tabel Hook (1981)")
    print("=" * 70)
    report["section_1"]["description"] = "Perbandingan model interpolasi dengan data empiris Hook"
    hook_metrics = validate_against_hook_table()
    report["section_1"]["metrics"] = hook_metrics

    # Section 2: Simulation Convergence
    print("\n" + "=" * 70)
    print("SECTION 2: Validasi Konvergensi Simulasi")
    print("=" * 70)
    report["section_2"]["description"] = "Verifikasi bahwa simulasi MC converge ke nilai teoritis"
    convergence_results = validate_simulation_convergence(n_simulations=10000)
    report["section_2"]["results"] = convergence_results

    # Calculate overall summary
    all_deviations = [r["deviation"] for r in convergence_results]
    report["summary"] = {
        "total_tests": len(convergence_results),
        "max_absolute_deviation": max(abs(d) for d in all_deviations),
        "average_absolute_deviation": sum(abs(d) for d in all_deviations) / len(all_deviations),
        "simulation_accuracy": "Acceptable" if max(abs(d) for d in all_deviations) < 0.5 else "Review Needed",
    }

    print("\n" + "=" * 70)
    print("OVERALL SUMMARY")
    print("=" * 70)
    print(f"  Total tests performed:      {report['summary']['total_tests']}")
    print(f"  Max absolute deviation:     {report['summary']['max_absolute_deviation']:.4f}%")
    print(f"  Average absolute deviation: {report['summary']['average_absolute_deviation']:.4f}%")
    print(f"  Simulation accuracy:        {report['summary']['simulation_accuracy']}")

    # Save to file
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[Laporan disimpan ke: {output_path}]")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validasi Model Monte Carlo Non-Disjunction")
    parser.add_argument("--output", "-o", type=str, help="Path untuk menyimpan laporan validasi (JSON)")
    parser.add_argument("--n-simulations", "-n", type=int, default=10000, help="Jumlah iterasi simulasi")

    args = parser.parse_args()

    output_path = Path(args.output) if args.output else None
    generate_validation_report(output_path)

    print("\n" + "=" * 70)
    print("VALIDASI SELESAI")
    print("=" * 70)