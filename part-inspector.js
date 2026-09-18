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
const SECTION_VIEW_DIR = new THREE.Vector3(-0.5, -0.38, -0.9).normalize(); // camera -> target, shared with framing

// Snap the shared view direction to its dominant world axis, so the cut
// reads as a clean straight section rather than a diagonal slice.
function axisSnappedNormal(dir) {
  const ax = Math.abs(dir.x), ay = Math.abs(dir.y), az = Math.abs(dir.z);
  if (az >= ax && az >= ay) return new THREE.Vector3(0, 0, Math.sign(dir.z) || 1);
  if (ax >= ay) return new THREE.Vector3(Math.sign(dir.x) || 1, 0, 0);
  return new THREE.Vector3(0, Math.sign(dir.y) || 1, 0);
}
const SECTION_PLANE_NORMAL = axisSnappedNormal(SECTION_VIEW_DIR);

const dialog = document.getElementById("inspect-dialog");
const canvas = document.getElementById("inspect-canvas");
const titleEl = document.getElementById("inspect-title");
const specsEl = document.getElementById("inspect-specs");
const closeBtn = document.getElementById("inspect-close");
const resetBtn = document.getElementById("inspect-reset");
const sectionBtn = document.getElementById("inspect-section");
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

let sectionOn = false;
let sectionBox = null; // THREE.Box3 of currentModel, set in open()
let sectionCenter = null; // screen-space-centered framing target, used as the cut plane's anchor
let sectionGroup = null; // THREE.Group: stencil-marking meshes + cap, added to scene when on
let sectionMarkMaterials = []; // cloned materials on the marking meshes, for disposal

const cache = new Map(); // url -> THREE.Group (loaded gltf.scene)
const loading = new Map(); // url -> Promise, so prefetch + open never double-fetch

function ensureScene() {
  if (renderer) return;
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, stencil: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.localClippingEnabled = true;

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

export async function open(url, label, specs, sectionable) {
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

  if (sectionBtn) sectionBtn.hidden = !sectionable;

  if (!dialog.open) dialog.showModal();
  document.body.classList.add("inspect-open");
  resize();

  teardownSection();
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
    sectionBox = box;
    const framing = frameBox(box, SECTION_VIEW_DIR, camera.fov, camera.aspect || 1, 1.5);
    sectionCenter = framing.target.clone();
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
  teardownSection();
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

function buildSectionGroup() {
  if (!currentModel || !sectionBox || !sectionCenter) return;
  currentModel.updateMatrixWorld(true);

  const center = sectionCenter;
  const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(SECTION_PLANE_NORMAL, center);

  const group = new THREE.Group();
  sectionMarkMaterials = [];

  currentModel.traverse((obj) => {
    if (!obj.isMesh) return;

    // Physically remove the near-side geometry from the real mesh.
    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    for (const m of mats) m.clippingPlanes = [plane];

    // Two stencil-marking clones per real mesh (standard clipping+stencil capping):
    // back faces increment, front faces decrement, leaving a non-zero count
    // wherever solid material crosses the plane.
    const baseMat = new THREE.MeshBasicMaterial({
      depthWrite: false, depthTest: false, colorWrite: false,
      stencilWrite: true, stencilFunc: THREE.AlwaysStencilFunc,
      clippingPlanes: [plane],
    });

    const backMat = baseMat.clone();
    backMat.side = THREE.BackSide;
    backMat.stencilFail = backMat.stencilZFail = backMat.stencilZPass = THREE.IncrementWrapStencilOp;
    const backMesh = new THREE.Mesh(obj.geometry, backMat);
    backMesh.matrix.copy(obj.matrixWorld);
    backMesh.matrixAutoUpdate = false;
    backMesh.renderOrder = 1;

    const frontMat = baseMat.clone();
    frontMat.side = THREE.FrontSide;
    frontMat.stencilFail = frontMat.stencilZFail = frontMat.stencilZPass = THREE.DecrementWrapStencilOp;
    const frontMesh = new THREE.Mesh(obj.geometry, frontMat);
    frontMesh.matrix.copy(obj.matrixWorld);
    frontMesh.matrixAutoUpdate = false;
    frontMesh.renderOrder = 1;

    group.add(backMesh, frontMesh);
    sectionMarkMaterials.push(backMat, frontMat);
  });

  // One capping disc, sized to comfortably cover the model, painted only
  // where the stencil count left by the marking meshes above is non-zero.
  const sphere = sectionBox.getBoundingSphere(new THREE.Sphere());
  const capGeom = new THREE.PlaneGeometry(sphere.radius * 2.5, sphere.radius * 2.5);
  const capMat = new THREE.MeshStandardMaterial({
    color: 0xb8bec8, side: THREE.DoubleSide, metalness: 0.15, roughness: 0.7,
    stencilWrite: true, stencilRef: 0, stencilFunc: THREE.NotEqualStencilFunc,
  });
  const capMesh = new THREE.Mesh(capGeom, capMat);
  capMesh.position.copy(center);
  capMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), SECTION_PLANE_NORMAL);
  capMesh.renderOrder = 2;
  capMesh.onAfterRender = (r) => r.clearStencil();
  group.add(capMesh);

  sectionGroup = group;
  scene.add(group);
}

function teardownSection() {
  if (currentModel) {
    currentModel.traverse((obj) => {
      if (!obj.isMesh) return;
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
      for (const m of mats) m.clippingPlanes = [];
    });
  }
  if (sectionGroup) {
    scene.remove(sectionGroup);
    for (const mat of sectionMarkMaterials) mat.dispose();
    sectionMarkMaterials = [];
    const cap = sectionGroup.children[sectionGroup.children.length - 1];
    cap.geometry.dispose();
    cap.material.dispose();
    sectionGroup = null;
  }
  sectionOn = false;
  sectionBtn?.classList.remove("active");
}

function setSectionOn(on) {
  if (on === sectionOn) return;
  if (on) {
    buildSectionGroup();
    sectionOn = true;
    sectionBtn?.classList.add("active");
  } else {
    teardownSection();
  }
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
  sectionBtn?.addEventListener("click", () => setSectionOn(!sectionOn));

  // Click on the backdrop (the dialog element itself, not its content) closes it.
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) close();
  });

  // Esc triggers the native 'cancel' -> 'close' sequence; run our own
  // cleanup on 'close' so it fires for every closing path uniformly.
  dialog.addEventListener("close", () => {
    teardownSection();
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
