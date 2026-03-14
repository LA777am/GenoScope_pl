
console.log("GENOSCOPE SYSTEM: INITIALIZED V3.0"); // Check console to confirm load

let scene, camera, renderer;
let dnaGroup, bokehSystem, gridSystem;
let particlesA, particlesB, connectors;
let pulses = []; // Array to store data packets


let mouseX = 0;
let mouseY = 0;
let targetRotationX = 0;
let targetRotationY = 0;

const CONFIG = {
  basePairs: 100,         
  radius: 4,              
  tubeLength: 100,        
  spinSpeed: 0.005,       
  colorA: 0x00ffcc,       // Teal
  colorB: 0xe0c48a,       // Gold
  pulseSpeed: 0.2         
};

let time = 0;

init();
animate();


function init() {
  const canvas = document.getElementById("bg-canvas");


  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x000000, 0.02); 

  camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
  // Pull camera back on mobile so the DNA helix fits without clipping
  camera.position.set(0, 0, window.innerWidth < 600 ? 50 : 30);


  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));


  setupHolographicTilt();
  createDNA();
  createGrid();
  createBokeh();
  

  for(let i=0; i<5; i++) {
    createPulse();
  }


  window.addEventListener("resize", onResize);
  document.addEventListener("mousemove", onMouseMove);
  setupTransitionLogic();
}


function createDNA() {
  dnaGroup = new THREE.Group();
  scene.add(dnaGroup);

  const count = CONFIG.basePairs;
  const geometryA = new THREE.BufferGeometry();
  const geometryB = new THREE.BufferGeometry();
  const geometryConnectors = new THREE.BufferGeometry();
  

  geometryA.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
  geometryB.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
  geometryConnectors.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3 * 2), 3));


  const matDot = new THREE.PointsMaterial({ size: 0.4, transparent: true, opacity: 0.9, blending: THREE.AdditiveBlending });
  const matLine = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.1 });


  const matA = matDot.clone(); matA.color.setHex(CONFIG.colorA);
  particlesA = new THREE.Points(geometryA, matA);


  const matB = matDot.clone(); matB.color.setHex(CONFIG.colorB);
  particlesB = new THREE.Points(geometryB, matB);


  connectors = new THREE.LineSegments(geometryConnectors, matLine);

  dnaGroup.add(particlesA, particlesB, connectors);
  

  dnaGroup.rotation.z = Math.PI / 6;
}


function createPulse() {

  pulses.push({
    index: Math.random() * CONFIG.basePairs, 
    strand: Math.random() > 0.5 ? 0 : 1,     
    mesh: new THREE.Mesh(
      new THREE.SphereGeometry(0.3, 8, 8),
      new THREE.MeshBasicMaterial({ color: 0xffffff })
    )
  });

  scene.add(pulses[pulses.length-1].mesh);
}


function createGrid() {
  gridSystem = new THREE.GridHelper(200, 50, 0x111111, 0x050505);
  gridSystem.position.y = -15;
  gridSystem.rotation.x = 0.1; // Slight tilt
  scene.add(gridSystem);
}

function createBokeh() {
  const geo = new THREE.BufferGeometry();
  const count = 50;
  const pos = new Float32Array(count*3);
  for(let i=0; i<count*3; i++) pos[i] = (Math.random()-0.5)*150;
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  
  const mat = new THREE.PointsMaterial({
    color: CONFIG.colorA, size: 2, transparent: true, opacity: 0.2, blending: THREE.AdditiveBlending
  });
  bokehSystem = new THREE.Points(geo, mat);
  scene.add(bokehSystem);
}


function updateDNA() {
  const posA = particlesA.geometry.attributes.position.array;
  const posB = particlesB.geometry.attributes.position.array;
  const posConn = connectors.geometry.attributes.position.array;

  const spacing = CONFIG.tubeLength / CONFIG.basePairs;
  const offset = CONFIG.tubeLength / 2;

  for (let i = 0; i < CONFIG.basePairs; i++) {
    const x = (i * spacing) - offset;
    const angle = (i * 0.2) + time; // The Twist
    

    const yWave = Math.sin(i * 0.1 + time * 2) * 2;


    const yA = Math.cos(angle) * CONFIG.radius + yWave;
    const zA = Math.sin(angle) * CONFIG.radius;


    const yB = Math.cos(angle + Math.PI) * CONFIG.radius + yWave;
    const zB = Math.sin(angle + Math.PI) * CONFIG.radius;


    const idx = i * 3;
    posA[idx] = x; posA[idx+1] = yA; posA[idx+2] = zA;
    posB[idx] = x; posB[idx+1] = yB; posB[idx+2] = zB;

    const cIdx = i * 6;
    posConn[cIdx] = x; posConn[cIdx+1] = yA; posConn[cIdx+2] = zA;
    posConn[cIdx+3] = x; posConn[cIdx+4] = yB; posConn[cIdx+5] = zB;
  }
  
  particlesA.geometry.attributes.position.needsUpdate = true;
  particlesB.geometry.attributes.position.needsUpdate = true;
  connectors.geometry.attributes.position.needsUpdate = true;


  pulses.forEach(p => {
    p.index += CONFIG.pulseSpeed;
    if(p.index >= CONFIG.basePairs) p.index = 0; // Loop back


    const i = Math.floor(p.index);
    const spacing = CONFIG.tubeLength / CONFIG.basePairs;
    const offset = CONFIG.tubeLength / 2;
    const x = (i * spacing) - offset;
    const angle = (i * 0.2) + time;
    const yWave = Math.sin(i * 0.1 + time * 2) * 2;

   
    let ly, lz;
    if(p.strand === 0) {
       ly = Math.cos(angle) * CONFIG.radius + yWave;
       lz = Math.sin(angle) * CONFIG.radius;
    } else {
       ly = Math.cos(angle + Math.PI) * CONFIG.radius + yWave;
       lz = Math.sin(angle + Math.PI) * CONFIG.radius;
    }


    const rot = Math.PI / 6;
    const wx = x * Math.cos(rot) - ly * Math.sin(rot);
    const wy = x * Math.sin(rot) + ly * Math.cos(rot);
    
    p.mesh.position.set(wx, wy, lz);
  });
}

function onMouseMove(event) {
  mouseX = (event.clientX - window.innerWidth / 2) * 0.001;
  mouseY = (event.clientY - window.innerHeight / 2) * 0.001;
}

function animate() {
  requestAnimationFrame(animate);
  time += CONFIG.spinSpeed;

  updateDNA();


  targetRotationX += (mouseY - targetRotationX) * 0.05;
  targetRotationY += (mouseX - targetRotationY) * 0.05;

  dnaGroup.rotation.x = targetRotationX; 
  dnaGroup.rotation.y = targetRotationY;

  // Floor Movement
  if(gridSystem) {
      gridSystem.position.z += 0.1;
      if(gridSystem.position.z > 0) gridSystem.position.z = -10;
  }

  renderer.render(scene, camera);
}

function onResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  // Re-adjust camera depth on resize so rings stay circular, not oval
  camera.position.z = window.innerWidth < 600 ? 50 : 30;
}

function setupTransitionLogic() {
  const initBtn = document.getElementById("initBtn");
  const shutterSystem = document.getElementById("transition-system");
  const statusLine = document.querySelector(".status-line");
  const successLine = document.querySelector(".success");

  if (!initBtn) return;

  initBtn.addEventListener("click", (e) => {
    e.preventDefault();
    shutterSystem.classList.add("active");
    setTimeout(() => {
      if (statusLine) statusLine.style.display = "none";
      if (successLine) {
        successLine.style.display = "block";
        successLine.classList.add("glitch-effect");
      }
    }, 1200);
    setTimeout(() => { window.location.href = "/auth"; }, 2200);
  });
}




// 2. Add this new function at the bottom of the file:
function setupHolographicTilt() {
  const reactor = document.querySelector('.reactor-system');
  const overlay = document.querySelector('.intro-overlay');

  if (!reactor || !overlay) return;


  document.addEventListener('mousemove', (e) => {
    const x = e.clientX;
    const y = e.clientY;
    
    const w = window.innerWidth;
    const h = window.innerHeight;


    const rotateY = ((x - w / 2) / w) * 20; 
    const rotateX = ((y - h / 2) / h) * -20;


    reactor.style.transform = `
      perspective(1000px) 
      rotateX(${rotateX}deg) 
      rotateY(${rotateY}deg) 
      scale3d(1, 1, 1)
    `;
  });


  document.addEventListener('mouseleave', () => {
    reactor.style.transform = `
      perspective(1000px) 
      rotateX(0deg) 
      rotateY(0deg)
    `;
  });
}