// API client buat connect ke backend fastapi
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// untuk ambil risk profile berdasarkan usia
export async function getRiskProfile(age) {
  const res = await fetch(`${BASE_URL}/api/risk/${age}`);
  if (!res.ok) throw new Error(`API Error ${res.status}: ${await res.text()}`);
  return res.json();
}

// untuk ambil data kurva risk
export async function getRiskCurve(ageMin = 15, ageMax = 50) {
  const res = await fetch(`${BASE_URL}/api/risk/curve?age_min=${ageMin}&age_max=${ageMax}`);
  if (!res.ok) throw new Error(`API Error ${res.status}`);
  return res.json();
}

// untuk membandingkan 2 usia
export async function compareAges(ageA, ageB) {
  const res = await fetch(`${BASE_URL}/api/risk/compare?age_a=${ageA}&age_b=${ageB}`);
  if (!res.ok) throw new Error(`API Error ${res.status}`);
  return res.json();
}

// untuk menjalankan simulasi Monte Carlo di backend
export async function runSimulation(params) {
  const res = await fetch(`${BASE_URL}/api/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      maternal_age:      params.maternal_age,
      n_simulations:     params.n_simulations,
      target_chromosome: params.target_chromosome,
      random_seed:       params.random_seed ?? null,
    }),
  });
  if (!res.ok) throw new Error(`Simulation API Error ${res.status}: ${await res.text()}`);
  return res.json();
}

// untuk menjalankan simulasi untuk semua range umur
export async function runAgeSweep(ageMin = 20, ageMax = 45, nSim = 500) {
  const res = await fetch(
    `${BASE_URL}/api/simulate/sweep?age_min=${ageMin}&age_max=${ageMax}&n_sim=${nSim}`
  );
  if (!res.ok) throw new Error(`Sweep API Error ${res.status}`);
  return res.json();
}