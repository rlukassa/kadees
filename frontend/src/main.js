/**
 * main.js — Application Entry Point (camelCase sync edition)
 * ===========================================================
 * Mengintegrasikan semua modul: API client, Three.js scene, Chart.js charts,
 * dan DOM event handlers. Semua response keys dari backend menggunakan camelCase.
 */

import { MeiosisScene } from './scenes/MeiosisScene.js';
import { getRiskProfile, getRiskCurve, runSimulation, runAgeSweep } from './utils/api.js';
import { createRiskCurveChart, createNdPieChart, drawRiskGauge } from './components/RiskChart.js';

// ─────────────────────────────────────────────
// DOM REFERENCES
// ─────────────────────────────────────────────
const ageSlider      = document.getElementById('age-slider');
const ageDisplay     = document.getElementById('age-display');
const nSimSelect     = document.getElementById('n-sim-select');
const chrSelect      = document.getElementById('chr-select');
const btnRun         = document.getElementById('btn-run');
const btnSweep       = document.getElementById('btn-sweep');
const loadingOverlay = document.getElementById('loading-overlay');
const loadingText    = document.getElementById('loading-text');
const toast          = document.getElementById('toast');
const canvasOverlay  = document.getElementById('canvas-overlay');
const sectionResults = document.getElementById('section-results');
const syndromeBox    = document.getElementById('syndrome-box');

// Result stat elements — semua key mengikuti camelCase response backend
const resAneuploid = document.getElementById('res-aneuploid');
const resObserved  = document.getElementById('res-observed');
const resNdMI      = document.getElementById('res-nd-mi');
const resNdMII     = document.getElementById('res-nd-mii');

// Risk stat elements
const statTotalRisk = document.getElementById('stat-total-risk');
const statMiRisk    = document.getElementById('stat-mi-risk');
const statMiiRisk   = document.getElementById('stat-mii-risk');
const statCategory  = document.getElementById('stat-category');
const statRatio     = document.getElementById('stat-ratio');

// Stage bar chips
const stageChips = {
  interphase: document.getElementById('chip-interphase'),
  prophase:   document.getElementById('chip-prophase'),
  metaphase:  document.getElementById('chip-metaphase'),
  anaphase:   document.getElementById('chip-anaphase'),
  meiosis2:   document.getElementById('chip-meiosis2'),
  gametes:    document.getElementById('chip-gametes'),
};

// ─────────────────────────────────────────────
// INIT THREE.JS SCENE
// ─────────────────────────────────────────────
const scene = new MeiosisScene(document.getElementById('three-canvas'));

scene.onStageChange((stageName) => {
  Object.values(stageChips).forEach(c => c.classList.remove('active', 'error'));
  const chip = stageChips[stageName];
  if (chip) chip.classList.add('active');
});

// ─────────────────────────────────────────────
// INIT: Load risk curve & risk profile default
// ─────────────────────────────────────────────
let riskCurveData = [];

async function initApp() {
  try {
    const curveRes = await getRiskCurve(15, 50);
    riskCurveData = curveRes.curve;
    createRiskCurveChart('risk-chart', riskCurveData, 30);
    await updateRiskProfile(30);
  } catch (err) {
    showToast('Backend tidak terhubung. Pastikan server FastAPI berjalan.', 'error');
  }
}

// ─────────────────────────────────────────────
// RISK PROFILE UPDATE — baca field camelCase dari response
// ─────────────────────────────────────────────
async function updateRiskProfile(age) {
  try {
    const profile = await getRiskProfile(age);

    // Backend mengembalikan camelCase: totalRiskPercent, meiosisIRisk, meiosisIIRisk, dll.
    statTotalRisk.textContent = `${profile.totalRiskPercent.toFixed(4)}%`;
    statMiRisk.textContent    = `${(profile.meiosisIRisk * 100).toFixed(4)}%`;
    statMiiRisk.textContent   = `${(profile.meiosisIIRisk * 100).toFixed(4)}%`;
    statRatio.textContent     = `${profile.riskRatioToBase.toFixed(1)}x`;

    // Update badge kategori
    const catMap = {
      'rendah': 'rendah', 'sedang': 'sedang',
      'tinggi': 'tinggi', 'sangat tinggi': 'sangat-tinggi'
    };
    const catClass = catMap[profile.riskCategory] || 'rendah';
    statCategory.textContent = profile.riskCategory.toUpperCase();
    statCategory.className = `stat-value risk-badge ${catClass}`;

    // Update gauge
    drawRiskGauge('risk-gauge', profile.totalRiskPercent, 60);

    // Update garis pada chart
    if (riskCurveData.length) {
      createRiskCurveChart('risk-chart', riskCurveData, age);
    }
  } catch (err) {
    // Silently fail — backend mungkin belum jalan
  }
}

// ─────────────────────────────────────────────
// EVENT: Slider Usia
// ─────────────────────────────────────────────
let sliderDebounce;
ageSlider.addEventListener('input', () => {
  const age = parseInt(ageSlider.value);
  ageDisplay.textContent = `${age} tahun`;
  clearTimeout(sliderDebounce);
  sliderDebounce = setTimeout(() => updateRiskProfile(age), 300);
});

// ─────────────────────────────────────────────
// EVENT: Tombol Jalankan Simulasi
// ─────────────────────────────────────────────
btnRun.addEventListener('click', async () => {
  const age    = parseInt(ageSlider.value);
  const nSim   = parseInt(nSimSelect.value);
  const chrNum = parseInt(chrSelect.value);

  setLoading(true, `Menjalankan ${nSim.toLocaleString()} iterasi Monte Carlo…`);
  btnRun.disabled = true;

  try {
    const data = await runSimulation({
      maternalAge:      age,        // camelCase — sinkron dengan backend v2.0
      nSimulations:     nSim,
      targetChromosome: chrNum,
    });

    // Response backend sudah camelCase: aneuploidCount, observedRiskPercent, dll.
    const r = data.results;
    resAneuploid.textContent = r.aneuploidCount.toLocaleString();
    resObserved.textContent  = `${r.observedRiskPercent.toFixed(4)}%`;
    resNdMI.textContent      = r.ndMeiosisICount.toLocaleString();
    resNdMII.textContent     = r.ndMeiosisIICount.toLocaleString();

    // Tampilkan sindrom
    if (Object.keys(r.syndromeCounts).length > 0) {
      const synHtml = Object.entries(r.syndromeCounts)
        .sort((a, b) => b[1] - a[1])
        .map(([syn, cnt]) => `<div>🔴 <strong>${syn}</strong>: ${cnt} gamet</div>`)
        .join('');
      syndromeBox.innerHTML = synHtml;
    } else {
      syndromeBox.innerHTML = '<div>✅ Tidak ada aneuploidi terdeteksi pada sampel ini.</div>';
    }

    sectionResults.style.display = 'block';

    // Update pie chart — gunakan ndMeiosisICount, ndMeiosisIICount (camelCase)
    createNdPieChart('nd-pie-chart', r.ndMeiosisICount, r.ndMeiosisIICount);

    // Sembunyikan canvas overlay dan play animasi Three.js
    canvasOverlay.classList.add('hidden');
    scene.playSingleSimulation(data);

    showToast(`✅ Simulasi selesai dalam ${r.executionTimeMs.toFixed(0)} ms`);
  } catch (err) {
    showToast(`❌ Error: ${err.message}`, 'error');
  } finally {
    setLoading(false);
    btnRun.disabled = false;
  }
});

// ─────────────────────────────────────────────
// EVENT: Age Sweep
// ─────────────────────────────────────────────
btnSweep.addEventListener('click', async () => {
  setLoading(true, 'Menjalankan analisis sweep usia 20–45…');
  btnSweep.disabled = true;
  try {
    // Response: { sweep: [{age, observedRisk, modelRisk, aneuploidCount}], totalAges }
    const data = await runAgeSweep(20, 45, 500);
    createRiskCurveChart('risk-chart', data.sweep.map(d => ({
      maternalAge:       d.age,
      totalRiskPercent:  d.observedRisk * 100,   // backend returns fraction
    })), parseInt(ageSlider.value));
    showToast(`✅ Sweep selesai. ${data.totalAges} titik usia dianalisis.`);
  } catch (err) {
    showToast(`❌ Error sweep: ${err.message}`, 'error');
  } finally {
    setLoading(false);
    btnSweep.disabled = false;
  }
});

// ─────────────────────────────────────────────
// EVENT: Keyboard Shortcut (Space = pause)
// ─────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  if (e.code === 'Space' && e.target === document.body) {
    e.preventDefault();
    const paused = scene.togglePause();
    showToast(paused ? '⏸️ Animasi dijeda' : '▶️ Animasi dilanjutkan');
  }
});

// ─────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────

function setLoading(visible, text = '') {
  loadingOverlay.classList.toggle('visible', visible);
  loadingOverlay.setAttribute('aria-hidden', String(!visible));
  if (text) loadingText.textContent = text;
}

let toastTimeout;
function showToast(message, type = 'info') {
  toast.textContent = message;
  toast.style.borderColor = type === 'error' ? 'rgba(255,71,87,0.4)' : 'rgba(255,255,255,0.08)';
  toast.classList.add('show');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove('show'), 3500);
}

// ─────────────────────────────────────────────
// START
// ─────────────────────────────────────────────
initApp();
