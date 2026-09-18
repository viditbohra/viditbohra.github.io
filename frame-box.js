import * as THREE from "three";

// Fits `box` in view along a fixed viewing direction, centering it in
// screen space (not just at its 3D centroid) - a diagonal/L-shaped object
// like this arm has a screen-space footprint that isn't symmetric around
// its bounding-box center, so lookAt(box.center) alone leaves it off-centre.
// Shared by the story camera (case-study.js) and the part inspector
// (part-inspector.js), which is why it lives on its own.
export function frameBox(box, viewDirFromTarget, fovDeg, aspect, margin = 1.2) {
  const dir = viewDirFromTarget.clone().normalize(); // camera -> target
  const worldUp = new THREE.Vector3(0, 1, 0);
  let right = new THREE.Vector3().crossVectors(dir, worldUp);
  if (right.lengthSq() < 1e-6) right = new THREE.Vector3(1, 0, 0);
  right.normalize();
  const up = new THREE.Vector3().crossVectors(right, dir).normalize();

  const center = box.getCenter(new THREE.Vector3());
  const corners = [];
  for (let i = 0; i < 8; i++) {
    corners.push(new THREE.Vector3(
      i & 1 ? box.max.x : box.min.x,
      i & 2 ? box.max.y : box.min.y,
      i & 4 ? box.max.z : box.min.z,
    ));
  }
  let minR = Infinity, maxR = -Infinity, minU = Infinity, maxU = -Infinity;
  for (const c of corners) {
    const rel = c.clone().sub(center);
    const r = rel.dot(right), u = rel.dot(up);
    minR = Math.min(minR, r); maxR = Math.max(maxR, r);
    minU = Math.min(minU, u); maxU = Math.max(maxU, u);
  }
  const target = center.clone()
    .add(right.clone().multiplyScalar((minR + maxR) / 2))
    .add(up.clone().multiplyScalar((minU + maxU) / 2));
  const halfW = ((maxR - minR) / 2) || 0.001;
  const halfH = ((maxU - minU) / 2) || 0.001;

  const vFov = (fovDeg * Math.PI) / 180;
  const hFov = 2 * Math.atan(Math.tan(vFov / 2) * aspect);
  const dist = Math.max(halfH / Math.tan(vFov / 2), halfW / Math.tan(hFov / 2)) * margin;

  const position = target.clone().add(dir.clone().negate().multiplyScalar(dist));
  return { position, target };
}
