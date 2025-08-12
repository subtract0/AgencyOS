import * as THREE from 'https://unpkg.com/three@0.160.0/build/three.module.js';
import { OrbitControls } from 'https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'https://unpkg.com/three@0.160.0/examples/jsm/renderers/CSS2DRenderer.js';

const container = document.getElementById('app');
const speedEl = document.getElementById('speed');
const scene = new THREE.Scene();
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
container.appendChild(renderer.domElement);
const labelRenderer = new CSS2DRenderer();
labelRenderer.setSize(window.innerWidth, window.innerHeight);
labelRenderer.domElement.style.position = 'absolute';
labelRenderer.domElement.style.top = '0';
labelRenderer.domElement.style.pointerEvents = 'none';
container.appendChild(labelRenderer.domElement);
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 2000);
camera.position.set(0, 30, 80);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
const ambient = new THREE.AmbientLight(0x404040, 0.5);
scene.add(ambient);
const sunGroup = new THREE.Group();
scene.add(sunGroup);
const sunGeo = new THREE.SphereGeometry(5, 64, 64);
const sunMat = new THREE.MeshBasicMaterial({ color: 0xffcc66 });
const sun = new THREE.Mesh(sunGeo, sunMat);
sunGroup.add(sun);
const sunLight = new THREE.PointLight(0xffffff, 2.2, 0, 2);
sunLight.position.set(0,0,0);
sunGroup.add(sunLight);
const starsGeo = new THREE.BufferGeometry();
const starCount = 2000;
const starPos = new Float32Array(starCount * 3);
for (let i = 0; i < starCount; i++) {
  const r = 400 + Math.random() * 600;
  const t = Math.random() * Math.PI * 2;
  const p = Math.acos(2 * Math.random() - 1);
  starPos[i*3+0] = r * Math.sin(p) * Math.cos(t);
  starPos[i*3+1] = r * Math.cos(p);
  starPos[i*3+2] = r * Math.sin(p) * Math.sin(t);
}
starsGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3));
const starsMat = new THREE.PointsMaterial({ color: 0xffffff, size: 0.6, sizeAttenuation: true });
const stars = new THREE.Points(starsGeo, starsMat);
scene.add(stars);
const system = new THREE.Group();
scene.add(system);
const yearSeconds = 20;
let showLabels = true;
let paused = false;
let timeScale = 1;
const planets = [
  { name: 'Mercury', color: 0xb1b1b1, size: 0.19, dist: 8, years: 0.24, rot: 58.6 },
  { name: 'Venus', color: 0xe0c16c, size: 0.47, dist: 11, years: 0.62, rot: -243 },
  { name: 'Earth', color: 0x5aa9ff, size: 0.5, dist: 14, years: 1.0, rot: 1 },
  { name: 'Mars', color: 0xd26c4a, size: 0.27, dist: 17, years: 1.88, rot: 1.03 },
  { name: 'Jupiter', color: 0xd8b28a, size: 5.5, dist: 24, years: 11.86, rot: 0.41 },
  { name: 'Saturn', color: 0xe8d5a9, size: 4.7, dist: 32, years: 29.45, rot: 0.44, rings: true },
  { name: 'Uranus', color: 0x9fd9e8, size: 2.0, dist: 38, years: 84, rot: -0.72 },
  { name: 'Neptune', color: 0x6fa8ff, size: 1.95, dist: 44, years: 164.8, rot: 0.67 }
];
const planetData = [];
function makeLabel(text) {
  const div = document.createElement('div');
  div.className = 'label';
  div.textContent = text;
  return new CSS2DObject(div);
}
function addOrbit(radius) {
  const seg = 256;
  const pts = new Float32Array((seg+1) * 3);
  for (let i = 0; i <= seg; i++) {
    const a = (i / seg) * Math.PI * 2;
    pts[i*3+0] = Math.cos(a) * radius;
    pts[i*3+1] = 0;
    pts[i*3+2] = Math.sin(a) * radius;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pts, 3));
  const m = new THREE.LineBasicMaterial({ color: 0x333333 });
  const line = new THREE.Line(g, m);
  line.rotation.x = 0;
  system.add(line);
}
for (const p of planets) {
  addOrbit(p.dist);
  const pivot = new THREE.Object3D();
  system.add(pivot);
  const geo = new THREE.SphereGeometry(p.size, 48, 48);
  const mat = new THREE.MeshStandardMaterial({ color: p.color, roughness: 0.8, metalness: 0.0 });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set(p.dist, 0, 0);
  pivot.add(mesh);
  const label = makeLabel(p.name);
  label.position.set(0, p.size + 0.8, 0);
  mesh.add(label);
  if (p.rings) {
    const ringGeo = new THREE.RingGeometry(p.size * 1.3, p.size * 2.2, 128);
    const ringMat = new THREE.MeshBasicMaterial({ color: 0xdcc7a4, side: THREE.DoubleSide, transparent: true, opacity: 0.7 });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2.3;
    mesh.add(ring);
  }
  planetData.push({ pivot, mesh, years: p.years, rot: p.rot, label });
}
function setLabelsVisible(v) {
  labelRenderer.domElement.style.display = v ? 'block' : 'none';
}
setLabelsVisible(showLabels);
function onResize() {
  const w = window.innerWidth, h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  labelRenderer.setSize(w, h);
}
window.addEventListener('resize', onResize);
window.addEventListener('keydown', (e) => {
  if (e.key === ' ') { paused = !paused; }
  if (e.key === '[') { timeScale = Math.max(0.1, +(Math.round((timeScale/1.5)*10)/10).toFixed(1)); }
  if (e.key === ']') { timeScale = Math.min(20, +(Math.round((timeScale*1.5)*10)/10).toFixed(1)); }
  if (e.key.toLowerCase() === 'l') { showLabels = !showLabels; setLabelsVisible(showLabels); }
});
let last = performance.now();
function animate() {
  requestAnimationFrame(animate);
  const now = performance.now();
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  if (!paused) {
    const s = dt * timeScale;
    for (const p of planetData) {
      const period = p.years * yearSeconds;
      const orbitAng = (Math.PI * 2) * (s / period);
      p.pivot.rotation.y += orbitAng;
      const rotPeriod = Math.abs(p.rot) * 0.05;
      if (rotPeriod > 0) {
        const spin = (Math.PI * 2) * (s / rotPeriod) * (p.rot < 0 ? -1 : 1);
        p.mesh.rotation.y += spin;
      }
    }
    sun.rotation.y += dt * 0.2;
  }
  controls.update();
  speedEl.textContent = `Speed: ${timeScale.toFixed(1)}x${paused ? ' (paused)' : ''}`;
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
}
animate();
