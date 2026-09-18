// Continuous scroll-driven camera for the Mars Rover Arm case study.
// Ported from scroll-sync-demo.html's update() pattern to a real three.js
// scene instead of the SVG line-art stand-in it demonstrated the mechanic with.

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { frameBox } from "./frame-box.js";
import * as inspector from "./part-inspector.js";

const REDUCE = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const MECHANISMS = ["Linear base", "Shoulder", "Elbow", "Wrist", "Gripper"];

const KEYWORDS = {
  "Linear base": ["linear_base", "mgn9", "rail2", "lift_the_rail", "side_plate", "side_top_plate_hub",
                   "top_cylinder", "to_connect_5mm_spacers", "for_the_other_bearing_raiser",
                   "bearing_heigh_inc", "please_let_this_be_the_final_mount", "new_block",
                   "fake_ball_screw", "motor_plate"],
  "Shoulder": ["shoulder", "gear_assembly", "gears", "stage_1", "stage_2", "gear_holder"],
  "Elbow": ["elbow", "8coupler", "coupler_assem", "collar", "hyper_hub_d", "6d"],
  "Wrist": ["worm", "cant_make_it_any_smaller", "differential"],
  "Gripper": ["gripper", "jaw", "gripping_assembly", "camera_holder", "link_atacher", "restrictor"],
};

function classifyByName(name) {
  const low = name.toLowerCase();
  for (const [bucket, kws] of Object.entries(KEYWORDS)) {
    for (const kw of kws) if (low.includes(kw)) return bucket;
  }
  return null;
}

const HUD = {
  "Linear base": { title: "Linear base", rows: [["Rails", "2× MGN9H"], ["Drive", "Trapezoidal lead screw"], ["Adjustment", "7–8 mm"]] },
  "Shoulder": { title: "Shoulder", rows: [["Reduction", "81:1, 2-stage cycloidal"], ["Torque", "160 Nm"], ["Brake", "Fail-safe electromagnetic"]] },
  "Elbow": { title: "Elbow", rows: [["Reduction", "34:1, single-stage"], ["Torque", "65 Nm"]] },
  "Wrist": { title: "Differential wrist", rows: [["DOF", "2, differential"], ["Anti-backdrive", "Worm stage"], ["Mass", "−35% (v2, printed)"]] },
  "Gripper": { title: "Gripper", rows: [["Drive", "N20 motor + lead screw"], ["Control", "Wireless (ESP32)"]] },
};

const canvas = document.getElementById("stage-canvas");
const stageWrap = document.querySelector(".stage-wrap");
const chaptersEl = document.getElementById("chapters");
const progNum = document.getElementById("prog-num");
const progName = document.getElementById("prog-name");
const hud = document.getElementById("stage-hud");
const inspectBtn = document.getElementById("inspect-btn");
const inspectBtnLabel = inspectBtn?.querySelector(".inspect-btn-label");

// Per-mechanism part metadata (model URL, byte size, human label), read
// straight off each chapter section rather than duplicated into JS - the
// HTML built by build_case_study_chapter() is the source of truth.
const PARTS = {};
document.querySelectorAll(".chapter[data-mech]").forEach((el) => {
  if (!el.dataset.partModel) return;
  PARTS[el.dataset.mech] = {
    url: el.dataset.partModel,
    bytes: Number(el.dataset.partBytes) || 0,
    label: el.dataset.partLabel || el.dataset.mech,
    sectionable: el.dataset.partSectionable === "1",
  };
});

let activePart = null;

function formatMB(bytes) {
  return bytes ? `${(bytes / 1024 / 1024).toFixed(0)} MB` : "";
}

function updateInspectButton(mechName) {
  const part = PARTS[mechName] || null;
  if (part === activePart) return;
  activePart = part;
  if (!inspectBtn) return;
  if (!part) {
    inspectBtn.hidden = true;
    return;
  }
  inspectBtn.hidden = false;
  const size = formatMB(part.bytes);
  inspectBtnLabel.textContent = `Inspect the ${part.label}${size ? ` (${size})` : ""}`;
  inspector.prefetch(part.url);
}

function openActivePart() {
  if (!activePart) return;
  const spec = HUD[MECHANISMS.find((m) => PARTS[m] === activePart)];
  inspector.open(activePart.url, `The ${activePart.label}`, spec?.rows, activePart.sectionable);
}

inspectBtn?.addEventListener("click", openActivePart);
canvas.addEventListener("click", () => {
  if (activePart) openActivePart();
});

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(32, 1, 0.01, 100);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

scene.add(new THREE.HemisphereLight(0x9098a8, 0x151310, 1.6));
const key = new THREE.DirectionalLight(0xfff3e0, 2.2);
key.position.set(3, 5, 4);
scene.add(key);
const rim = new THREE.DirectionalLight(0x6f8cff, 0.6);
rim.position.set(-4, 2, -3);
scene.add(rim);

function resize() {
  const w = stageWrap.clientWidth, h = stageWrap.clientHeight;
  if (!w || !h) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(() => { resize(); computeKeyframes(); }).observe(stageWrap);
resize();

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function lerp(a, b, t) { return a + (b - a) * t; }

let meshInfo = [];
let keyframes = null;
let currentCamPos = new THREE.Vector3();
let currentCamTarget = new THREE.Vector3();
let bucketOpacity = {};
let ready = false;
let sceneBox = null;
let bucketBoxes = {};
const viewDir = new THREE.Vector3(-0.5, -0.38, -0.9); // camera -> target

// Each mechanism's camera keyframe activates at that chapter's own vertical
// center (not an equal 1/N slice of the page) - chapters have very different
// text lengths, so equal slicing would badly misalign the camera with what's
// actually on screen.
function computeBreakpoints() {
  const chaptersRect = chaptersEl.getBoundingClientRect();
  const total = chaptersRect.height - window.innerHeight;
  const bp = { Overview: 0 };
  document.querySelectorAll(".chapter[data-mech]").forEach((el) => {
    const r = el.getBoundingClientRect();
    const top = r.top - chaptersRect.top;
    const center = top + r.height / 2;
    bp[el.dataset.mech] = total > 0 ? clamp(center / total, 0, 1) : 0;
  });
  return bp;
}

function computeKeyframes() {
  if (!sceneBox) return;
  const aspect = camera.aspect || (stageWrap.clientWidth / stageWrap.clientHeight) || 1;
  const bp = computeBreakpoints();
  const order = ["Overview", ...MECHANISMS];
  const hadKeyframes = !!keyframes;
  keyframes = order.map((name) => {
    const box = name === "Overview" ? sceneBox : bucketBoxes[name];
    const margin = name === "Overview" ? 1.15 : 1.35;
    return { name, bp: bp[name] ?? 0, ...frameBox(box, viewDir, camera.fov, aspect, margin) };
  });
  if (!hadKeyframes) {
    currentCamPos.copy(keyframes[0].position);
    currentCamTarget.copy(keyframes[0].target);
    for (const m of MECHANISMS) bucketOpacity[m] = 1;
  }
}

new GLTFLoader().load(stageWrap.dataset.model, (gltf) => {
  const model = gltf.scene;
  scene.add(model);

  model.traverse((obj) => {
    if (!obj.isMesh) return;
    // Walk root -> mesh (not mesh -> root): a sub-assembly's own name (e.g.
    // "Shoulder Assembly Final 1.0") is an unambiguous signal for everything
    // inside it, whereas a leaf part can carry a generic name ("shaft
    // original-1") that happens to collide with an unrelated mechanism's
    // keyword. Checking outermost-first means that collision never gets a
    // chance to win once the correct sub-assembly has already matched.
    const chain = [];
    for (let node = obj; node; node = node.parent) chain.push(node);
    chain.reverse();
    let bucket = null;
    for (const node of chain) {
      bucket = classifyByName(node.name);
      if (bucket) break;
    }
    const box = new THREE.Box3().setFromObject(obj);
    const centroid = box.getCenter(new THREE.Vector3());
    obj.material = obj.material.clone();
    obj.material.transparent = true;
    meshInfo.push({ obj, bucket, centroid, box });
  });

  const anchors = {};
  const anchorCounts = {};
  for (const { bucket, centroid } of meshInfo) {
    if (!bucket) continue;
    anchors[bucket] = (anchors[bucket] || new THREE.Vector3()).add(centroid);
    anchorCounts[bucket] = (anchorCounts[bucket] || 0) + 1;
  }
  for (const b in anchors) anchors[b].divideScalar(anchorCounts[b]);

  for (const info of meshInfo) {
    if (!info.bucket) {
      let best = null, bestDist = Infinity;
      for (const b in anchors) {
        const d = info.centroid.distanceTo(anchors[b]);
        if (d < bestDist) { bestDist = d; best = b; }
      }
      info.bucket = best;
    }
  }

  sceneBox = new THREE.Box3().setFromObject(model);
  for (const m of MECHANISMS) {
    const box = new THREE.Box3();
    for (const info of meshInfo) if (info.bucket === m) box.union(info.box);
    bucketBoxes[m] = box;
  }

  computeKeyframes();
  ready = true;
  update();
  animate();
});

let lastHudBucket = null;
function renderHud(bucket, visible) {
  if (!visible) { hud.innerHTML = ""; lastHudBucket = null; return; }
  if (bucket === lastHudBucket) return;
  lastHudBucket = bucket;
  const spec = HUD[bucket];
  if (!spec) { hud.innerHTML = ""; return; }
  let html = `<div class="spec-title">${spec.title}</div>`;
  for (const [k, v] of spec.rows) html += `<div class="spec-row"><span>${k}</span><b>${v}</b></div>`;
  hud.innerHTML = html;
}

function update() {
  if (!ready) return;
  const rect = chaptersEl.getBoundingClientRect();
  const total = rect.height - window.innerHeight;
  const scrolled = -rect.top;
  const progress = total > 0 ? clamp(scrolled / total, 0, 1) : 0;

  let i0 = 0;
  for (let i = 0; i < keyframes.length - 1; i++) {
    if (progress >= keyframes[i].bp) i0 = i;
  }
  const i1 = Math.min(i0 + 1, keyframes.length - 1);
  const span = keyframes[i1].bp - keyframes[i0].bp || 1;
  const t = clamp((progress - keyframes[i0].bp) / span, 0, 1);
  const k0 = keyframes[i0], k1 = keyframes[i1];

  const goalPos = k0.position.clone().lerp(k1.position, t);
  const goalTarget = k0.target.clone().lerp(k1.target, t);

  const ease = REDUCE ? 1 : 0.16;
  currentCamPos.lerp(goalPos, ease);
  currentCamTarget.lerp(goalTarget, ease);
  camera.position.copy(currentCamPos);
  camera.lookAt(currentCamTarget);

  const activeIdx = t < 0.5 ? i0 : i1;
  const activeName = keyframes[activeIdx].name;
  const focus = clamp(progress / (keyframes[1].bp || 0.001), 0, 1);

  const opEase = REDUCE ? 1 : 0.12;
  for (const m of MECHANISMS) {
    const targetOp = activeName === "Overview" || m === activeName ? 1 : lerp(1, 0.14, focus);
    bucketOpacity[m] = lerp(bucketOpacity[m] ?? 1, targetOp, opEase);
  }
  for (const info of meshInfo) {
    if (info.bucket) info.obj.material.opacity = bucketOpacity[info.bucket];
  }

  const dispIdx = MECHANISMS.indexOf(activeName) + 1; // 0 while on Overview
  progNum.textContent = String(dispIdx).padStart(2, "0") + " / 05";
  progName.textContent = activeName;
  renderHud(activeName, focus > 0.35);
  updateInspectButton(activeName);

  renderer.render(scene, camera);
}

let ticking = false;
function onScroll() {
  if (!ticking) { requestAnimationFrame(() => { update(); ticking = false; }); ticking = true; }
}
window.addEventListener("scroll", onScroll, { passive: true });
window.addEventListener("resize", () => { resize(); computeKeyframes(); update(); });

function animate() {
  requestAnimationFrame(animate);
  update();
}
