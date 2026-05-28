import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import gsap from 'gsap';

// warna-warna utama yang dipakai untuk visualisasi
const COLORS = {
  bg:           0x07080f,
  chrNormal:    0x00d4ff,
  chrNd:        0xff4757,   // merah — kromosom non-target yang ND
  chrNdTarget:  0xff9500,   // oranye — kromosom TARGET yang ND
  chrNdMII:     0xff9f43,
  spindle:      0x7c3aed,
  spindleNd:    0xff4757,
  spindleNdTarget: 0xff9500,
  cellMembrane: 0x1a2035,
  nucleus:      0x0d1530,
  particle:     0x00d4ff,
  gamet:        0x2ed573,
  gametNd:      0xff4757,
  gametNdTarget: 0xff9500,
};

export class MeiosisScene {
  constructor(canvasEl) {
    this.canvas = canvasEl;
    this.animating = false;
    this.paused = false;
    this._objects = [];
    this._timeline = null;
    this._onStageChange = null;
    this._lastSimData = null;

    this._initRenderer();
    this._initScene();
    this._initCamera();
    this._initLights();
    this._initControls();
    this._initParticles();
    this._startRenderLoop();
    this._handleResize();
  }

  // setup renderer untuk Three.js
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

   // untuk membuat scene utama
  _initScene() {
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(COLORS.bg, 0.035);
  }

  // setup kamera
  _initCamera() {
    const aspect = this.canvas.clientWidth / this.canvas.clientHeight;
    this.camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 500);
    this.camera.position.set(0, 0, 20);
  }

  _initLights() {
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.3));

    const dir = new THREE.DirectionalLight(0xffffff, 0.8);
    dir.position.set(10, 20, 15);
    this.scene.add(dir);

    const bluePoint = new THREE.PointLight(COLORS.chrNormal, 2, 40);
    bluePoint.position.set(-8, 5, 0);
    this.scene.add(bluePoint);

    const purplePoint = new THREE.PointLight(COLORS.spindle, 1.5, 30);
    purplePoint.position.set(8, -5, 0);
    this.scene.add(purplePoint);
  }

  // orbit control agar kamera bisa diputar user
  _initControls() {
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.minDistance = 5;
    this.controls.maxDistance = 60;
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 0.3;
  }

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

  // untuk render loop utama
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

  // untuk membuat membran sel
  _makeCellMembrane(radius = 7, color = COLORS.cellMembrane, opacity = 0.25) {
    const geo = new THREE.SphereGeometry(radius, 32, 32);
    const mat = new THREE.MeshPhongMaterial({
      color,
      transparent: true,
      opacity,
      side: THREE.FrontSide,
    });
    const mesh = new THREE.Mesh(geo, mat);
    this._objects.push(mesh);
    return mesh;
  }

  // untuk membuat kromosom
  _makeChromosome(color = COLORS.chrNormal, length = 1.2, ndEffect = false) {
    const group = new THREE.Group();

    const geo = new THREE.CapsuleGeometry(0.12, length, 8, 16);
    const mat = new THREE.MeshPhongMaterial({
      color,
      emissive: color,
      emissiveIntensity: ndEffect ? 0.6 : 0.2,
      shininess: 80,
    });
    group.add(new THREE.Mesh(geo, mat));

    // glow aura khusus kromosom yang mengalami non-disjunction
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

  // membuat spindle fiber antar kutub sel
  _makeSpindleFiber(from, to, color = COLORS.spindle) {
    const dir = new THREE.Vector3().subVectors(to, from);
    const len = dir.length();
    const mid = new THREE.Vector3().addVectors(from, to).multiplyScalar(0.5);

    const geo = new THREE.CylinderGeometry(0.03, 0.03, len, 6);
    const mat = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.6 });
    const mesh = new THREE.Mesh(geo, mat);

    mesh.position.copy(mid);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());

    this._objects.push(mesh);
    return mesh;
  }

  // untuk menjalankan simulasi meiosis
  playSingleSimulation(simulationData) {
    this._lastSimData = simulationData;
    this._clearScene();
    this.controls.autoRotate = false;

    const hasND = simulationData.results.aneuploidCount > 0;
    const targetChr = simulationData.config?.targetChromosome ?? 21;
    const allSamples = simulationData.sampleGametes || [];

    // simpan kromosom yang mengalami non-disjunction
    const ndSet    = new Set();
    const ndMIISet = new Set();
    allSamples.forEach(g => {
      (g.affectedChromosomes || []).forEach(c => {
        ndSet.add(c.number);
        if (c.state === 'nd_mII') ndMIISet.add(c.number);
      });
    });

    const cellGroup = new THREE.Group();
    this.scene.add(cellGroup);

    const membrane = this._makeCellMembrane(6.5, COLORS.cellMembrane, 0.2);
    cellGroup.add(membrane);

    // membuat 23 kromosom
    const chrGroups = [];
    for (let i = 0; i < 23; i++) {
      const chrNum = i + 1;
      const angle  = (i / 23) * Math.PI * 2;
      const r      = 3.5;
      const isNd       = ndSet.has(chrNum);
      const isTarget   = chrNum === targetChr;
      const isMII      = ndMIISet.has(chrNum);

      let color;
      if (isNd && isTarget)  color = COLORS.chrNdTarget;
      else if (isNd && isMII) color = COLORS.chrNdMII;
      else if (isNd)         color = COLORS.chrNd;
      else                   color = COLORS.chrNormal;

      const chrG = this._makeChromosome(color, isTarget ? 1.1 : 0.9, isNd);
      chrG.position.set(
        Math.cos(angle) * r,
        Math.sin(angle) * r * 0.6,
        (Math.random() - 0.5) * 1.5
      );
      chrG.rotation.z = angle + Math.PI / 2;
      cellGroup.add(chrG);
      chrGroups.push(chrG);
    }

    const poleTop    = new THREE.Vector3(0,  6, 0);
    const poleBottom = new THREE.Vector3(0, -6, 0);
    const spindleGroup = new THREE.Group();
    spindleGroup.visible = false;
    this.scene.add(spindleGroup);

    chrGroups.forEach((cg, cgIdx) => {
      const chrNum   = cgIdx + 1;
      const isNd     = ndSet.has(chrNum);
      const isTarget = chrNum === targetChr;
      const fiberColor = isNd
        ? (isTarget ? COLORS.spindleNdTarget : COLORS.spindleNd)
        : COLORS.spindle;
      spindleGroup.add(
        this._makeSpindleFiber(cg.position, poleTop, fiberColor),
        this._makeSpindleFiber(cg.position, poleBottom, fiberColor)
      );
    });

    const tl = gsap.timeline({ defaults: { ease: 'power2.inOut' } });
    this._timeline = tl;

    // interfase
    tl.addLabel('interphase');
    tl.call(() => this._setStage('interphase'));

    // profase
    tl.addLabel('prophase', '+=1.5');
    tl.call(() => this._setStage('prophase'), null, 'prophase');
    tl.to(cellGroup.rotation, { y: Math.PI * 0.5, duration: 2 }, 'prophase');

    // metafase
    tl.addLabel('metaphase', '+=0.8');
    tl.call(() => {
      this._setStage('metaphase');
      spindleGroup.visible = true;
    }, null, 'metaphase');
    chrGroups.forEach((cg) => {
      tl.to(cg.position, {
        x: (Math.random() - 0.5) * 1.5,
        y: (Math.random() - 0.5) * 0.4,
        z: (Math.random() - 0.5) * 1.5,
        duration: 1.2,
      }, 'metaphase+=0.05');
    });

    // anafase
    tl.addLabel('anaphase', '+=0.5');
    tl.call(() => this._setStage('anaphase'), null, 'anaphase');
    chrGroups.forEach((cg, i) => {
      const chrNum = i + 1;
      const isNd   = ndSet.has(chrNum) && hasND;
      const targetY = (i % 2 === 0) ? 4.5 : -4.5;

      if (isNd) {
        tl.to(cg.position, { y: (Math.random() - 0.5) * 0.5, duration: 1.5 }, 'anaphase+=0.03');
        tl.to(cg.children[0].material, {
          emissiveIntensity: 1.0, duration: 0.3, yoyo: true,
          repeat: chrNum === targetChr ? 8 : 4,
        }, 'anaphase');
      } else {
        tl.to(cg.position, { y: targetY, duration: 1.5 }, 'anaphase+=0.03');
      }
    });

    // Meiosis II
    tl.addLabel('meiosis2', '+=0.3');
    tl.call(() => this._setStage('meiosis2'), null, 'meiosis2');
    tl.to(membrane.scale, { x: 0.5, y: 0.5, z: 0.5, duration: 1.0 }, 'meiosis2');

    // pembentukan gamete
    tl.addLabel('gametes', '+=0.5');
    tl.call(() => {
      this._setStage('gametes');
      spindleGroup.visible = false;
      this._showGametes(simulationData);
    }, null, 'gametes');

    tl.call(() => { this.controls.autoRotate = true; }, null, '+=1');
  }

  // menampilkan gamete hasil meiosis
  _showGametes(simData) {
    this._clearScene();
    const targetChr     = simData.config?.targetChromosome ?? 21;
    const sampleGametes = simData.sampleGametes || [];
    const aneuploidItems = sampleGametes.map(g => ({ isAneuploid: true, gamete: g }));
    const normalCount    = Math.max(1, 8 - aneuploidItems.length);
    const items = [
      ...aneuploidItems,
      ...Array.from({ length: normalCount }, () => ({ isAneuploid: false, gamete: null })),
    ];
    const displayCount = items.length;

    const radius = 5;
    items.forEach((item, i) => {
      const angle = (i / displayCount) * Math.PI * 2;

      // menentukan warna gamete berdasarkan kondisi kromosom
      let color = COLORS.gamet;
      if (item.isAneuploid && item.gamete) {
        const affected  = item.gamete.affectedChromosomes || [];
        const targetHit = affected.some(c => c.number === targetChr);
        const hasMII    = affected.some(c => c.state === 'nd_mII');
        if (targetHit)   color = COLORS.gametNdTarget;
        else if (hasMII) color = COLORS.chrNdMII;
        else             color = COLORS.gametNd;
      }

      const size = item.isAneuploid ? 0.8 : 0.65;
      const geo  = new THREE.SphereGeometry(size, 20, 20);
      const mat  = new THREE.MeshPhongMaterial({
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

      sphere.scale.set(0, 0, 0);
      gsap.to(sphere.scale, {
        x: 1, y: 1, z: 1,
        duration: 0.6,
        delay: i * 0.08,
        ease: 'back.out(1.5)',
      });

      if (item.isAneuploid) {
        gsap.to(mat, {
          emissiveIntensity: 0.9,
          duration: 0.5,
          yoyo: true,
          repeat: -1,
          ease: 'sine.inOut',
        });
      }
    });
  }

  // untuk membersihkan objek dari scene
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

  // update stage meiosis
  _setStage(stageName) {
    if (typeof this._onStageChange === 'function') {
      this._onStageChange(stageName);
    }
  }

  onStageChange(callback) {
    this._onStageChange = callback;
  }

  // untuk melihat stage tertentu
  seekToStage(stageName) {
    if (!this._lastSimData) return;
    this.paused = false;
    this.playSingleSimulation(this._lastSimData);
    if (stageName !== 'interphase') {
      this._timeline.seek(stageName, false);
    }
  }

  hasSimulation() {
    return this._lastSimData !== null;
  }

  togglePause() {
    this.paused = !this.paused;
    if (this._timeline) {
      this.paused ? this._timeline.pause() : this._timeline.resume();
    }
    return this.paused;
  }

  // resize canvas
  _handleResize() {
    window.addEventListener('resize', () => {
      const w = this.canvas.clientWidth;
      const h = this.canvas.clientHeight;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h);
    });
  }

  dispose() {
    this._clearScene();
    this.controls.dispose();
    this.renderer.dispose();
  }
}