// Untuk mengelola dua grafik: Kurva Risiko dan Distribusi ND 
import Chart from 'chart.js/auto';

// untuk membuat line chart untuk visualisasi kenaikan risiko berdasarkan usia
export function createRiskCurveChart(canvasId, curveData, currentAge = 30) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;

  // hapus chart lama jika ada supaya gambar chart tidak numpuk
  const existing = Chart.getChart(canvas);
  if (existing) existing.destroy();

  const ages  = curveData.map(d => d.maternal_age);
  const risks = curveData.map(d => d.total_risk_percent);

  // warna gradient berdasarkan nilai risiko
  const ctx = canvas.getContext('2d');
  const gradient = ctx.createLinearGradient(0, 0, 0, 200);
  gradient.addColorStop(0, 'rgba(239, 68, 68, 0.22)');
  gradient.addColorStop(0.5, 'rgba(251, 191, 36, 0.12)');
  gradient.addColorStop(1, 'rgba(30, 64, 175, 0.04)');

  return new Chart(canvas, {
    type: 'line',
    data: {
      labels: ages,
      datasets: [{
        label: 'Risiko Aneuploidi (%)',
        data: risks,
        borderColor: '#2563eb',
        backgroundColor: gradient,
        borderWidth: 1.5,
        pointBackgroundColor: ages.map(a => a === currentAge ? '#ef4444' : '#2563eb'),
        pointRadius: ages.map(a => a === currentAge ? 6 : 2.5),
        fill: true,
        tension: 0.4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1e3a5f',
          titleColor: '#93c5fd',
          bodyColor: '#dbeafe',
          borderColor: '#1e40af',
          borderWidth: 1,
          cornerRadius: 8,
          callbacks: {
            label: ctx => `Risiko: ${ctx.parsed.y.toFixed(4)}%`,
          },
        },
      },
      scales: {
        x: {
          grid: { color: '#e8eef6' },
          ticks: { color: '#4a6e98', font: { size: 11, family: 'Inter, system-ui, sans-serif' } },
          title: { display: true, text: 'Usia (tahun)', color: '#4a6e98', font: { size: 11, family: 'Inter, system-ui, sans-serif' } },
        },
        y: {
          grid: { color: '#e8eef6' },
          ticks: { color: '#4a6e98', font: { size: 11, family: 'Inter, system-ui, sans-serif' }, callback: v => v.toFixed(1) + '%' },
          title: { display: true, text: 'Risiko (%)', color: '#4a6e98', font: { size: 11, family: 'Inter, system-ui, sans-serif' } },
        },
      },
    },
  });
}

// pie chart untuk perbandingan ND Meiosis I vs Meiosis II
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
        backgroundColor: ['rgba(30, 64, 175, 0.75)', 'rgba(74, 144, 217, 0.75)'],
        borderColor: ['#1e40af', '#4a90d9'],
        borderWidth: 1.5,
        hoverOffset: 6,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '65%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: '#4a6e98',
            font: { size: 11, family: 'Inter, system-ui, sans-serif' },
            padding: 12,
            boxWidth: 12,
          },
        },
        tooltip: {
          backgroundColor: '#1e3a5f',
          titleColor: '#93c5fd',
          bodyColor: '#dbeafe',
          borderColor: '#1e40af',
          borderWidth: 1,
          cornerRadius: 8,
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

// gauge chart untuk indikator visual total risiko di panel kiri bawah risk card
export function drawRiskGauge(canvasId, riskPercent, maxPercent = 60) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  const cx = w / 2;
  const cy = h * 0.9;
  const r = Math.min(w, h) * 0.72;

  ctx.clearRect(0, 0, w, h);

  ctx.beginPath();
  ctx.arc(cx, cy, r, Math.PI, 0, false);
  ctx.strokeStyle = '#b8cfe8';
  ctx.lineWidth = 10;
  ctx.stroke();

  // nilai risiko dibanding maksimum
  const fraction = Math.min(riskPercent / maxPercent, 1);

  const grad = ctx.createLinearGradient(0, 0, w, 0);
  grad.addColorStop(0, '#22c55e');
  grad.addColorStop(0.4, '#f59e0b');
  grad.addColorStop(1, '#ef4444');

  ctx.beginPath();
  ctx.arc(cx, cy, r, Math.PI, Math.PI + Math.PI * fraction, false);
  ctx.strokeStyle = grad;
  ctx.lineWidth = 10;
  ctx.lineCap = 'round';
  ctx.stroke();

  // Text risiko
  ctx.fillStyle = '#1e40af';
  ctx.font = `600 ${h * 0.21}px 'JetBrains Mono', monospace`;
  ctx.textAlign = 'center';
  ctx.fillText(
    riskPercent < 0.01 ? riskPercent.toFixed(4) + '%' : riskPercent.toFixed(2) + '%',
    cx, cy - r * 0.12
  );

  // label bawah gauge
  ctx.fillStyle = '#4a6e98';
  ctx.font = `400 ${h * 0.12}px 'Inter', sans-serif`;
  ctx.fillText('risiko total', cx, cy - r * 0.12 + h * 0.17);
}