import { getRiskCurve } from './utils/api.js';
import Chart from 'chart.js/auto';

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
  { name: 'Triple X', aka: '47,XXX', chr: 'X', type: 'seks', kar: '47,XXX', inc: '1/1.000 (perempuan)', via: 'viable', nd: 'Meiosis I/II', age: 'Lemah', feat: 'Tinggi badan di atas rata-rata, kesulitan belajar ringan, perkembangan bahasa terlambat, menstruasi biasanya normal', desc: 'Tinggi badan di atas rata-rata, kesulitan belajar ringan, perkembangan bahasa terlambat, menstruasi biasanya normal.', ac: '#166534', featured: false },
  { name: 'Sindrom XYY', aka: '47,XYY', chr: 'Y', type: 'seks', kar: '47,XYY', inc: '1/1.000 (laki-laki)', via: 'viable', nd: 'Meiosis II', age: 'Tidak ada', feat: 'Tubuh sangat tinggi, peningkatan risiko masalah perilaku/ADHD pada sebagian individu, fertil, rentan akne', desc: 'Tubuh sangat tinggi, peningkatan risiko masalah perilaku/ADHD pada sebagian individu, fertil, rentan akne.', ac: '#059669', featured: false },
  { name: 'Sindrom XXXY', aka: '48,XXXY', chr: 'X', type: 'seks', kar: '48,XXXY', inc: 'Sangat jarang', via: 'viable', nd: 'Meiosis I+II', age: 'Sedang', feat: 'Disabilitas intelektual sedang-berat, hipogonadisme, ginekomastia, wajah khas', desc: 'Disabilitas intelektual sedang-berat, hipogonadisme, ginekomastia, wajah khas.', ac: '#15803d', featured: false },
  { name: 'Sindrom XXYY', aka: '48,XXYY', chr: 'X/Y', type: 'seks', kar: '48,XXYY', inc: '1/17.000 (laki-laki)', via: 'viable', nd: 'Meiosis I+II', age: 'Sedang', feat: 'Masalah perilaku dan temperamental, hipogonadisme, tubuh sangat tinggi, tremor halus', desc: 'Masalah perilaku dan temperamental, hipogonadisme, tubuh sangat tinggi, tremor halus.', ac: '#15803d', featured: false },
  { name: 'Sindrom XXXXY', aka: '49,XXXXY', chr: 'X', type: 'seks', kar: '49,XXXXY', inc: 'Sangat jarang', via: 'viable', nd: 'Multiple non-disjunction', age: 'Lemah', feat: 'Disabilitas intelektual berat, sinostosis radioulnar, hipogonadisme, dismorfisme wajah', desc: 'Disabilitas intelektual berat, sinostosis radioulnar, hipogonadisme, dismorfisme wajah.', ac: '#166534', featured: false },
  { name: 'Penta X', aka: '49,XXXXX', chr: 'X', type: 'seks', kar: '49,XXXXX', inc: '< 1/100.000 (perempuan)', via: 'jarang', nd: 'Multiple non-disjunction', age: 'Lemah', feat: 'Disabilitas intelektual berat, defek kraniofasial, kelainan jantung dan ginjal', desc: 'Disabilitas intelektual berat, defek kraniofasial, kelainan jantung dan ginjal.', ac: '#b91c1c', featured: false },
  { name: 'Trisomi 22', aka: 'Trisomi 22', chr: '22', type: 'autosom', kar: '47,XX/XY +22', inc: 'sangat jarang', via: 'jarang', nd: 'Bervariasi', age: 'Sedang', feat: 'Kelainan kraniofasial, defek jantung, disabilitas intelektual (mosaik)', desc: 'Kelainan kraniofasial, defek jantung, disabilitas intelektual (mosaik).', ac: '#166534', featured: false },
  { name: 'Sindrom Down Mosaik', aka: 'Mosaik Trisomi 21', chr: '21', type: 'mosaik', kar: '46/47,+21 [mosaik]', inc: '~1-2% kasus Trisomi 21', via: 'viable', nd: 'Meiosis I+mitosis', age: 'Sedang', feat: 'Fenotip lebih ringan dari Trisomi 21 penuh; variabilitas gejala besar', desc: 'Fenotip lebih ringan dari Trisomi 21 penuh; variabilitas gejala besar.', ac: '#16a34a', featured: false },
  { name: 'Sindrom Turner Mosaik', aka: 'Mosaik 45,X', chr: 'X', type: 'mosaik', kar: '45,X/46,XX [mosaik]', inc: 'Lebih jarang dibanding bentuk klasik', via: 'viable', nd: 'Meiosis/mitosis', age: 'Lemah', feat: 'Gejala lebih ringan dari Turner klasik; sebagian kecil masih bisa hamil alami', desc: 'Gejala lebih ringan dari Turner klasik; sebagian kecil masih bisa hamil alami.', ac: '#15803d', featured: false },
  { name: 'Sindrom Klinefelter Mosaik', aka: 'Mosaik 47,XXY', chr: 'X', type: 'mosaik', kar: '46,XY/47,XXY [mosaik]', inc: 'Lebih jarang dibanding bentuk klasik', via: 'viable', nd: 'Meiosis/mitosis', age: 'Sedang', feat: 'Sebagian pria bisa fertil; gejala lebih ringan dari Klinefelter klasik', desc: 'Sebagian pria bisa fertil; gejala lebih ringan dari Klinefelter klasik.', ac: '#15803d', featured: false },
  { name: 'Trisomi 8 Mosaik', aka: 'Warkany Syndrome 2', chr: '8', type: 'mosaik', kar: '46/47,+8 [mosaik]', inc: 'sangat jarang', via: 'viable', nd: 'Mitosis post-zigot', age: 'Lemah', feat: 'Kelainan muskuloskeletal, wajah khas, disabilitas intelektual ringan-sedang, stenosis ureter', desc: 'Kelainan muskuloskeletal, wajah khas, disabilitas intelektual ringan-sedang, stenosis ureter.', ac: '#c2410c', featured: false },
  { name: 'Trisomi 9 Mosaik', aka: 'Trisomi 9 Parsial', chr: '9', type: 'mosaik', kar: '46/47,+9 [mosaik]', inc: 'Kasus sangat jarang', via: 'jarang', nd: 'Mitosis post-zigot', age: 'Lemah', feat: 'Kelainan otak, defek jantung, dismorfisme wajah, kelainan tulang', desc: 'Kelainan otak, defek jantung, dismorfisme wajah, kelainan tulang.', ac: '#b91c1c', featured: false },
  { name: 'Trisomi 20 Mosaik', aka: 'Mosaik Trisomi 20', chr: '20', type: 'mosaik', kar: '46/47,+20 [mosaik]', inc: 'Jarang ditemukan prenatal', via: 'viable', nd: 'Mitosis post-zigot', age: 'Lemah', feat: 'Sering ditemukan prenatal; fenotip sering normal atau sangat ringan', desc: 'Sering ditemukan prenatal; fenotip sering normal atau sangat ringan.', ac: '#15803d', featured: false },
  { name: 'Trisomi 22 Mosaik', aka: 'Mosaik Trisomi 22', chr: '22', type: 'mosaik', kar: '46/47,+22 [mosaik]', inc: 'Sangat jarang', via: 'jarang', nd: 'Mitosis post-zigot', age: 'Lemah', feat: 'Kelainan kraniofasial, defek jantung, disabilitas intelektual', desc: 'Kelainan kraniofasial, defek jantung, disabilitas intelektual.', ac: '#047857', featured: false },
  ...[1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 17, 19].map(i => ({
    name: `Trisomi ${i}`,
    aka: `Trisomi ${i}`,
    chr: `${i}`,
    type: 'autosom',
    kar: `47,XX/XY +${i}`,
    inc: 'Umumnya tidak ditemukan pada kelahiran hidup',
    via: 'tidak viable',
    nd: 'Bervariasi',
    age: 'Lemah',
    feat: 'Aborsi spontan dini; kelainan berat organ vital.',
    desc: `Trisomi ${i} penuh umumnya tidak kompatibel dengan kehidupan. Sebagian besar berakhir keguguran pada trimester pertama.`,
    ac: '#94a3b8',
    featured: false,
  })),
  { name: 'Trisomi 16', aka: 'Trisomi 16', chr: '16', type: 'autosom', kar: '47,XX/XY +16', inc: 'Umumnya tidak ditemukan pada kelahiran hidup', via: 'tidak viable', nd: 'Bervariasi', age: 'Kuat', feat: 'Aborsi spontan dini; kelainan berat organ vital. Penyebab tersering miscarriage trisomi.', desc: 'Trisomi 16 penuh umumnya tidak kompatibel dengan kehidupan. Penyebab tersering miscarriage trisomi. Sebagian besar berakhir keguguran pada trimester pertama.', ac: '#94a3b8', featured: false },
];

function viaTag(v) {
  const k = (v || '').toLowerCase();
  if (k.includes('jarang')) return { cls: 'type-jarang', lbl: 'Jarang' };
  if (k.includes('tidak')) return { cls: 'type-tidak', lbl: 'Tidak Viable' };
  if (k.includes('viable') || k.includes('viabel')) return { cls: 'type-viable', lbl: 'Viable' };
  if (k.includes('mosaik')) return { cls: 'type-mosaik', lbl: 'Mosaik' };
  if (k.includes('kematian')) return { cls: 'type-jarang', lbl: 'Neonatal' };
  return { cls: 'type-tidak', lbl: 'Tidak Viable' };
}

function ageLabel(a) {
  return { Kuat: 'Pengaruh kuat', Sedang: 'Pengaruh sedang', Lemah: 'Pengaruh lemah', 'Tidak ada': 'Tidak berpengaruh' }[a] || a;
}

function ageClass(a) {
  return { Kuat: 'age-kuat', Sedang: 'age-sedang', Lemah: 'age-lemah', 'Tidak ada': 'age-tidak' }[a] || 'age-tidak';
}

// Carousel state
let currentSlide = 0;
let autoSlideInterval = null;
const CARDS_PER_PAGE = 4;

// Parse incidence for display
function parseInc(inc) {
  if (!inc) return { num: '', label: 'insiden' };
  if (inc.includes('/')) {
    const parts = inc.split('/');
    return { num: `1:${parts[1]?.trim() || '?'}`, label: 'insiden kelahiran' };
  }
  return { num: inc, label: 'insiden' };
}

function renderSpotlight() {
  const featured = SYNDROMES.filter(s => s.featured);
  const totalPages = Math.ceil(featured.length / CARDS_PER_PAGE);

  // Create carousel structure
  const el = document.getElementById('spotlight-grid');
  const wrapper = document.querySelector('.spot-carousel-wrap') || createCarouselStructure();

  const track = document.getElementById('spot-carousel-track');
  track.innerHTML = featured.map((s, i) => {
    const v = viaTag(s.via);
    const inc = parseInc(s.inc);
    return `<div class="spot-card ${v.cls} appear" data-index="${i}" style="animation-delay:${i * 0.07}s">
      <div class="spot-card-inner">
        <div class="spot-top">
          <span class="spot-kary">${s.kar}</span>
          <span class="spot-badge">${v.lbl}</span>
        </div>
        <div class="spot-name">${s.name}</div>
        <div class="spot-aka">${s.aka} · Chr ${s.chr}</div>
        <div class="spot-inc">
          <span class="spot-inc-num">${inc.num}</span>
          <span class="spot-inc-label">${inc.label}</span>
        </div>
        <p class="spot-desc">${s.desc}</p>
        <div class="spot-features">
          <div class="spot-ftitle">Manifestasi Klinis</div>
          <div class="spot-fbody">${s.feat}</div>
        </div>
        <div class="spot-footer">
          <span class="spot-footer-lbl">Pengaruh Usia Maternal</span>
          <span class="spot-footer-val ${ageClass(s.age)}">${ageLabel(s.age)}</span>
        </div>
      </div>
    </div>`;
  }).join('');

  // Update dots
  updateCarouselDots();

  // Add click handlers
  document.querySelectorAll('.spot-card').forEach(card => {
    card.addEventListener('click', () => {
      const idx = parseInt(card.dataset.index);
      showDetailModal(featured[idx]);
    });
  });

  // Start auto-slide
  startAutoSlide();
}

function createCarouselStructure() {
  const section = document.getElementById('spotlight-section');
  const divider = section.querySelector('.divider');

  const wrapper = document.createElement('div');
  wrapper.className = 'spot-carousel-wrap';
  wrapper.innerHTML = `
    <div class="spot-carousel-track" id="spot-carousel-track"></div>
  `;

  const nav = document.createElement('div');
  nav.className = 'carousel-nav';
  nav.innerHTML = `
    <button class="carousel-btn" id="carousel-prev">←</button>
    <div class="carousel-dots" id="carousel-dots"></div>
    <button class="carousel-btn" id="carousel-next">→</button>
  `;

  const progress = document.createElement('div');
  progress.className = 'carousel-progress';
  progress.innerHTML = `<div class="carousel-progress-bar" id="carousel-progress-bar"></div>`;

  section.insertBefore(wrapper, divider.nextSibling);
  section.insertBefore(nav, divider.nextSibling);
  section.insertBefore(progress, divider.nextSibling);

  // Add event listeners
  document.getElementById('carousel-prev').addEventListener('click', () => {
    prevSlide();
    resetAutoSlide();
  });
  document.getElementById('carousel-next').addEventListener('click', () => {
    nextSlide();
    resetAutoSlide();
  });

  return wrapper;
}

function updateCarouselDots() {
  const featured = SYNDROMES.filter(s => s.featured);
  const totalPages = Math.ceil(featured.length / CARDS_PER_PAGE);
  const dotsContainer = document.getElementById('carousel-dots');

  dotsContainer.innerHTML = Array.from({ length: totalPages }, (_, i) =>
    `<div class="carousel-dot ${i === currentSlide ? 'active' : ''}" data-page="${i}"></div>`
  ).join('');

  dotsContainer.querySelectorAll('.carousel-dot').forEach(dot => {
    dot.addEventListener('click', () => {
      currentSlide = parseInt(dot.dataset.page);
      updateCarousel();
      resetAutoSlide();
    });
  });

  // Update button states
  document.getElementById('carousel-prev').disabled = currentSlide === 0;
  document.getElementById('carousel-next').disabled = currentSlide >= totalPages - 1;
}

function updateCarousel() {
  const track = document.getElementById('spot-carousel-track');
  const cardWidth = track.querySelector('.spot-card')?.offsetWidth || 0;
  const gap = 16;
  const offset = currentSlide * (cardWidth + gap);
  track.style.transform = `translateX(-${offset}px)`;

  updateCarouselDots();

  // Update progress bar
  const featured = SYNDROMES.filter(s => s.featured);
  const totalPages = Math.ceil(featured.length / CARDS_PER_PAGE);
  const progress = (currentSlide / (totalPages - 1)) * 100 || 0;
  document.getElementById('carousel-progress-bar').style.width = `${progress}%`;
}

function prevSlide() {
  const featured = SYNDROMES.filter(s => s.featured);
  const totalPages = Math.ceil(featured.length / CARDS_PER_PAGE);
  if (currentSlide > 0) {
    currentSlide--;
    updateCarousel();
  }
}

function nextSlide() {
  const featured = SYNDROMES.filter(s => s.featured);
  const totalPages = Math.ceil(featured.length / CARDS_PER_PAGE);
  if (currentSlide < totalPages - 1) {
    currentSlide++;
    updateCarousel();
  }
}

function startAutoSlide() {
  if (autoSlideInterval) clearInterval(autoSlideInterval);
  autoSlideInterval = setInterval(() => {
    const featured = SYNDROMES.filter(s => s.featured);
    const totalPages = Math.ceil(featured.length / CARDS_PER_PAGE);
    currentSlide = (currentSlide + 1) % totalPages;
    updateCarousel();
  }, 5000);
}

function resetAutoSlide() {
  startAutoSlide();
}

// Detail Modal
function showDetailModal(syndrome) {
  let modal = document.getElementById('syndrome-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'syndrome-modal';
    document.body.appendChild(modal);
  }

  const v = viaTag(syndrome.via);
  const inc = parseInc(syndrome.inc);
  const featList = syndrome.feat.split(', ').map(f => f.trim());

  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header ${v.cls}">
        <span class="modal-kary">${syndrome.kar}</span>
        <button class="modal-close" onclick="closeDetailModal()">×</button>
        <h2 class="modal-title">${syndrome.name}</h2>
        <p class="modal-subtitle">${syndrome.aka} · Kromosom ${syndrome.chr}</p>
      </div>
      <div class="modal-body">
        <div class="modal-section">
          <div class="modal-section-title">Insiden</div>
          <div class="modal-inc">
            <span class="modal-inc-num">${inc.num}</span>
            <span class="modal-inc-label">${inc.label}<br><small style="color:var(--ink-faint)">${syndrome.inc}</small></span>
          </div>
        </div>

        <div class="modal-section">
          <div class="modal-section-title">Deskripsi</div>
          <p class="modal-desc">${syndrome.desc}</p>
        </div>

        <div class="modal-section">
          <div class="modal-section-title">Manifestasi Klinis</div>
          <div class="modal-feat-list">
            ${featList.map(f => `
              <div class="modal-feat-item">
                <span class="modal-feat-dot"></span>
                <span>${f}</span>
              </div>
            `).join('')}
          </div>
        </div>

        <div class="modal-section">
          <div class="modal-section-title">Informasi Tambahan</div>
          <div class="modal-meta">
            <div class="modal-meta-item">
              <span class="modal-meta-label">Status:</span>
              <span class="spot-badge ${v.cls}" style="font-size:0.65rem;padding:3px 8px;">${v.lbl}</span>
            </div>
            <div class="modal-meta-item">
              <span class="modal-meta-label">Non-disjunction:</span>
              <span>${syndrome.nd}</span>
            </div>
            <div class="modal-meta-item">
              <span class="modal-meta-label">Pengaruh Usia:</span>
              <span class="modal-age-tag ${ageClass(syndrome.age)}">${ageLabel(syndrome.age)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  modal.classList.add('show');
  document.body.style.overflow = 'hidden';

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeDetailModal();
  });
}

function closeDetailModal() {
  const modal = document.getElementById('syndrome-modal');
  if (modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }
}

// Keyboard support for modal
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeDetailModal();
  if (e.key === 'ArrowLeft') { prevSlide(); resetAutoSlide(); }
  if (e.key === 'ArrowRight') { nextSlide(); resetAutoSlide(); }
});

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
    const inc = parseInc(s.inc);
    return `<div class="syn-card ${v.cls} appear" data-syndrome='${JSON.stringify(s).replace(/'/g, "&#39;")}' style="animation-delay:${Math.min(i * 0.025, 0.45)}s">
      <div class="syn-card-inner">
        <div class="syn-top">
          <span class="syn-kary">${s.kar}</span>
          <span class="syn-badge">${v.lbl}</span>
        </div>
        <div class="syn-name">${s.name}</div>
        <div class="syn-chr">Chr ${s.chr} · ${s.aka}</div>
        <div class="syn-inc">
          <span class="syn-inc-num">${inc.num}</span>
          <span class="syn-inc-label">insiden</span>
        </div>
        <div class="syn-feat">${s.feat}</div>
        <div class="syn-foot">
          <span class="syn-inc">${s.inc}</span>
          <span class="syn-age ${ageClass(s.age)}">${ageLabel(s.age)}</span>
        </div>
      </div>
    </div>`;
  }).join('');

  // Add click handlers
  document.querySelectorAll('.syn-card').forEach(card => {
    card.addEventListener('click', () => {
      const data = JSON.parse(card.dataset.syndrome.replace(/&#39;/g, "'"));
      showDetailModal(data);
    });
  });
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
            font: { size: 12, family: 'GoogleSans, Inter, system-ui, sans-serif', weight: '500' },
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
            font: { size: 12, family: 'GoogleSans, Inter, system-ui, sans-serif', weight: '500' },
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
