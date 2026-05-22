/**
 * MeiosisScene.js — Three.js 3D Scene untuk Visualisasi Meiosis
 * ==============================================================
 * Kelas utama yang mengelola seluruh siklus animasi Three.js:
 *   - Sel induk diploid dengan 23 pasang kromosom 3D
 *   - Animasi benang spindle dan pemisahan kromosom
 *   - Efek non-disjunction (gagal pisah) merah berdenyut
 *   - Gamet hasil meiosis (normal / aneuploid)
 *
 * Teknologi: Three.js r165, GSAP 3 (animasi), OrbitControls
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import gsap from 'gsap';

// ── Warna Tema ───────────────────────────────────────────────
const COLORS = {
  bg:             0x07080f,
  chrNormal:      0x00d4ff,   // Cyan — kromosom normal
  chrNd:          0xff4757,   // Merah — non-disjunction
  chrNdMII:       0xff9f43,   // Oranye — ND Meiosis II
  spindle:        0x7c3aed,   // Ungu — benang spindle
  spindleNd:      0xff4757,   // Merah — spindle gagal
  cellMembrane:   0x1a2035,
  nucleus:        0x0d1530,
  particle:       0x00d4ff,
  gamet:          0x2ed573,   // Hijau — gamet normal
  gametNd:        0xff4757,   // Merah — gamet aneuploid
};

export class MeiosisScene {
  /**
   * constructor(canvasEl)
   * // Inisialisasi Three.js renderer, scene, camera, dan controls.
   * // param canvasEl: HTMLCanvasElement target canvas.
   * // output: None.
   * // dipakai untuk: new MeiosisScene(document.getElementById('three-canvas')).
   */
  constructor(canvasEl) {
    this.canvas = canvasEl;
    this.animating = false;
    this.paused = false;
    this._objects = [];       // Semua mesh yang bisa di-dispose
    this._timeline = null;    // GSAP Timeline aktif
    this._onStageChange = null; // Callback untuk update UI stage bar

    this._initRenderer();
    this._initScene();
    this._initCamera();
    this._initLights();
    this._initControls();
    this._initParticles();
    this._startRenderLoop();
    this._handleResize();
  }

  // ──────────────────────────────────────────────────────────
  // INIT METHODS
  // ──────────────────────────────────────────────────────────

  /**
   * _initRenderer()
   * // Mengkonfigurasi WebGLRenderer dengan antialiasing dan tone mapping.
   * // param: tidak ada.
   * // output: None. Menetapkan this.renderer.
   * // dipakai untuk: langkah pertama konstruktor.
   */
  _initRenderer() {
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: false,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.2;
    this.renderer.setClearColor(COLORS.bg, 1);
  }

  /**
   * _initScene()
   * // Membuat THREE.Scene dan menambahkan fog ambient.
   * // param: tidak ada.
   * // output: None. Menetapkan this.scene.
   * // dipakai untuk: langkah kedua konstruktor.
   */
  _initScene() {
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(COLORS.bg, 0.035);
  }

  /**
   * _initCamera()
   * // Membuat PerspectiveCamera dengan posisi default.
   * // param: tidak ada.
   * // output: None. Menetapkan this.camera.
   * // dipakai untuk: langkah ketiga konstruktor.
   */
  _initCamera() {
    const aspect = this.canvas.clientWidth / this.canvas.clientHeight;
    this.camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 500);
    this.camera.position.set(0, 0, 20);
  }

  /**
   * _initLights()
   * // Menambahkan ambient + directional + point lights ke scene.
   * // param: tidak ada.
   * // output: None.
   * // dipakai untuk: memberikan depth dan nuansa neon ke objek 3D.
   */
  _initLights() {
    const ambient = new THREE.AmbientLight(0xffffff, 0.3);
    this.scene.add(ambient);

    const dir = new THREE.DirectionalLight(0xffffff, 0.8);
    dir.position.set(10, 20, 15);
    this.scene.add(dir);

    // Point lights berwarna neon
    const bluePoint = new THREE.PointLight(COLORS.chrNormal, 2, 40);
    bluePoint.position.set(-8, 5, 0);
    this.scene.add(bluePoint);

    const purplePoint = new THREE.PointLight(COLORS.spindle, 1.5, 30);
    purplePoint.position.set(8, -5, 0);
    this.scene.add(purplePoint);
  }

  /**
   * _initControls()
   * // Menginisialisasi OrbitControls untuk interaksi mouse (drag, scroll, pan).
   * // param: tidak ada.
   * // output: None. Menetapkan this.controls.
   * // dipakai untuk: memungkinkan user memutar dan memperbesar/kecil scene 3D.
   */
  _initControls() {
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.minDistance = 5;
    this.controls.maxDistance = 60;
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 0.3;
  }

  /**
   * _initParticles()
   * // Membuat field partikel background (efek kosmik / DNA floating particles).
   * // param: tidak ada.
   * // output: None. Menambahkan Points ke this.scene.
   * // dipakai untuk: estetika background agar terkesan seperti lingkungan biologis.
   */
  _initParticles() {
    const count = 1200;
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      positions[i * 3]     = (Math.random() - 0.5) * 120;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 120;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 120;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    const mat = new THREE.PointsMaterial({
      color: COLORS.particle,
      size: 0.08,
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.35,
    });
    this.scene.add(new THREE.Points(geo, mat));
  }

  // ──────────────────────────────────────────────────────────
  // RENDER LOOP
  // ──────────────────────────────────────────────────────────

  /**
   * _startRenderLoop()
   * // Memulai requestAnimationFrame loop untuk rendering kontinu.
   * // param: tidak ada.
   * // output: None.
   * // dipakai untuk: animasi real-time Three.js.
   */
  _startRenderLoop() {
    const animate = () => {
      requestAnimationFrame(animate);
      if (!this.paused) {
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
      }
    };
    animate();
  }

  // ──────────────────────────────────────────────────────────
  // SCENE BUILDING
  // ──────────────────────────────────────────────────────────

  /**
   * _makeCellMembrane(radius, color, opacity)
   * // Membuat mesh bola transparan sebagai membran sel.
   * // param radius: float radius bola.
   * // param color: hex warna membran.
   * // param opacity: float transparansi (0–1).
   * // output: THREE.Mesh membran sel.
   * // dipakai untuk: membuat representasi visual sel induk dan sel anak.
   */
  _makeCellMembrane(radius = 7, color = COLORS.cellMembrane, opacity = 0.25) {
    const geo = new THREE.SphereGeometry(radius, 32, 32);
    const mat = new THREE.MeshPhongMaterial({
      color,
      transparent: true,
      opacity,
      side: THREE.FrontSide,
      wireframe: false,
    });
    const mesh = new THREE.Mesh(geo, mat);
    this._objects.push(mesh);
    return mesh;
  }

  /**
   * _makeChromosome(color, length, ndEffect)
   * // Membuat mesh kapsul/silinder yang merepresentasikan satu kromosom.
   * // param color: hex warna kromosom.
   * // param length: float panjang kromosom.
   * // param ndEffect: boolean, jika true tambahkan efek glow merah ND.
   * // output: THREE.Group berisi mesh kromosom + glow.
   * // dipakai untuk: membangun representasi 23 pasang kromosom dalam sel.
   */
  _makeChromosome(color = COLORS.chrNormal, length = 1.2, ndEffect = false) {
    const group = new THREE.Group();

    const geo = new THREE.CapsuleGeometry(0.12, length, 8, 16);
    const mat = new THREE.MeshPhongMaterial({
      color,
      emissive: color,
      emissiveIntensity: ndEffect ? 0.6 : 0.2,
      shininess: 80,
    });
    const mesh = new THREE.Mesh(geo, mat);
    group.add(mesh);

    // Glow aura untuk kromosom ND
    if (ndEffect) {
      const glowGeo = new THREE.CapsuleGeometry(0.22, length + 0.1, 8, 16);
      const glowMat = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.15,
        side: THREE.BackSide,
      });
      group.add(new THREE.Mesh(glowGeo, glowMat));
    }

    this._objects.push(group);
    return group;
  }

  /**
   * _makeSpindleFiber(from, to, color)
   * // Membuat silinder tipis yang merepresentasikan satu benang spindle.
   * // param from: THREE.Vector3 titik awal (sentromer kromosom).
   * // param to: THREE.Vector3 titik akhir (kutub sel / kinetochor).
   * // param color: hex warna benang.
   * // output: THREE.Mesh silinder spindle.
   * // dipakai untuk: visualisasi benang spindel saat metafase/anafase.
   */
  _makeSpindleFiber(from, to, color = COLORS.spindle) {
    const dir = new THREE.Vector3().subVectors(to, from);
    const len = dir.length();
    const mid = new THREE.Vector3().addVectors(from, to).multiplyScalar(0.5);

    const geo = new THREE.CylinderGeometry(0.03, 0.03, len, 6);
    const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.6 });
    const mesh = new THREE.Mesh(geo, mat);

    // Orientasikan silinder agar mengarah dari from ke to
    mesh.position.copy(mid);
    mesh.quaternion.setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      dir.normalize()
    );
    this._objects.push(mesh);
    return mesh;
  }

  // ──────────────────────────────────────────────────────────
  // PUBLIC: PLAY ANIMATION
  // ──────────────────────────────────────────────────────────

  /**
   * playSingleSimulation(simulationData)
   * // Menjalankan animasi GSAP lengkap berdasarkan data simulasi dari API.
   * // Animasi mencakup: interfase → profase → metafase → anafase → gamet.
   * // Jika ada ND, animasi spindel gagal ditampilkan dengan efek berdenyut merah.
   * // param simulationData: object SimulationResult dari API /api/simulate.
   * // output: None. Memulai GSAP timeline animasi.
   * // dipakai untuk: dipanggil setelah respons API berhasil diterima.
   */
  playSingleSimulation(simulationData) {
    this._clearScene();
    this.controls.autoRotate = false;

    const hasND = simulationData.results.aneuploid_count > 0;
    const sampleGamete = simulationData.sample_gametes?.[0];
    const ndChromosomes = sampleGamete?.affected_chromosomes || [];

    // ── Buat sel induk ─────────────────────────────────────
    const cellGroup = new THREE.Group();
    this.scene.add(cellGroup);

    const membrane = this._makeCellMembrane(6.5, COLORS.cellMembrane, 0.2);
    cellGroup.add(membrane);

    // ── Buat 23 kromosom mini melingkar di dalam sel ────────
    const chrGroups = [];
    for (let i = 0; i < 23; i++) {
      const angle = (i / 23) * Math.PI * 2;
      const r = 3.5;
      const isNd = ndChromosomes.some(c => c.number === (i + 1));
      const color = isNd ? COLORS.chrNd : COLORS.chrNormal;

      const chrG = this._makeChromosome(color, 0.9, isNd);
      chrG.position.set(
        Math.cos(angle) * r,
        Math.sin(angle) * r * 0.6,
        (Math.random() - 0.5) * 1.5
      );
      chrG.rotation.z = angle + Math.PI / 2;
      cellGroup.add(chrG);
      chrGroups.push(chrG);
    }

    // ── Spindle fibers ke dua kutub ────────────────────────
    const poleTop = new THREE.Vector3(0, 6, 0);
    const poleBottom = new THREE.Vector3(0, -6, 0);
    const spindleGroup = new THREE.Group();
    spindleGroup.visible = false;
    this.scene.add(spindleGroup);

    chrGroups.forEach((cg) => {
      const isNd = ndChromosomes.some((_, idx) => idx < 3 && cg === chrGroups[idx]);
      const fiberColor = isNd ? COLORS.spindleNd : COLORS.spindle;
      const f1 = this._makeSpindleFiber(cg.position, poleTop, fiberColor);
      const f2 = this._makeSpindleFiber(cg.position, poleBottom, fiberColor);
      spindleGroup.add(f1, f2);
    });

    // ── GSAP Timeline Animasi ──────────────────────────────
    const tl = gsap.timeline({ defaults: { ease: 'power2.inOut' } });
    this._timeline = tl;

    // [0] Interfase — sel tampak normal, kromosom melingkar
    tl.call(() => this._setStage('interphase'));

    // [1] Profase — kromosom memadat, bergerak ke tengah
    tl.call(() => this._setStage('prophase'), null, '+=1.5');
    tl.to(cellGroup.rotation, { y: Math.PI * 0.5, duration: 2 }, '-=0');

    // [2] Metafase — spindle muncul, kromosom berbaris di ekuator
    tl.call(() => {
      this._setStage('metaphase');
      spindleGroup.visible = true;
    }, null, '+=0.8');
    chrGroups.forEach((cg, i) => {
      tl.to(cg.position, {
        x: (Math.random() - 0.5) * 1.5,
        y: (Math.random() - 0.5) * 0.4,
        z: (Math.random() - 0.5) * 1.5,
        duration: 1.2,
      }, '<0.05');
    });

    // [3] Anafase — kromosom berpisah ke dua kutub
    tl.call(() => this._setStage('anaphase'), null, '+=0.5');
    chrGroups.forEach((cg, i) => {
      const isNd = ndChromosomes.some(c => c.number === (i + 1));
      const targetY = (i % 2 === 0) ? 4.5 : -4.5;

      if (isNd && hasND) {
        // ND: kromosom tidak bergerak ke kutub — tetap di tengah
        tl.to(cg.position, { y: (Math.random() - 0.5) * 0.5, duration: 1.5 }, '<0.03');
        // Tambah efek pulse merah
        tl.to(cg.children[0].material, { emissiveIntensity: 1.0, duration: 0.3, yoyo: true, repeat: 4 }, '<');
      } else {
        tl.to(cg.position, { y: targetY, duration: 1.5 }, '<0.03');
      }
    });

    // [4] Meiosis II — sel membelah
    tl.call(() => this._setStage('meiosis2'), null, '+=0.3');
    tl.to(membrane.scale, { x: 0.5, y: 0.5, z: 0.5, duration: 1.0 });

    // [5] Tampilkan gamet hasil
    tl.call(() => {
      this._setStage('gametes');
      spindleGroup.visible = false;
      this._showGametes(simulationData, hasND);
    }, null, '+=0.5');

    tl.call(() => { this.controls.autoRotate = true; }, null, '+=1');
  }

  /**
   * _showGametes(simData, hasND)
   * // Membuat representasi visual gamet hasil meiosis di scene.
   * // param simData: object data simulasi dari API.
   * // param hasND: boolean, apakah ada non-disjunction.
   * // output: None. Menambahkan mesh gamet ke scene.
   * // dipakai untuk: dipanggil pada akhir timeline animasi meiosis.
   */
  _showGametes(simData, hasND) {
    this._clearScene();
    const total = simData.results.total_runs;
    const aneuploidCount = simData.results.aneuploid_count;
    const normalCount = simData.results.normal_count;

    // Tampilkan 8 gamet sebagai bola-bola kecil
    const displayCount = 8;
    for (let i = 0; i < displayCount; i++) {
      // Proporsi aneuploid: misal dari 10.000, 105 aneuploid → 1-2 dari 8 tampil merah
      const isAneuploid = i < Math.round((aneuploidCount / total) * displayCount);
      const color = isAneuploid ? COLORS.gametNd : COLORS.gamet;

      const angle = (i / displayCount) * Math.PI * 2;
      const radius = 5;
      const geo = new THREE.SphereGeometry(0.7, 20, 20);
      const mat = new THREE.MeshPhongMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.3,
        transparent: true,
        opacity: 0.85,
      });
      const sphere = new THREE.Mesh(geo, mat);
      sphere.position.set(Math.cos(angle) * radius, Math.sin(angle) * radius * 0.5, 0);

      this.scene.add(sphere);
      this._objects.push(sphere);

      // Animasi fade-in
      sphere.scale.set(0, 0, 0);
      gsap.to(sphere.scale, {
        x: 1, y: 1, z: 1,
        duration: 0.6,
        delay: i * 0.08,
        ease: 'back.out(1.5)',
      });

      // Pulse emissive untuk aneuploid
      if (isAneuploid) {
        gsap.to(mat, {
          emissiveIntensity: 0.9,
          duration: 0.5,
          yoyo: true,
          repeat: -1,
          ease: 'sine.inOut',
        });
      }
    }
  }

  // ──────────────────────────────────────────────────────────
  // HELPERS
  // ──────────────────────────────────────────────────────────

  /**
   * _clearScene()
   * // Menghapus semua objek simulasi dari scene dan melepas memori GPU.
   * // param: tidak ada.
   * // output: None.
   * // dipakai untuk: reset scene sebelum memulai animasi baru.
   */
  _clearScene() {
    this._objects.forEach((obj) => {
      this.scene.remove(obj);
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose());
        else obj.material.dispose();
      }
    });
    this._objects = [];
    if (this._timeline) {
      this._timeline.kill();
      this._timeline = null;
    }
  }

  /**
   * _setStage(stageName)
   * // Memanggil callback UI untuk mengupdate stage bar.
   * // param stageName: string nama fase ('interphase', 'prophase', ...).
   * // output: None.
   * // dipakai untuk: sinkronisasi UI stage bar dengan animasi GSAP.
   */
  _setStage(stageName) {
    if (typeof this._onStageChange === 'function') {
      this._onStageChange(stageName);
    }
  }

  /**
   * onStageChange(callback)
   * // Mendaftarkan callback yang dipanggil setiap kali stage animasi berubah.
   * // param callback: function(stageName: string) => void.
   * // output: None.
   * // dipakai untuk: menghubungkan scene ke UI stage bar chips di HTML.
   */
  onStageChange(callback) {
    this._onStageChange = callback;
  }

  /**
   * togglePause()
   * // Menjeda atau melanjutkan animasi GSAP dan render loop.
   * // param: tidak ada.
   * // output: boolean — status paused saat ini (true = sedang jeda).
   * // dipakai untuk: tombol Space bar keyboard shortcut.
   */
  togglePause() {
    this.paused = !this.paused;
    if (this._timeline) {
      this.paused ? this._timeline.pause() : this._timeline.resume();
    }
    return this.paused;
  }

  /**
   * _handleResize()
   * // Menyesuaikan renderer dan camera saat ukuran jendela berubah.
   * // param: tidak ada.
   * // output: None. Mendaftarkan event listener 'resize'.
   * // dipakai untuk: responsivitas tampilan pada berbagai ukuran layar.
   */
  _handleResize() {
    window.addEventListener('resize', () => {
      const w = this.canvas.clientWidth;
      const h = this.canvas.clientHeight;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h);
    });
  }

  /**
   * dispose()
   * // Menghancurkan renderer dan membersihkan semua resource Three.js.
   * // param: tidak ada.
   * // output: None.
   * // dipakai untuk: cleanup saat komponen di-unmount (SPA).
   */
  dispose() {
    this._clearScene();
    this.controls.dispose();
    this.renderer.dispose();
  }
}
