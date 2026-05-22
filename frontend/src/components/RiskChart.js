/**
 * RiskChart.js — Chart.js Chart Components
 * ==========================================
 * Mengelola dua grafik: Kurva Risiko (line chart) dan Distribusi ND (pie chart).
 */

import Chart from 'chart.js/auto';

/**
 * createRiskCurveChart(canvasId, curveData, currentAge)
 * // Membuat atau update line chart kurva risiko usia maternal.
 * // param canvasId: string ID canvas element.
 * // param curveData: array data titik {maternal_age, total_risk_percent}.
 * // param currentAge: integer usia yang sedang dipilih (ditandai dengan garis vertikal).
 * // output: Chart instance.
 * // dipakai untuk: panel kanan — menampilkan tren risiko antar usia.
 */
export function createRiskCurveChart(canvasId, curveData, currentAge = 30) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  // Hapus chart lama jika ada
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  const ages = curveData.map(d => d.maternal_age);
  const risks = curveData.map(d => d.total_risk_percent);

  // Warna gradient berdasarkan nilai risiko
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 200);
  gradient.addColorStop(0, 'rgba(255, 71, 87, 0.6)');
  gradient.addColorStop(0.5, 'rgba(255, 165, 2, 0.3)');
  gradient.addColorStop(1, 'rgba(0, 212, 255, 0.05)');

  return new Chart(canvas, {
    type: 'line',
    data: {
      labels: ages,
      datasets: [{
        label: 'Risiko Aneuploidi (%)',
        data: risks,
        borderColor: '#00d4ff',
        backgroundColor: gradient,
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: ages.map(a =>
          a === currentAge ? '#ff4757' : 'rgba(0,212,255,0.6)'
        ),
        pointRadius: ages.map(a => a === currentAge ? 6 : 2),
        fill: true,
        tension: 0.4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(13,17,23,0.9)',
          titleColor: '#00d4ff',
          bodyColor: '#e2e8f0',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          callbacks: {
            label: ctx => `Risiko: ${ctx.parsed.y.toFixed(4)}%`,
          },
        },
        // Garis vertikal usia 35 (AMA threshold)
        annotation: undefined,
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: 'rgba(255,255,255,0.4)', font: { size: 9 } },
          title: { display: true, text: 'Usia (tahun)', color: 'rgba(255,255,255,0.4)', font: { size: 9 } },
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.05)' },
          ticks: { color: 'rgba(255,255,255,0.4)', font: { size: 9 }, callback: v => v.toFixed(2) + '%' },
          title: { display: true, text: 'Risiko (%)', color: 'rgba(255,255,255,0.4)', font: { size: 9 } },
        },
      },
    },
  });
}

/**
 * createNdPieChart(canvasId, ndMI, ndMII)
 * // Membuat atau update doughnut chart distribusi ND Meiosis I vs II.
 * // param canvasId: string ID canvas element.
 * // param ndMI: integer jumlah ND di Meiosis I.
 * // param ndMII: integer jumlah ND di Meiosis II.
 * // output: Chart instance.
 * // dipakai untuk: panel kanan — distribusi ND per fase meiosis.
 */
export function createNdPieChart(canvasId, ndMI, ndMII) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  const total = ndMI + ndMII;
  if (total === 0) return null;

  return new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: ['Non-disjunction Meiosis I', 'Non-disjunction Meiosis II'],
      datasets: [{
        data: [ndMI, ndMII],
        backgroundColor: ['rgba(124, 58, 237, 0.75)', 'rgba(255, 107, 53, 0.75)'],
        borderColor: ['#7c3aed', '#ff6b35'],
        borderWidth: 1.5,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: 'rgba(255,255,255,0.55)',
            font: { size: 9 },
            padding: 8,
            boxWidth: 10,
          },
        },
        tooltip: {
          backgroundColor: 'rgba(13,17,23,0.9)',
          titleColor: '#00d4ff',
          bodyColor: '#e2e8f0',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          callbacks: {
            label: ctx => {
              const pct = ((ctx.parsed / total) * 100).toFixed(1);
              return `${ctx.label}: ${ctx.parsed} (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

/**
 * drawRiskGauge(canvasId, riskPercent, maxPercent)
 * // Menggambar semi-circular gauge risiko menggunakan Canvas 2D API.
 * // param canvasId: string ID canvas element.
 * // param riskPercent: float nilai risiko dalam persen (0–100).
 * // param maxPercent: float nilai maksimum skala gauge (default: 60).
 * // output: None. Langsung menggambar ke canvas.
 * // dipakai untuk: indikator visual risiko di panel kiri bawah risk card.
 */
export function drawRiskGauge(canvasId, riskPercent, maxPercent = 60) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  const cx = w / 2;
  const cy = h * 0.9;
  const r = Math.min(w, h) * 0.75;

  ctx.clearRect(0, 0, w, h);

  // Track background
  ctx.beginPath();
  ctx.arc(cx, cy, r, Math.PI, 0, false);
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 10;
  ctx.stroke();

  // Risk fill
  const fraction = Math.min(riskPercent / maxPercent, 1);
  const startAngle = Math.PI;
  const endAngle = Math.PI + (Math.PI * fraction);

  const grad = ctx.createLinearGradient(0, 0, w, 0);
  grad.addColorStop(0, '#2ed573');
  grad.addColorStop(0.4, '#ffa502');
  grad.addColorStop(1, '#ff4757');

  ctx.beginPath();
  ctx.arc(cx, cy, r, startAngle, endAngle, false);
  ctx.strokeStyle = grad;
  ctx.lineWidth = 10;
  ctx.lineCap = 'round';
  ctx.stroke();

  // Text risiko
  ctx.fillStyle = '#e2e8f0';
  ctx.font = `bold ${h * 0.22}px 'JetBrains Mono', monospace`;
  ctx.textAlign = 'center';
  ctx.fillText(`${riskPercent < 0.01 ? riskPercent.toFixed(4) : riskPercent.toFixed(2)}%`, cx, cy - r * 0.15);

  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.font = `${h * 0.13}px Inter, sans-serif`;
  ctx.fillText('risiko total', cx, cy - r * 0.15 + h * 0.16);
}
