import { getRiskCurve } from './utils/api.js';
import Chart from 'chart.js/auto';

// tabel 1: Total kelainan kromosom per 1.000 kelahiran hidup, dikonversi ke persen
const RISK_FALLBACK = {
  15: .22, 16: .21, 17: .20, 18: .19, 19: .18,
  20: .19, 21: .19, 22: .20, 23: .20, 24: .21,
  25: .21, 26: .22, 27: .23, 28: .23, 29: .24,
  30: .26, 31: .26, 32: .31, 33: .35, 34: .41,
  35: .56, 36: .67, 37: .81, 38: .95, 39: 1.24,
  40: 1.58, 41: 2.05, 42: 2.55, 43: 3.26, 44: 4.18,
  45: 5.37, 46: 6.89, 47: 8.91, 48: 11.50, 49: 14.93,
};

let riskCurveCache = null;

function getRisk(age) {
  const a = Math.max(15, Math.min(49, Math.round(age)));
  if (riskCurveCache) {
    const point = riskCurveCache.find(p => p.maternal_age === a);
    if (point) return point.total_risk_percent;
  }
  return RISK_FALLBACK[a] || 0.20;
}

// data Hook 1981 untuk bar chart edukasi
function getHook1981(age) {
  const a = Math.max(15, Math.min(49, Math.round(age)));
  return RISK_FALLBACK[a] || 0.20;
}

const SYNDROMES = [
  { name: 'Sindrom Down (Trisomi 21)', aka: 'Trisomi 21', chr: '21', type: 'autosom', kar: '47,XX/XY +21', inc: '1/700', via: 'viable', nd: 'Meiosis I', age: 'Kuat', feat: 'Wajah datar, hipotonia, disabilitas intelektual ringan-sedang, defek jantung kongenital (40-50%), Brushfield spots', desc: 'Sindrom kromosom paling umum yang viable. Tiga salinan kromosom 21 memengaruhi ratusan gen. Risiko meningkat signifikan seiring bertambahnya usia maternal.', ac: '#16a34a', featColor: '#DFFFBF', featured: true },
  { name: 'Sindrom Edwards (Trisomi 18)', aka: 'Trisomi 18', chr: '18', type: 'autosom', kar: '47,XX/XY +18', inc: '1/5.000', via: 'jarang', nd: 'Meiosis I', age: 'Kuat', feat: 'Tangan mengepal (Edwards fist), defek jantung kompleks, rocker-bottom feet, mikrosefali, overlapping fingers', desc: 'Trisomi autosom kedua paling umum. Lebih dari 90% kasus mengalami defek jantung. Median kelangsungan hidup hanya beberapa minggu.', ac: '#dc2626', featColor: '#FFC2BE', featured: true },
  { name: 'Sindrom Patau (Trisomi 13)', aka: 'Trisomi 13', chr: '13', type: 'autosom', kar: '47,XX/XY +13', inc: '1/10.000', via: 'jarang', nd: 'Meiosis I', age: 'Kuat', feat: 'Holoprosensefali, celah bibir/langit-langit, polidaktili, siklopia, defek jantung berat', desc: 'Kelainan berat otak, wajah, dan jantung. Sebagian besar bayi meninggal pada minggu pertama kehidupan, meskipun sebagian kecil dapat bertahan lebih lama dengan perawatan intensif.', ac: '#ca8a04', featColor: '#FFFEC8', featured: true },
  { name: 'Sindrom Turner', aka: 'Monosomi X', chr: 'X', type: 'seks', kar: '45,X', inc: '1/2.500 (perempuan)', via: 'viable', nd: 'Meiosis I/II', age: 'Tidak ada', feat: 'Perawakan pendek, ovarium streaks, mayoritas infertilitas, webbed neck, koarktasio aorta, amenore primer', desc: 'Satu-satunya monosomi yang viable pada manusia. Sekitar 95-99% embrio 45,X gugur spontan. Hanya terjadi pada wanita.', ac: '#15803d', featColor: '#DFFFBF', featured: true },
  { name: 'Sindrom Klinefelter', aka: '47,XXY', chr: 'X', type: 'seks', kar: '47,XXY', inc: '1/500 (laki-laki)', via: 'viable', nd: 'Meiosis I', age: 'Sedang', feat: 'Hipogonadisme, ginekomastia, gangguan fertilitas yang umum terjadi pada sebagian besar pasien, testis kecil, tubuh tinggi, testosteron rendah, risiko osteoporosis', desc: 'Sindrom kromosom seks paling umum pada pria. Sekitar 75% tidak pernah terdiagnosis. Sering ditemukan saat konsultasi kesuburan.', ac: '#15803d', featColor: '#DFFFBF', featured: true },
  { name: 'Triple X', aka: '47,XXX', chr: 'X', type: 'seks', kar: '47,XXX', inc: '1/1.000 (perempuan)', via: 'viable', nd: 'Meiosis I/II', age: 'Lemah', feat: 'Tinggi badan di atas rata-rata, kesulitan belajar ringan, perkembangan bahasa terlambat, menstruasi biasanya normal', desc: 'Banyak wanita 47,XXX tidak pernah terdiagnosis dan memiliki gejala sangat ringan atau tanpa gejala signifikan.', ac: '#166534', featured: false },
  { name: 'Sindrom XYY', aka: '47,XYY', chr: 'Y', type: 'seks', kar: '47,XYY', inc: '1/1.000 (laki-laki)', via: 'viable', nd: 'Meiosis II', age: 'Tidak ada', feat: 'Tubuh sangat tinggi, peningkatan risiko masalah perilaku/ADHD pada sebagian individu, fertil, rentan akne', desc: 'Sindrom kromosom seks dengan hubungan maternal age yang minimal dibanding trisomi autosom. Umumnya fertil dan hidup normal.', ac: '#059669', featured: false },
  { name: 'Sindrom XXXY', aka: '48,XXXY', chr: 'X', type: 'seks', kar: '48,XXXY', inc: 'Sangat jarang', via: 'viable', nd: 'Meiosis I+II', age: 'Sedang', feat: 'Disabilitas intelektual sedang-berat, hipogonadisme, ginekomastia, wajah khas', desc: 'Varian Klinefelter lebih berat. Tiga kromosom X menyebabkan gangguan perkembangan lebih signifikan.', ac: '#15803d', featured: false },
  { name: 'Sindrom XXYY', aka: '48,XXYY', chr: 'X/Y', type: 'seks', kar: '48,XXYY', inc: '1/17.000 (laki-laki)', via: 'viable', nd: 'Meiosis I+II', age: 'Sedang', feat: 'Masalah perilaku dan temperamental, hipogonadisme, tubuh sangat tinggi, tremor halus', desc: 'Kombinasi X dan Y ekstra. Sering didiagnosis saat dewasa muda.', ac: '#15803d', featured: false },
  { name: 'Sindrom XXXXY', aka: '49,XXXXY', chr: 'X', type: 'seks', kar: '49,XXXXY', inc: 'Sangat jarang', via: 'viable', nd: 'Multiple non-disjunction', age: 'Lemah', feat: 'Disabilitas intelektual berat, sinostosis radioulnar, hipogonadisme, dismorfisme wajah', desc: 'Bentuk paling berat dari kelompok Klinefelter.', ac: '#166534', featured: false },
  { name: 'Penta X', aka: '49,XXXXX', chr: 'X', type: 'seks', kar: '49,XXXXX', inc: '< 1/100.000 (perempuan)', via: 'jarang', nd: 'Multiple non-disjunction', age: 'Lemah', feat: 'Disabilitas intelektual berat, defek kraniofasial, kelainan jantung dan ginjal', desc: 'Lima kromosom X — kasus sangat langka. Prognosis buruk.', ac: '#b91c1c', featured: false },
  { name: 'Trisomi 22', aka: 'Trisomi 22', chr: '22', type: 'autosom', kar: '47,XX/XY +22', inc: 'sangat jarang', via: 'jarang', nd: 'Bervariasi', age: 'Sedang', feat: 'Kelainan kraniofasial, defek jantung, disabilitas intelektual (mosaik)', desc: 'umumnya tidak kompatibel dengan kehidupan. Kasus mosaik bisa bertahan dengan gejala bervariasi.', ac: '#166534', featured: false },
  { name: 'Sindrom Down Mosaik', aka: 'Mosaik Trisomi 21', chr: '21', type: 'mosaik', kar: '46/47,+21 [mosaik]', inc: '~1-2% kasus Trisomi 21', via: 'viable', nd: 'Meiosis I+mitosis', age: 'Sedang', feat: 'Fenotip lebih ringan dari Trisomi 21 penuh; variabilitas gejala besar', desc: 'Sebagian sel normal, sebagian trisomi. Dampak klinis tergantung proporsi sel aneuploid.', ac: '#16a34a', featured: false },
  { name: 'Sindrom Turner Mosaik', aka: 'Mosaik 45,X', chr: 'X', type: 'mosaik', kar: '45,X/46,XX [mosaik]', inc: 'Lebih jarang dibanding bentuk klasik', via: 'viable', nd: 'Meiosis/mitosis', age: 'Lemah', feat: 'Gejala lebih ringan dari Turner klasik; sebagian kecil masih bisa hamil alami', desc: 'Prognosis reproduksi lebih baik. Bentuk paling umum dari Turner.', ac: '#15803d', featured: false },
  { name: 'Sindrom Klinefelter Mosaik', aka: 'Mosaik 47,XXY', chr: 'X', type: 'mosaik', kar: '46,XY/47,XXY [mosaik]', inc: 'Lebih jarang dibanding bentuk klasik', via: 'viable', nd: 'Meiosis/mitosis', age: 'Sedang', feat: 'Sebagian pria bisa fertil; gejala lebih ringan dari Klinefelter klasik', desc: 'Mosaik Klinefelter dengan prognosis reproduksi lebih baik.', ac: '#15803d', featured: false },
  { name: 'Trisomi 8 Mosaik', aka: 'Warkany Syndrome 2', chr: '8', type: 'mosaik', kar: '46/47,+8 [mosaik]', inc: 'sangat jarang', via: 'viable', nd: 'Mitosis post-zigot', age: 'Lemah', feat: 'Kelainan muskuloskeletal, wajah khas, disabilitas intelektual ringan-sedang, stenosis ureter', desc: 'Trisomi 8 penuh tidak viable. Bentuk mosaik memungkinkan bertahan dengan gejala variabel.', ac: '#c2410c', featured: false },
  { name: 'Trisomi 9 Mosaik', aka: 'Trisomi 9 Parsial', chr: '9', type: 'mosaik', kar: '46/47,+9 [mosaik]', inc: 'Kasus sangat jarang', via: 'jarang', nd: 'Mitosis post-zigot', age: 'Lemah', feat: 'Kelainan otak, defek jantung, dismorfisme wajah, kelainan tulang', desc: 'Sangat jarang. Prognosis tergantung persentase sel aneuploid.', ac: '#b91c1c', featured: false },
  { name: 'Trisomi 20 Mosaik', aka: 'Mosaik Trisomi 20', chr: '20', type: 'mosaik', kar: '46/47,+20 [mosaik]', inc: 'Jarang ditemukan prenatal', via: 'viable', nd: 'Mitosis post-zigot', age: 'Lemah', feat: 'Sering ditemukan prenatal; fenotip sering normal atau sangat ringan', desc: 'Sering ditemukan saat amniosentesis tanpa tanda klinis nyata.', ac: '#15803d', featured: false },
  { name: 'Trisomi 22 Mosaik', aka: 'Mosaik Trisomi 22', chr: '22', type: 'mosaik', kar: '46/47,+22 [mosaik]', inc: 'Sangat jarang', via: 'jarang', nd: 'Mitosis post-zigot', age: 'Lemah', feat: 'Kelainan kraniofasial, defek jantung, disabilitas intelektual', desc: 'Prognosis bervariasi tergantung proporsi sel aneuploid.', ac: '#047857', featured: false },
  ...[1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19].map(i => ({
    name: `Trisomi ${i}`,
    aka: `Trisomi ${i}`,
    chr: `${i}`,
    type: 'autosom',
    kar: `47,XX/XY +${i}`,
    inc: 'Umumnya tidak ditemukan pada kelahiran hidup',
    via: 'tidak viable',
    nd: 'Bervariasi',
    age: i === 16 ? 'Kuat' : 'Lemah',
    feat: `Aborsi spontan dini; kelainan berat organ vital.${i === 16 ? ' Penyebab tersering miscarriage trisomi.' : ''}`,
    desc: `Trisomi ${i} penuh umumnya tidak kompatibel dengan kehidupan. Sebagian besar berakhir keguguran pada trimester pertama.`,
    ac: '#94a3b8',
    featured: false,
  })),
];

function viaTag(v) {
  const k = (v || '').toLowerCase();
  if (k.includes('jarang')) return { cls: 'tag-jarang', lbl: 'Jarang Viable' };
  if (k.includes('tidak')) return { cls: 'tag-tidak', lbl: 'Tidak Viable' };
  if (k.includes('viable') || k.includes('viabel')) return { cls: 'tag-viable', lbl: 'Viable' };
  if (k.includes('mosaik')) return { cls: 'tag-mosaik', lbl: 'Mosaik' };
  if (k.includes('kematian')) return { cls: 'tag-jarang', lbl: 'Neonatal' };
  return { cls: 'tag-tidak', lbl: 'Tidak Viable' };
}

function ageLabel(a) {
  return { Kuat: 'Pengaruh kuat', Sedang: 'Pengaruh sedang', Lemah: 'Pengaruh lemah', 'Tidak ada': 'Tidak berpengaruh' }[a] || a;
}

function ageClass(a) {
  return { Kuat: 'age-kuat', Sedang: 'age-sedang', Lemah: 'age-lemah', 'Tidak ada': 'age-tidak' }[a] || 'age-tidak';
}

function renderSpotlight() {
  const el = document.getElementById('spotlight-grid');
  el.innerHTML = SYNDROMES.filter(s => s.featured).map((s, i) => {
    const v = viaTag(s.via);
    return `<div class="spot-card appear" style="--ac:${s.ac}; animation-delay:${i * 0.07}s">
      <div class="spot-top">
        <span class="spot-kary">${s.kar}</span>
        <span class="tag ${v.cls}">${v.lbl}</span>
      </div>
      <div class="spot-name">${s.name}</div>
      <div class="spot-aka">${s.aka} · Chr ${s.chr}</div>
      <p class="spot-desc">${s.desc}</p>
      <div class="spot-features">
        <div class="spot-ftitle">Manifestasi Klinis</div>
        <div class="spot-fbody">${s.feat}</div>
      </div>
      <div class="spot-footer">
        <span class="syn-inc">${s.inc}</span>
        <span class="spot-footer-val ${ageClass(s.age)}">${ageLabel(s.age)}</span>
      </div>
    </div>`;
  }).join('');
}

function renderGrid(list) {
  const el = document.getElementById('all-grid');
  const em = document.getElementById('empty-msg');
  const spotSection = document.getElementById('spotlight-section');
  const divText = document.getElementById('all-divider-text');

  const q = document.getElementById('edu-search').value.toLowerCase().trim();
  const f = document.querySelector('.filt.active-filt')?.dataset.f || 'all';
  const isFiltered = f !== 'all' || q.length > 0;

  spotSection.style.display = isFiltered ? 'none' : '';
  divText.textContent = isFiltered
    ? `Ditemukan ${list.length} sindrom yang sesuai`
    : 'Semua Sindrom Kromosom';

  if (!list.length) {
    el.innerHTML = '';
    em.style.display = 'block';
    return;
  }
  em.style.display = 'none';
  el.innerHTML = list.map((s, i) => {
    const v = viaTag(s.via);
    return `<div class="syn-card appear" style="--ac:${s.ac}; animation-delay:${Math.min(i * 0.025, 0.45)}s">
      <div class="syn-top">
        <span class="syn-kary">${s.kar}</span>
        <span class="tag ${v.cls}">${v.lbl}</span>
      </div>
      <div class="syn-name">${s.name}</div>
      <div class="syn-chr">Chr ${s.chr} · ${s.aka}</div>
      <div class="syn-feat">${s.feat}</div>
      <div class="syn-foot">
        <span class="syn-inc">${s.inc}</span>
        <span class="syn-age ${ageClass(s.age)}">${ageLabel(s.age)}</span>
      </div>
    </div>`;
  }).join('');
}

function getFiltered() {
  const q = document.getElementById('edu-search').value.toLowerCase().trim();
  const f = document.querySelector('.filt.active-filt')?.dataset.f || 'all';
  let list = SYNDROMES;
  if (f === 'viable') list = list.filter(s => { const v = s.via.toLowerCase(); return v.includes('viab') && !v.includes('tidak'); });
  else if (f === 'autosom') list = list.filter(s => s.type === 'autosom');
  else if (f === 'seks') list = list.filter(s => s.type === 'seks');
  else if (f === 'mosaik') list = list.filter(s => s.type === 'mosaik');
  else if (f === 'ama') list = list.filter(s => s.age === 'Kuat' || s.age === 'Sedang');
  if (q) {
    list = list.filter(s =>
      [s.name, s.aka, s.feat, s.kar, s.chr, s.desc].some(x => x.toLowerCase().includes(q))
    );
  }
  return list;
}

document.getElementById('filter-group').addEventListener('click', e => {
  const btn = e.target.closest('.filt');
  if (!btn) return;
  document.querySelectorAll('.filt').forEach(b => b.classList.remove('active-filt'));
  btn.classList.add('active-filt');
  renderGrid(getFiltered());
});

document.getElementById('edu-search').addEventListener('input', () => renderGrid(getFiltered()));

let ageBarsChart = null;

function riskColor(r) {
  if (r < 0.5) return { bg: 'rgba(74,222,128,0.85)', border: '#16a34a' };
  if (r < 2) return { bg: 'rgba(251,146,60,0.85)', border: '#c2410c' };
  return { bg: 'rgba(239,68,68,0.85)', border: '#b91c1c' };
}

function renderBars() {
  const pts = [15, 20, 25, 28, 30, 32, 35, 37, 38, 40, 42, 45, 49];
  const canvas = document.getElementById('age-bars-canvas');
  if (!canvas) return;

  if (ageBarsChart) ageBarsChart.destroy();

  const risks = pts.map(getHook1981);
  const colors = risks.map(riskColor);

  ageBarsChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: pts,
      datasets: [{
        data: risks,
        backgroundColor: colors.map(c => c.bg),
        borderColor: colors.map(c => c.border),
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false,
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
            title: ctx => `Usia ${ctx[0].label} tahun`,
            label: ctx => `Risiko: ${ctx.parsed.y < 1 ? ctx.parsed.y.toFixed(2) : ctx.parsed.y.toFixed(1)}%`,
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          border: { display: false },
          title: {
            display: true,
            text: 'Usia Ibu (Tahun)',
            color: '#4a6e98',
            font: { size: 12, family: 'Inter, system-ui, sans-serif', weight: '500' },
            padding: { top: 8 },
          },
          ticks: {
            color: ctx => {
              const r = risks[ctx.index];
              if (r >= 2) return '#dc2626';
              if (r >= 0.5) return '#c2410c';
              return '#64748b';
            },
            font: ctx => ({
              size: 12,
              family: 'Inter, system-ui, sans-serif',
              weight: risks[ctx.index] >= 0.5 ? '700' : '400',
            }),
          },
        },
        y: {
          type: 'logarithmic',
          grid: { color: 'rgba(196,207,232,0.5)' },
          border: { display: false },
          title: {
            display: true,
            text: 'Risiko Aneuploidi (%)',
            color: '#4a6e98',
            font: { size: 12, family: 'Inter, system-ui, sans-serif', weight: '500' },
            padding: { bottom: 8 },
          },
          afterBuildTicks: axis => {
            axis.ticks = [0.1, 0.3, 0.6, 0.9, 1.2, 1.5, 2, 3, 5, 10, 15].map(v => ({ value: v }));
          },
          ticks: {
            color: '#4a6e98',
            font: { size: 11, family: 'Inter, system-ui, sans-serif' },
            callback: v => v + '%',
          },
        },
      },
    },
  });
}

async function initEdu() {
  try {
    const res = await getRiskCurve(15, 49);
    riskCurveCache = res.curve;
  } catch {

  }

  renderSpotlight();
  renderGrid(SYNDROMES);
  renderBars();
}

initEdu();
