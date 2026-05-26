// Entry point aplikasi
import { MeiosisScene } from './scenes/MeiosisScene.js';
import { getRiskProfile, getRiskCurve, runSimulation, runAgeSweep } from './utils/api.js';
import { createRiskCurveChart, createNdPieChart, drawRiskGauge } from './components/RiskChart.js';

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

const resAneuploid = document.getElementById('res-aneuploid');
const resObserved  = document.getElementById('res-observed');
const resNdMI      = document.getElementById('res-nd-mi');
const resNdMII     = document.getElementById('res-nd-mii');

const statTotalRisk = document.getElementById('stat-total-risk');
const statMiRisk    = document.getElementById('stat-mi-risk');
const statMiiRisk   = document.getElementById('stat-mii-risk');
const statCategory  = document.getElementById('stat-category');
const statRatio     = document.getElementById('stat-ratio');

const stageChips = {
  interphase: document.getElementById('chip-interphase'),
  prophase:   document.getElementById('chip-prophase'),
  metaphase:  document.getElementById('chip-metaphase'),
  anaphase:   document.getElementById('chip-anaphase'),
  meiosis2:   document.getElementById('chip-meiosis2'),
  gametes:    document.getElementById('chip-gametes'),
};

const scene = new MeiosisScene(document.getElementById('three-canvas'));

scene.onStageChange((stageName) => {
  Object.values(stageChips).forEach(c => c.classList.remove('active', 'error'));
  const chip = stageChips[stageName];
  if (chip) chip.classList.add('active');
});


let riskCurveData = [];

function showChartCanvas(canvasId, placeholderId) {
  const canvas = document.getElementById(canvasId);
  const ph = document.getElementById(placeholderId);
  if (canvas) canvas.style.display = 'block';
  if (ph) ph.style.display = 'none';
}

async function initApp() {
  drawRiskGauge('risk-gauge', 0, 60);
  try {
    const curveRes = await getRiskCurve(15, 50);
    riskCurveData = curveRes.curve;
    showChartCanvas('risk-chart', 'risk-chart-placeholder');
    createRiskCurveChart('risk-chart', riskCurveData, 30);
    await updateRiskProfile(30);
  } catch {
    showToast('Backend tidak terhubung. Pastikan server FastAPI berjalan.', 'error');
  }
}

async function updateRiskProfile(age) {
  try {
    const profile = await getRiskProfile(age);

    statTotalRisk.textContent = `${profile.total_risk_percent.toFixed(4)}%`;
    statMiRisk.textContent    = `${(profile.meiosis_I_risk * 100).toFixed(4)}%`;
    statMiiRisk.textContent   = `${(profile.meiosis_II_risk * 100).toFixed(4)}%`;
    statRatio.textContent     = `${profile.risk_ratio_to_base.toFixed(1)}x`;

    // mapping warna badge berdasarkan kategori risiko
    const catStyles = {
      rendah:          { bg: '#f0fdf4', color: '#15803d', border: '#bbf7d0', label: 'Rendah' },
      sedang:          { bg: '#fffbeb', color: '#b45309', border: '#fde68a', label: 'Sedang' },
      tinggi:          { bg: '#fff7ed', color: '#c2410c', border: '#fed7aa', label: 'Tinggi' },
      'sangat tinggi': { bg: '#fef2f2', color: '#b91c1c', border: '#fecaca', label: 'Sangat Tinggi' },
    };
    const style = catStyles[profile.risk_category] || catStyles.rendah;
    statCategory.textContent = style.label;
    statCategory.style.cssText = `background:${style.bg};color:${style.color};border:1px solid ${style.border}`;

    drawRiskGauge('risk-gauge', profile.total_risk_percent, 60);

    if (riskCurveData.length) {
      createRiskCurveChart('risk-chart', riskCurveData, age);
    }
  } catch {
  }
}

// debounce biar request ga spam tiap slider digeser
let sliderDebounce;
ageSlider.addEventListener('input', () => {
  const age = parseInt(ageSlider.value);
  ageDisplay.textContent = `${age} tahun`;
  clearTimeout(sliderDebounce);
  sliderDebounce = setTimeout(() => updateRiskProfile(age), 300);
});

btnRun.addEventListener('click', async () => {
  const age    = parseInt(ageSlider.value);
  const nSim   = parseInt(nSimSelect.value);
  const chrNum = parseInt(chrSelect.value);

  setLoading(true, `Menjalankan ${nSim.toLocaleString()} iterasi Monte Carlo...`);
  btnRun.disabled = true;

  try {
    const data = await runSimulation({
      maternal_age: age,
      n_simulations: nSim,
      target_chromosome: chrNum,
    });

    // tampilkan hasil simulasi ke panel statistik
    const r = data.results;
    resAneuploid.textContent = r.aneuploid_count.toLocaleString();
    resObserved.textContent  = `${r.observed_risk_percent.toFixed(4)}%`;
    resNdMI.textContent      = r.nd_meiosis_I_count.toLocaleString();
    resNdMII.textContent     = r.nd_meiosis_II_count.toLocaleString();

    if (Object.keys(r.syndrome_counts).length > 0) {
      syndromeBox.innerHTML = Object.entries(r.syndrome_counts)
        .sort((a, b) => b[1] - a[1]) // urutkan sindrom dari jumlah terbanyak
        .map(([syn, cnt]) => `<div><strong>${syn}</strong>: ${cnt} gamet</div>`)
        .join('');
    } else {
      syndromeBox.innerHTML = '<div>Tidak ada aneuploidi terdeteksi pada sampel ini.</div>';
    }

    sectionResults.style.display = 'block';
    showChartCanvas('nd-pie-chart', 'nd-chart-placeholder');
    createNdPieChart('nd-pie-chart', r.nd_meiosis_I_count, r.nd_meiosis_II_count);
    canvasOverlay.classList.add('hidden');
    scene.playSingleSimulation(data);

    showToast(`Simulasi selesai dalam ${r.execution_time_ms.toFixed(0)} ms`);
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  } finally {
    setLoading(false);
    btnRun.disabled = false;
  }
});

btnSweep.addEventListener('click', async () => {
  setLoading(true, 'Menjalankan analisis sweep usia 20-45...');
  btnSweep.disabled = true;
  try {
    const data = await runAgeSweep(20, 45, 500);
    createRiskCurveChart('risk-chart', data.sweep.map(d => ({
      maternal_age: d.age,
      total_risk_percent: d.observed_risk * 100,
    })), parseInt(ageSlider.value));
    showToast(`Sweep selesai. ${data.total_ages} titik usia dianalisis.`);
  } catch (err) {
    showToast(`Error sweep: ${err.message}`, 'error');
  } finally {
    setLoading(false);
    btnSweep.disabled = false;
  }
});

// shortcut space untuk pause/resume animasi
document.addEventListener('keydown', (e) => {
  if (e.code === 'Space' && e.target === document.body) {
    e.preventDefault();
    const paused = scene.togglePause();
    showToast(paused ? 'Animasi dijeda' : 'Animasi dilanjutkan');
  }
});

// toggle overlay loading selama request berjalan
function setLoading(visible, text = '') {
  loadingOverlay.classList.toggle('visible', visible);
  if (text) loadingText.textContent = text;
}

let toastTimeout;
function showToast(message, type = 'info') {
  toast.textContent = message;
  toast.style.borderColor = type === 'error' ? '#fecaca' : '#bbf7d0';
  toast.classList.add('show');
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => toast.classList.remove('show'), 3500);
}

// load data awal untuk chart & risk profile
initApp();