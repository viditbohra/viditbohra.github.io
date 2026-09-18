// Full-screen dialog for freely orbiting a single component's own GLB.
// Deliberately separate from case-study.js's scroll-driven camera: drag and
// scroll are the same gesture on trackpad/touch, so free orbit and the
// scripted scroll camera can never share one canvas without fighting each
// other. Splitting them into two modes (browse the story / inspect a part)
// removes the conflict instead of trying to arbitrate it.

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { frameBox } from "./frame-box.js";

const REDUCE = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const ORBIT_STEP = 0.08; // radians per arrow-key press
const ZOOM_STEP = 0.12; // fraction of distance per +/- press

const dialog = document.getElementById("inspect-dialog");
const canvas = document.getElementById("inspect-canvas");
const titleEl = document.getElementById("inspect-title");
const specsEl = document.getElementById("inspect-specs");
const closeBtn = document.getElementById("inspect-close");
const resetBtn = document.getElementById("inspect-reset");
const progressEl = document.getElementById("inspect-progress");

if (!dialog) {
  // Page has no inspector markup (older cached build, or a page that
  // doesn't use this feature) - nothing to wire up.
  console.warn("part-inspector: #inspect-dialog not found, skipping init");
}

let renderer = null;
let scene = null;
let camera = null;
let controls = null;
let currentModel = null;
let loadToken = 0;
let openInitial = null; // { position, target } for Reset
let userInteracted = false;
let rafId = null;

const cache = new Map(); // url -> THREE.Group (loaded gltf.scene)
const loading = new Map(); // url -> Promise, so prefetch + open never double-fetch

function ensureScene() {
  if (renderer) return;
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(32, 1, 0.01, 100);

  scene.add(new THREE.HemisphereLight(0x9098a8, 0x151310, 1.6));
  const key = new THREE.DirectionalLight(0xfff3e0, 2.2);
  key.position.set(3, 5, 4);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x6f8cff, 0.6);
  rim.position.set(-4, 2, -3);
  scene.add(rim);

  controls = new OrbitControls(camera, canvas);
  controls.enablePan = false;
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.autoRotate = !REDUCE;
  controls.autoRotateSpeed = 1.1;
  controls.addEventListener("start", () => {
    userInteracted = true;
    controls.autoRotate = false;
  });

  new ResizeObserver(resize).observe(canvas);
}

function resize() {
  if (!renderer) return;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (!w || !h) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

function loadModel(url) {
  if (cache.has(url)) return Promise.resolve(cache.get(url));
  if (loading.has(url)) return loading.get(url);

  const promise = new Promise((resolve, reject) => {
    new GLTFLoader().load(
      url,
      (gltf) => {
        cache.set(url, gltf.scene);
        loading.delete(url);
        resolve(gltf.scene);
      },
      (evt) => {
        if (evt.lengthComputable) {
          const mb = (n) => (n / 1024 / 1024).toFixed(1);
          setProgress(`${mb(evt.loaded)} / ${mb(evt.total)} MB`);
        } else {
          setProgress("Loading...");
        }
      },
      (err) => {
        loading.delete(url);
        reject(err);
      },
    );
  });
  loading.set(url, promise);
  return promise;
}

function setProgress(text) {
  if (progressEl) progressEl.textContent = text;
}

// Called ahead of time (chapter becomes active) so a click usually has
// nothing left to wait for. Silently ignored on slow/metered connections.
export function prefetch(url) {
  if (!url || cache.has(url) || loading.has(url)) return;
  const conn = navigator.connection;
  if (conn && (conn.saveData || /^(slow-2g|2g|3g)$/.test(conn.effectiveType || ""))) return;
  loadModel(url).catch(() => {});
}

export async function open(url, label, specs) {
  if (!dialog || !url) return;
  ensureScene();

  loadToken += 1;
  const myToken = loadToken;
  userInteracted = false;
  setProgress("");

  titleEl.textContent = label || "Part";
  specsEl.innerHTML = (specs || [])
    .map(([k, v]) => `<div class="inspect-spec-row"><span>${k}</span><b>${v}</b></div>`)
    .join("");

  if (!dialog.open) dialog.showModal();
  document.body.classList.add("inspect-open");
  resize();

  if (currentModel) {
    scene.remove(currentModel);
    currentModel = null;
  }

  try {
    const model = await loadModel(url);
    if (myToken !== loadToken) return; // dialog closed (or reopened) before this landed
    setProgress("");
    currentModel = model;
    scene.add(model);

    const box = new THREE.Box3().setFromObject(model);
    const viewDir = new THREE.Vector3(-0.5, -0.38, -0.9);
    const framing = frameBox(box, viewDir, camera.fov, camera.aspect || 1, 1.5);
    openInitial = framing;
    camera.position.copy(framing.position);
    controls.target.copy(framing.target);
    controls.update();
    controls.autoRotate = !REDUCE;

    animate();
  } catch (err) {
    if (myToken !== loadToken) return;
    setProgress("Couldn't load this part.");
    console.error("part-inspector: load failed", url, err);
  }
}

export function close() {
  if (!dialog) return;
  loadToken += 1; // invalidate any in-flight load
  if (dialog.open) dialog.close();
  document.body.classList.remove("inspect-open");
  if (rafId) cancelAnimationFrame(rafId);
  rafId = null;
}

function resetView() {
  if (!openInitial) return;
  userInteracted = false;
  camera.position.copy(openInitial.position);
  controls.target.copy(openInitial.target);
  controls.autoRotate = !REDUCE;
  controls.update();
}

function orbitBy(deltaAzimuth, deltaPolar) {
  const offset = camera.position.clone().sub(controls.target);
  const spherical = new THREE.Spherical().setFromVector3(offset);
  spherical.theta += deltaAzimuth;
  spherical.phi = THREE.MathUtils.clamp(spherical.phi + deltaPolar, 0.05, Math.PI - 0.05);
  offset.setFromSpherical(spherical);
  camera.position.copy(controls.target).add(offset);
  controls.autoRotate = false;
  userInteracted = true;
  controls.update();
}

function zoomBy(factor) {
  const offset = camera.position.clone().sub(controls.target);
  offset.multiplyScalar(factor);
  camera.position.copy(controls.target).add(offset);
  controls.update();
}

function animate() {
  rafId = requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

if (dialog) {
  closeBtn?.addEventListener("click", close);
  resetBtn?.addEventListener("click", resetView);

  // Click on the backdrop (the dialog element itself, not its content) closes it.
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) close();
  });

  // Esc triggers the native 'cancel' -> 'close' sequence; run our own
  // cleanup on 'close' so it fires for every closing path uniformly.
  dialog.addEventListener("close", () => {
    document.body.classList.remove("inspect-open");
    loadToken += 1;
    if (rafId) cancelAnimationFrame(rafId);
    rafId = null;
  });

  dialog.addEventListener("keydown", (e) => {
    if (!dialog.open) return;
    switch (e.key) {
      case "ArrowLeft": orbitBy(-ORBIT_STEP, 0); e.preventDefault(); break;
      case "ArrowRight": orbitBy(ORBIT_STEP, 0); e.preventDefault(); break;
      case "ArrowUp": orbitBy(0, -ORBIT_STEP); e.preventDefault(); break;
      case "ArrowDown": orbitBy(0, ORBIT_STEP); e.preventDefault(); break;
      case "+": case "=": zoomBy(1 - ZOOM_STEP); e.preventDefault(); break;
      case "-": case "_": zoomBy(1 + ZOOM_STEP); e.preventDefault(); break;
    }
  });
}
