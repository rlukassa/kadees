/**
 * api.js — API Client untuk FastAPI Backend (camelCase edition)
 * =============================================================
 * Wrapper fungsi fetch ke semua endpoint backend.
 * Semua request body dan query params menggunakan camelCase
 * agar sinkron dengan backend v2.0 (BACKEND.md).
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * getRiskProfile(age)
 * // Mengambil profil risiko untuk satu usia maternal dari API.
 * // param age: integer usia maternal (15–50).
 * // output: Promise<RiskProfile dict> — keys: maternalAge, totalRisk, totalRiskPercent,
 * //         meiosisIRisk, meiosisIIRisk, riskCategory, riskRatioToBase
 * // dipakai untuk: mengisi panel risk indicator saat slider digeser.
 */
export async function getRiskProfile(age) {
  const res = await fetch(`${BASE_URL}/api/risk/${age}`);
  if (!res.ok) throw new Error(`API Error ${res.status}: ${await res.text()}`);
  return res.json();
}

/**
 * getRiskCurve(ageMin, ageMax)
 * // Mengambil data kurva risiko untuk rentang usia.
 * // param ageMin: integer usia minimum.
 * // param ageMax: integer usia maksimum.
 * // output: Promise<{ curve: Array<RiskProfile>, totalPoints: number }>.
 * // dipakai untuk: rendering grafik kurva risiko di panel kanan.
 */
export async function getRiskCurve(ageMin = 15, ageMax = 50) {
  const res = await fetch(`${BASE_URL}/api/risk/curve?ageMin=${ageMin}&ageMax=${ageMax}`);
  if (!res.ok) throw new Error(`API Error ${res.status}`);
  return res.json();
}

/**
 * compareAges(ageA, ageB)
 * // Membandingkan profil risiko dua usia maternal.
 * // param ageA: usia pertama. param ageB: usia kedua.
 * // output: Promise<{ ageA, ageB, riskRatioAToB, interpretation }>.
 */
export async function compareAges(ageA, ageB) {
  const res = await fetch(`${BASE_URL}/api/risk/compare?ageA=${ageA}&ageB=${ageB}`);
  if (!res.ok) throw new Error(`API Error ${res.status}`);
  return res.json();
}

/**
 * runSimulation(params)
 * // Menjalankan simulasi Monte Carlo di backend.
 * // param params: { maternalAge, nSimulations, targetChromosome, randomSeed? }
 * // output: Promise<SimulationResult> — results.aneuploidCount, results.observedRiskPercent,
 * //         results.ndMeiosisICount, results.ndMeiosisIICount, results.syndromeCounts,
 * //         results.wilsonCI, results.modelValidation, sampleGametes[]
 * // dipakai untuk: tombol "Jalankan Simulasi", mengambil data untuk Three.js.
 */
export async function runSimulation(params) {
  const res = await fetch(`${BASE_URL}/api/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      maternalAge:      params.maternalAge,
      nSimulations:     params.nSimulations,
      targetChromosome: params.targetChromosome,
      randomSeed:       params.randomSeed ?? null,
    }),
  });
  if (!res.ok) throw new Error(`Simulation API Error ${res.status}: ${await res.text()}`);
  return res.json();
}

/**
 * runAgeSweep(ageMin, ageMax, nSim)
 * // Menjalankan simulasi untuk semua usia dalam rentang (age sweep).
 * // param ageMin: integer usia awal.
 * // param ageMax: integer usia akhir.
 * // param nSim: integer jumlah iterasi per usia.
 * // output: Promise<{ sweep: Array<{age, observedRisk, modelRisk, aneuploidCount}>,
 * //                   totalAges: number }>.
 * // dipakai untuk: grafik perbandingan tren risiko vs usia.
 */
export async function runAgeSweep(ageMin = 20, ageMax = 45, nSim = 500) {
  const res = await fetch(
    `${BASE_URL}/api/simulate/sweep?ageMin=${ageMin}&ageMax=${ageMax}&nSim=${nSim}`
  );
  if (!res.ok) throw new Error(`Sweep API Error ${res.status}`);
  return res.json();
}

/**
 * analyzeAge(age, nSim, baseline, confidence)
 * // Analisis statistik mendalam: Wilson CI + Relative Risk untuk satu usia.
 * // param age: usia yang dianalisis. param nSim: jumlah iterasi.
 * // param baseline: usia baseline untuk RR (default 25).
 * // param confidence: level CI (0.90/0.95/0.99, default 0.95).
 * // output: Promise<{ wilsonCI, relativeRisk, modelValidation, ... }>.
 */
export async function analyzeAge(age, nSim = 5000, baseline = 25, confidence = 0.95) {
  const res = await fetch(
    `${BASE_URL}/api/stats/analyze?age=${age}&nSim=${nSim}&baseline=${baseline}&confidence=${confidence}`
  );
  if (!res.ok) throw new Error(`Stats API Error ${res.status}`);
  return res.json();
}

/**
 * getDatasetStats()
 * // Mengambil ringkasan statistik dataset maternal_age_risk.csv.
 * // output: Promise<{ totalRecords, aneuploidCount, aneuploidRate, maternalAgeStats }>.
 */
export async function getDatasetStats() {
  const res = await fetch(`${BASE_URL}/api/data/stats`);
  if (!res.ok) throw new Error(`API Error ${res.status}`);
  return res.json();
}

/**
 * getSyndromes()
 * // Mengambil tabel referensi sindrom kromosom (37 baris dari OMIM/ACMG).
 * // output: Promise<{ count, syndromes: Array<SyndromeRef> }>.
 */
export async function getSyndromes() {
  const res = await fetch(`${BASE_URL}/api/data/syndromes`);
  if (!res.ok) throw new Error(`API Error ${res.status}`);
  return res.json();
}
