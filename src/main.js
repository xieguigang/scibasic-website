/* ============================================================
 *  sciBASIC# hero — two full-screen three.js scenes
 *  S1: sine-ripple particle field  z = sin(sqrt(x²+y²) − t)
 *  S2: Penrose-triangle knot (traced from logo-knot.png)
 *  Wheel / swipe switches screens · drag orbits the view
 * ============================================================ */
import * as THREE from 'three';

const BG = 0x030303;

/* ---------------- shared helpers ---------------- */

function makeRenderer(canvas) {
  const r = new THREE.WebGLRenderer({ canvas, antialias: true });
  r.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
  r.setSize(window.innerWidth, window.innerHeight);
  r.setClearColor(BG, 1);
  r.toneMapping = THREE.ACESFilmicToneMapping;
  r.toneMappingExposure = 1.12;
  return r;
}

function glowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grad.addColorStop(0, 'rgba(255,255,255,.9)');
  grad.addColorStop(0.18, 'rgba(255,255,255,.32)');
  grad.addColorStop(0.5, 'rgba(255,255,255,.10)');
  grad.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  return new THREE.CanvasTexture(c);
}

function addLights(scene) {
  scene.add(new THREE.AmbientLight(0xffffff, 0.15));
  const key = new THREE.PointLight(0xffffff, 230, 0, 2);
  key.position.set(-2.2, 8.2, 3.0);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x9aa7bd, 0.38);
  rim.position.set(4, 3, -6);
  scene.add(rim);
}

/* mouse-driven orbit: drag to rotate, subtle parallax when idle.
 * Rotates the CAMERA on a spherical rail (group stays world-aligned,
 * lighting stays consistent). Vertical touch swipes are reserved for
 * page switching and never reach the orbit. */
class Orbit {
  /* NOTE: the parallax *factor* is stored as parScale — naming it
   * `this.parallax` would shadow the parallax() method on the prototype
   * and explode every mousemove ("parallax is not a function"). */
  constructor(dom, { polar = [0.55, 1.35], az = [-1.2, 1.2], basePolar = 1.06, baseAz = 0, parallaxScale = 0.075 } = {}) {
    this.dom = dom;
    this.az = baseAz; this.pol = basePolar;
    this.tAz = baseAz; this.tPol = basePolar;
    this.clamp = { polar, az };
    this.parScale = parallaxScale;
    this.dragging = false; this.px = 0; this.py = 0;
    this.parX = 0; this.parY = 0;

    dom.style.cursor = 'grab';
    dom.addEventListener('pointerdown', (e) => {
      this.dragging = true; this.px = e.clientX; this.py = e.clientY;
      dom.style.cursor = 'grabbing';
      try { dom.setPointerCapture(e.pointerId); } catch (_) {}
    });
    dom.addEventListener('pointermove', (e) => {
      if (!this.dragging) return;
      /* vertical touch drags belong to page switching */
      if (e.pointerType === 'touch' && window.__touchAxis === 'page') return;
      const dx = e.clientX - this.px, dy = e.clientY - this.py;
      this.px = e.clientX; this.py = e.clientY;
      this.tAz += dx * 0.0042;
      this.tPol -= dy * 0.0032;
      this._clampTargets();
    });
    const up = () => { this.dragging = false; dom.style.cursor = 'grab'; };
    dom.addEventListener('pointerup', up);
    dom.addEventListener('pointercancel', up);
  }
  _clampTargets() {
    this.tAz = Math.max(this.clamp.az[0], Math.min(this.clamp.az[1], this.tAz));
    this.tPol = Math.max(this.clamp.polar[0], Math.min(this.clamp.polar[1], this.tPol));
  }
  parallax(nx, ny) { this.parX = nx; this.parY = ny; }
  update(dt) {
    const k = 1 - Math.exp(-dt * 5.5);
    this.az += (this.tAz + this.parX * this.parScale - this.az) * k;
    this.pol += (this.tPol - this.parY * this.parScale * 0.7 - this.pol) * k;
  }
}

/* ---------------- SCREEN 1 · sine-ripple particle field ---------------- */

function buildWave() {
  const canvas = document.getElementById('waveCanvas');
  const renderer = makeRenderer(canvas);
  renderer.toneMappingExposure = 0.98;
  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(BG, 20, 40);
  const camera = new THREE.PerspectiveCamera(38, window.innerWidth / window.innerHeight, 0.1, 80);

  const group = new THREE.Group();
  scene.add(group);

  /* 80 × 80 grid over [-8, 8]² */
  const N = 80, SPAN = 16, SP = SPAN / (N - 1);
  const COUNT = N * N;
  const geom = new THREE.SphereGeometry(0.08, 6, 4);
  const mat = new THREE.MeshStandardMaterial({ color: 0xc9c9c9, roughness: 0.55, metalness: 0.06 });
  const mesh = new THREE.InstancedMesh(geom, mat, COUNT);
  mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  group.add(mesh);

  const baseX = new Float32Array(COUNT), baseZ = new Float32Array(COUNT);
  for (let i = 0; i < N; i++) {
    for (let j = 0; j < N; j++) {
      const k = i * N + j;
      baseX[k] = -SPAN / 2 + i * SP;
      baseZ[k] = -SPAN / 2 + j * SP;
    }
  }

  /* z(x,y,t) = sin(sqrt(x²+y²) − t) with breathing swell + secondary ripples */
  function waveH(x, y, t) {
    const r = Math.sqrt(x * x + y * y);
    const swell = 0.42 + 0.38 * Math.pow(Math.sin(t * 0.36), 2);
    let h = Math.sin(r * 1.02 - t * 1.05) * swell;
    h += Math.sin(r * 1.9 - t * 1.55 + 1.7) * 0.10;
    h += 0.34 * Math.exp(-r * 0.16) * (0.5 + 0.5 * Math.sin(t * 0.47));
    h += Math.sin(x * 1.7 + t * 1.1) * Math.cos(y * 1.5 - t * 0.8) * 0.035;
    return h;
  }

  const M = new THREE.Matrix4();

  function updateWave(t) {
    const a = mesh.instanceMatrix.array;
    let o = 0;
    for (let k = 0; k < COUNT; k++) {
      const x = baseX[k], z = baseZ[k];
      /* write the translation column directly into the instance buffer */
      a[o + 12] = x;
      a[o + 13] = waveH(x, z, t);
      a[o + 14] = z;
      o += 16;
    }
    mesh.instanceMatrix.needsUpdate = true;
  }

  addLights(scene);

  const glow = new THREE.Sprite(new THREE.SpriteMaterial({
    map: glowTexture(), transparent: true, opacity: 0.4,
    blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false
  }));
  glow.scale.set(4.2, 4.2, 1);
  glow.position.set(-3.6, 2.1, 0.5);
  scene.add(glow);

  const orbit = new Orbit(canvas, {
    polar: [0.7, 1.35], az: [-1.25, 1.25], basePolar: 1.24, baseAz: 0
  });

  function resize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  function render(t, dt) {
    updateWave(t);
    glow.material.opacity = 0.3 + 0.1 * Math.sin(t * 0.8);
    orbit.update(dt);
    /* camera on spherical rail around the field */
    const R = 24;
    camera.position.set(
      Math.sin(orbit.az) * Math.sin(orbit.pol) * R,
      Math.cos(orbit.pol) * R + 0.4,
      Math.cos(orbit.az) * Math.sin(orbit.pol) * R
    );
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
  }

  return { render, resize, orbit };
}

/* ---------------- SCREEN 2 · Penrose knot ----------------
 * Integrated from the author's own code.html: three square-section
 * beams placed so the assembly is three-fold rotationally symmetric
 * about the (1,1,1) axis. Its orthographic projection along that axis
 * is a closed triangle at ANY roll angle — so trackIllusion() points
 * the (1,1,1) axis back at the camera every frame and the user may
 * orbit freely without the loop ever opening. Unlock reveals the
 * broken truth. Material stays V3's matte gray-white; sharp-edged
 * BoxGeometry, no rounded bevels. */
function buildKnot() {
  const canvas = document.getElementById('knotCanvas');
  const renderer = makeRenderer(canvas);
  const scene = new THREE.Scene();
  /* orthographic — same projection family as the VB IsometricEngine */
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 300);
  const DIST = 60;
  const BEST_AZ = Math.PI / 4;                 // canonical view: dir (1,1,1)/√3
  const BEST_POL = Math.acos(1 / Math.sqrt(3));

  function setFrustum() {
    const aspect = window.innerWidth / window.innerHeight;
    const halfH = Math.max(9.5, 8.2 / aspect);
    camera.left = -halfH * aspect; camera.right = halfH * aspect;
    camera.top = halfH; camera.bottom = -halfH;
    /* principal-point shift: knot left-of-center, text right — the view
     * direction through the model is untouched, the loop stays closed */
    camera.setViewOffset(window.innerWidth, window.innerHeight,
      Math.round(window.innerWidth * 0.17), 0,
      window.innerWidth, window.innerHeight);
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  /* ---------- the Knot: three beams, 3-fold symmetric about (1,1,1) ---------- */
  const T = 2.2, RHO = 0.32;
  const LEN = Math.sqrt(3) * T / RHO;
  const A = (LEN - 1.5 * T) / 3;
  const K = A + T / 2;

  const cx = new THREE.Vector3(LEN / 2, A + T / 2, A + K + T / 2);
  const cy = new THREE.Vector3(A + K + T / 2, LEN / 2, A + T / 2);
  const cz = new THREE.Vector3(A + T / 2, A + K + T / 2, LEN / 2);
  const centroid = cx.clone().add(cy).add(cz).multiplyScalar(1 / 3);

  /* V3 matte gray-white material; sharp edges, no rounding */
  const mat = new THREE.MeshStandardMaterial({ color: 0xd9d9d9, roughness: 0.42, metalness: 0.14 });

  const group = new THREE.Group();
  const dims = [[LEN, T, T], [T, LEN, T], [T, T, LEN]];
  const centers = [cx, cy, cz];
  for (let i = 0; i < 3; i++) {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(dims[i][0], dims[i][1], dims[i][2]), mat);
    mesh.position.copy(centers[i]).sub(centroid);
    group.add(mesh);
  }

  /* illusion lock: aim the (1,1,1) axis at the view direction every frame
   * + a fixed 30° roll; damped slerp turns switches into a graceful "close" */
  const AXIS = new THREE.Vector3(1, 1, 1).normalize();
  const ROLL = new THREE.Quaternion().setFromAxisAngle(AXIS, Math.PI / 6);
  group.quaternion.copy(ROLL);          // entrance pose: static, still "broken"
  scene.add(group);

  let illusionLock = true, autoSpin = false, entered = false, flight = null;
  const _toward = new THREE.Vector3();
  const _qAlign = new THREE.Quaternion();
  const _qTarget = new THREE.Quaternion();

  function trackIllusion(dt) {
    camera.getWorldDirection(_toward);       // where the camera looks
    _toward.negate().normalize();            // scene → camera
    _qAlign.setFromUnitVectors(AXIS, _toward);
    _qTarget.copy(_qAlign).multiply(ROLL);   // align + fixed roll
    const s = 1 - Math.exp(-dt * 10);        // frame-rate independent
    group.quaternion.slerp(_qTarget, s);
  }

  /* world-fixed lights: as the model tracks the camera, shading flows.
   * Ambient kept low — ACES tonemapping already compresses highlights,
   * and the three-facet gray read needs directional contrast. */
  scene.add(new THREE.AmbientLight(0xffffff, 0.32));
  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(8, 14, 6);
  const fill = new THREE.DirectionalLight(0xffffff, 0.45);
  fill.position.set(-9, 2, 5);
  const rim = new THREE.DirectionalLight(0xffffff, 0.5);
  rim.position.set(1, -9, 9);
  scene.add(key, fill, rim);

  /* dust — same particle language as screen 1 */
  const DN = 220;
  const dpos = new Float32Array(DN * 3);
  for (let i = 0; i < DN; i++) {
    const r = 10 + Math.random() * 12;
    const th = Math.random() * Math.PI * 2;
    dpos[i * 3] = Math.cos(th) * r;
    dpos[i * 3 + 1] = (Math.random() - 0.5) * 16;
    dpos[i * 3 + 2] = Math.sin(th) * r;
  }
  const dgeo = new THREE.BufferGeometry();
  dgeo.setAttribute('position', new THREE.BufferAttribute(dpos, 3));
  const dust = new THREE.Points(dgeo, new THREE.PointsMaterial({
    color: 0x9a9a9a, size: 2.4, transparent: true, opacity: 0.5,
    sizeAttenuation: false, depthWrite: false
  }));
  scene.add(dust);

  const glow = new THREE.Sprite(new THREE.SpriteMaterial({
    map: glowTexture(), transparent: true, opacity: 0.3,
    blending: THREE.AdditiveBlending, depthWrite: false
  }));
  glow.scale.set(16, 16, 1);
  glow.position.set(-11, 4, -9);
  scene.add(glow);

  /* free orbit — the tracking keeps the loop closed from any direction */
  const orbit = new Orbit(canvas, {
    polar: [0.15, Math.PI - 0.15], az: [-Math.PI, Math.PI],
    basePolar: BEST_POL, baseAz: BEST_AZ,
    parallaxScale: 0.015
  });

  const easeOutQuart = x => 1 - Math.pow(1 - x, 4);
  const easeInOut = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;

  function flyToBest(dur, ease) {
    flight = { t0: performance.now(), dur, ease,
      az0: orbit.az, pol0: orbit.pol, az1: BEST_AZ, pol1: BEST_POL };
    if (autoSpin) { autoSpin = false; btnSpin.classList.remove('active'); }
  }
  function stepFlight(now) {
    const a = Math.min(1, (now - flight.t0) / flight.dur);
    const e = flight.ease(a);
    orbit.az = orbit.tAz = flight.az0 + (flight.az1 - flight.az0) * e;
    orbit.pol = orbit.tPol = flight.pol0 + (flight.pol1 - flight.pol0) * e;
    if (a >= 1) flight = null;
  }

  /* entrance: fly in from an off angle while the model is still static —
   * the broken truth shows first, then it "closes" as the lock engages */
  function beginEntrance() {
    if (entered) return;
    entered = true;
    orbit.az = orbit.tAz = BEST_AZ + 0.95;
    orbit.pol = orbit.tPol = BEST_POL - 0.42;
    flight = { t0: performance.now(), dur: 2600, ease: easeOutQuart,
      az0: orbit.az, pol0: orbit.pol, az1: BEST_AZ, pol1: BEST_POL };
  }
  canvas.addEventListener('pointerdown', () => { if (flight) flight = null; });
  canvas.addEventListener('dblclick', () => { if (!flight) flyToBest(900, easeInOut); });

  /* panel buttons */
  const btnLock = document.getElementById('kBtnLock');
  const btnFront = document.getElementById('kBtnFront');
  const btnSpin = document.getElementById('kBtnSpin');
  btnLock.addEventListener('click', () => {
    illusionLock = !illusionLock;
    btnLock.classList.toggle('active', illusionLock);
  });
  btnFront.addEventListener('click', () => { if (!flight) flyToBest(900, easeInOut); });
  btnSpin.addEventListener('click', () => {
    autoSpin = !autoSpin;
    btnSpin.classList.toggle('active', autoSpin);
  });

  function resize() { setFrustum(); }
  setFrustum();   // initial frustum — the constructor default (±1) shows nothing

  function render(t, dt) {
    dust.rotation.y = t * 0.02;
    if (flight) stepFlight(performance.now());
    else {
      if (autoSpin && !orbit.dragging) orbit.tAz += dt * 0.22;
      orbit.update(dt);
    }
    if (illusionLock && !flight) trackIllusion(dt);   // always closed
    camera.position.set(
      Math.sin(orbit.az) * Math.sin(orbit.pol) * DIST,
      Math.cos(orbit.pol) * DIST,
      Math.cos(orbit.az) * Math.sin(orbit.pol) * DIST
    );
    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);
  }

  return { render, resize, beginEntrance, orbit };
}

/* ---------------- page orchestration ---------------- */

const viewport = document.getElementById('viewport');
const screens = [document.getElementById('s1'), document.getElementById('s2')];
let screen = 0, lock = false;

function go(n) {
  n = Math.max(0, Math.min(1, n));
  if (n === screen || lock) return;
  lock = true;
  screen = n;
  viewport.style.transform = `translateY(${-n * window.innerHeight}px)`;
  screens[0].classList.toggle('is-active', n === 0);
  screens[1].classList.toggle('is-active', n === 1);
  if (n === 1) knot.beginEntrance();   // fly in + close-up on first visit
  setTimeout(() => { lock = false; }, 1150);
}

/* wheel — accumulate to survive trackpad inertia */
let acc = 0, accTimer = null;
window.addEventListener('wheel', (e) => {
  if (lock) return;
  acc += e.deltaY;
  clearTimeout(accTimer);
  accTimer = setTimeout(() => { acc = 0; }, 250);
  if (acc > 60) { acc = 0; go(screen + 1); }
  else if (acc < -60) { acc = 0; go(screen - 1); }
}, { passive: true });

/* touch swipe (vertical) = page switch · horizontal drag = orbit */
let tX = 0, tY = 0, swipe = null;
window.addEventListener('pointerdown', (e) => {
  if (e.pointerType !== 'touch') return;
  tX = e.clientX; tY = e.clientY; swipe = null;
  window.__touchAxis = null;
});
window.addEventListener('pointermove', (e) => {
  if (e.pointerType !== 'touch') return;
  const dx = e.clientX - tX, dy = e.clientY - tY;
  if (window.__touchAxis === null && (Math.abs(dx) > 14 || Math.abs(dy) > 14)) {
    window.__touchAxis = Math.abs(dx) > Math.abs(dy) ? 'orbit' : 'page';
  }
});
window.addEventListener('pointerup', (e) => {
  if (e.pointerType !== 'touch') return;
  const dy = e.clientY - tY;
  if (window.__touchAxis === 'page' && Math.abs(dy) > 60) go(screen + (dy < 0 ? 1 : -1));
});

/* keyboard */
window.addEventListener('keydown', (e) => {
  if (['ArrowDown', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); go(screen + 1); }
  if (['ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); go(screen - 1); }
});

/* hero headline carousel */
const slides = [...document.querySelectorAll('#s1 .slide')];
const dots = [...document.querySelectorAll('#heroDots i')];
let cur = 0, cyc = null;
function showSlide(i) {
  cur = i;
  slides.forEach((s, k) => s.classList.toggle('active', k === i));
  dots.forEach((d, k) => d.classList.toggle('on', k === i));
}
function cycle() { clearInterval(cyc); cyc = setInterval(() => showSlide((cur + 1) % slides.length), 7500); }
dots.forEach((d, k) => d.addEventListener('click', () => { showSlide(k); cycle(); }));
cycle();

/* menu overlay */
document.getElementById('menuBtn').addEventListener('click', () => {
  document.body.classList.toggle('menu-open');
});
document.querySelectorAll('.menu-overlay a').forEach(a =>
  a.addEventListener('click', () => document.body.classList.remove('menu-open')));

/* ---------------- main loop ---------------- */

const wave = buildWave();
const knot = buildKnot();
window.__siteReady = true;
document.body.classList.add('ready');

window.addEventListener('mousemove', (e) => {
  const nx = (e.clientX / window.innerWidth) * 2 - 1;
  const ny = (e.clientY / window.innerHeight) * 2 - 1;
  wave.orbit.parallax(nx, ny);
  knot.orbit.parallax(nx, ny);
});

window.addEventListener('resize', () => {
  wave.resize(); knot.resize();
  viewport.style.transform = `translateY(${-screen * window.innerHeight}px)`;
});

let last = performance.now();
function tick(now) {
  const dt = Math.min((now - last) / 1000, 0.05);
  last = now;
  const t = now / 1000;
  if (screen === 0 || lock) wave.render(t, dt);
  if (screen === 1 || lock) knot.render(t, dt);
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
