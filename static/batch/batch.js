const resultsArea = document.getElementById("resultsArea");
const idleGraphic = document.getElementById("idleGraphic");
const log = (msg) => {
  const el = document.getElementById("log");
  el.textContent += msg + "\n";
  el.scrollTop = el.scrollHeight;
};

let currentBatchId = null;

let batchReportData = {
    summary: null,
    gc: null,
    coding: null,
    promoter: null
};
document.getElementById("startBatch").addEventListener("click", async () => {
  const fileInput = document.getElementById("fastaFile");
  const file = fileInput.files[0];

  if (!file) {
    alert("Please upload a FASTA file");
    return;
  }
  const validExtensions = ['.fasta', '.fa'];
  const fileName = file.name.toLowerCase();
  
  // validation logic
  if (!validExtensions.some(ext => fileName.endsWith(ext))) {
      alert("INVALID FILE FORMAT\n\nSystem only accepts FASTA formats (.fasta or .fa).\nPlease check your input file.");
      return; // Stop execution here
  }
  log("⏳ Initializing batch…");

  try {
    // 1 Upload FASTA (backend creates batch + processes everything)
    const fd = new FormData();
    fd.append("file", file);

    const res = await fetch("/api/batch/upload_fasta", {
      method: "POST",
      credentials: "same-origin",
      body: fd
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "Batch upload failed");
    }

    const result = await res.json();
    currentBatchId = result.batch_id;

    log(` Batch created: ${currentBatchId}`);
    log(` Sequences processed: ${result.total_sequences}`);
    log(" Analysis complete");


    await loadBatchResults(currentBatchId);

  } catch (err) {
    console.error(err);
    log("❌ ERROR: " + err.message);
  }
});

async function loadBatchResults(batchId) {
  log(" Fetching batch summary…");
  
  idleGraphic.style.opacity = "0";
  resultsArea.classList.add("active");

  
  const summary = await fetch(`/api/batches/${batchId}/summary`).then(r => r.json());
  batchReportData.summary = summary; 

  const summaryEl = document.getElementById("summary");
  

  const { batch_id, total_sequences, avg_gc, coding, promoter } = summary;

  summaryEl.innerHTML = `
    <div class="manifest-row row-gold">
      <span class="manifest-label">BATCH ID</span>
      <span class="manifest-value val-gold">#${batch_id}</span>
    </div>
    <div class="manifest-row">
      <span class="manifest-label">TOTAL READS</span>
      <span class="manifest-value val-white">${total_sequences}</span>
    </div>
    <div class="manifest-row row-cyan">
      <span class="manifest-label">AVG GC CONTENT</span>
      <span class="manifest-value val-cyan">${avg_gc ? avg_gc.toFixed(1) : 0}%</span>
    </div>
    <div class="manifest-row row-green">
      <span class="manifest-label">CODING CDS</span>
      <span class="manifest-value val-green">
        ${coding.count} <span class="sub-val">(${coding.percent}%)</span>
      </span>
    </div>
    <div class="manifest-row row-purple">
      <span class="manifest-label">PROMOTERS</span>
      <span class="manifest-value val-purple">
        ${promoter.count} <span class="sub-val">(${promoter.percent}%)</span>
      </span>
    </div>
  `;

 
  const gc = await fetch(`/api/batches/${batchId}/gc_distribution`).then(r => r.json());
  batchReportData.gc = gc; 
  renderGCChart(gc.gc_values);

  const codingDist = await fetch(`/api/batches/${batchId}/confidence_distribution?model=coding`).then(r => r.json());
  batchReportData.coding = codingDist; 
  renderConfidenceChart("codingConfidenceChart", codingDist.confidences, "Coding Confidence");


  const promoterDist = await fetch(`/api/batches/${batchId}/confidence_distribution?model=promoter`).then(r => r.json());
  batchReportData.promoter = promoterDist; 
  renderConfidenceChart("promoterConfidenceChart", promoterDist.confidences, "Promoter Confidence");

  const exportBtn = document.getElementById("exportBatchBtn");
  if(exportBtn) {
      exportBtn.style.display = "flex"; 
      exportBtn.onclick = generateBatchPDF;
  }

  log(" Charts rendered & Data ready for export");
}

let gcChart = null;
let codingChart = null;
let promoterChart = null;


function renderGCChart(values) {
  const canvas = document.getElementById("gcChart");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  if (gcChart) gcChart.destroy();

  

  const gradCyan = ctx.createLinearGradient(0, 0, 0, 400);
  gradCyan.addColorStop(0, 'rgba(0, 255, 204, 0.9)');
  gradCyan.addColorStop(1, 'rgba(0, 255, 204, 0.1)');


  const gradPurple = ctx.createLinearGradient(0, 0, 0, 400);
  gradPurple.addColorStop(0, 'rgba(147, 125, 177, 0.9)');
  gradPurple.addColorStop(1, 'rgba(189, 147, 249, 0.1)');


  const gradRose = ctx.createLinearGradient(0, 0, 0, 400);
  gradRose.addColorStop(0, 'rgba(252, 106, 135, 0.52)');
  gradRose.addColorStop(1, 'rgba(255, 85, 119, 0.1)');


  const backgrounds = values.map((_, i) => {
    const cycle = i % 3;
    if (cycle === 0) return gradCyan;
    if (cycle === 1) return gradPurple;
    return gradRose;
  });

  gcChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: values.map((_, i) => i + 1),
      datasets: [{
        label: "GC %",
        data: values,
        backgroundColor: backgrounds, 
        borderRadius: 4,
        borderWidth: 0,
        barPercentage: 0.7
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#6b7280', font: { family: 'JetBrains Mono', size: 10 } }
        },
        x: { display: false }
      }
    }
  });
}
function renderConfidenceChart(canvasId, values, label) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");


  if (canvasId === "codingConfidenceChart" && codingChart) codingChart.destroy();
  if (canvasId === "promoterConfidenceChart" && promoterChart) promoterChart.destroy();


  let colorStart, colorEnd, borderColor;

  if (canvasId === "codingConfidenceChart") {

    colorStart = 'rgba(224, 196, 138, 0.5)';
    colorEnd   = 'rgba(224, 196, 138, 0.0)';
    borderColor = "#E0C48A";
  } else {

    colorStart  = 'rgba(0, 255, 204, 0.35)';
    colorEnd    = 'rgba(0, 255, 204, 0.0)';
    borderColor = '#00e5b8';
  }


  const gradient = ctx.createLinearGradient(0, 0, 0, 400);
  gradient.addColorStop(0, colorStart);
  gradient.addColorStop(1, colorEnd);


  const thresholdData = new Array(values.length).fill(0.5);

  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: values.map((_, i) => i + 1),
      datasets: [

        {
          label: label,
          data: values,
          borderColor: borderColor,
          borderWidth: 2,
          backgroundColor: gradient,
          tension: 0.4,
          fill: true,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointBackgroundColor: borderColor,
          pointBorderColor: "#fff",
          order: 2 
        },


        {
          label: 'Threshold (0.5)',
          data: thresholdData,

          borderColor: 'rgba(255, 255, 255, 0.3)', 
          borderWidth: 1,

          borderDash: [4, 4],     
          pointRadius: 0,
          fill: false,
          order: 1,

          tension: 0              
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { 
        legend: { display: false },
        tooltip: {
            mode: 'index',
            intersect: false,
            filter: function(tooltipItem) {

                return tooltipItem.datasetIndex === 0; 
            }
        }
      },
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: {
          min: 0, max: 1, 
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { 
              color: '#6b7280', 
              font: { family: 'JetBrains Mono', size: 10 },
              stepSize: 0.2
          }
        },
        x: { display: false }
      }
    }
  });


  if (canvasId === "codingConfidenceChart") codingChart = chart;
  if (canvasId === "promoterConfidenceChart") promoterChart = chart;
}
const historyBtn = document.getElementById("historyBtn");
const historyModal = document.getElementById("historyModal");
const historyContent = document.getElementById("historyContent");

if (historyBtn) {
  historyBtn.addEventListener("click", () => {
    historyModal.classList.add("active");
    loadBatchHistory();
  });
}

function closeHistory() {
  historyModal.classList.remove("active");
  historyContent.innerHTML = "";
}


async function loadBatchHistory() {
  historyContent.innerHTML = `
    <div style="padding:20px;color:#666;text-align:center">
      FETCHING BATCH ARCHIVE...
    </div>
  `;

  try {
    const res = await fetch("/api/history/batch", {
      credentials: "same-origin"
    });

    if (!res.ok) throw new Error("Unauthorized");

    const batches = await res.json();

    if (!batches.length) {
      historyContent.innerHTML = `
        <div style="padding:20px;color:#666;text-align:center">
          NO BATCH RECORDS FOUND
        </div>`;
      return;
    }

    historyContent.innerHTML = "";

    batches.forEach(b => {
      const batchDiv = document.createElement("div");
      batchDiv.className = "batch-item";
      batchDiv.style.padding = "16px 20px";
      batchDiv.style.borderBottom = "1px solid rgba(255,255,255,0.05)";
      batchDiv.style.cursor = "pointer";

      batchDiv.innerHTML = `
        <div style="display:flex;justify-content:space-between">
          <span style="color:#e0c48a">BATCH #${b.batch_id}</span>
          <span style="color:#666;font-size:11px">
            ${new Date(b.created_at).toLocaleString()}
          </span>
        </div>
        <div style="color:#888;font-size:12px;margin-top:4px">
          Sequences: ${b.total_sequences}
        </div>
      `;

      batchDiv.onclick = () => expandBatch(b.batch_id, batchDiv);
      historyContent.appendChild(batchDiv);
    });

  } catch (e) {
    historyContent.innerHTML = `
      <div style="padding:20px;color:#ff3333;text-align:center">
        FAILED TO LOAD HISTORY
      </div>`;
  }
}



async function expandBatch(batchId, container) {
  const existing = container.querySelector(".seq-box");
  if (existing) {
    existing.remove();
    return;
  }

  const seqBox = document.createElement("div");
  seqBox.className = "seq-box";
  seqBox.style.marginTop = "12px";
  seqBox.style.paddingLeft = "12px";
  seqBox.style.borderLeft = "2px solid #00ffcc";
  seqBox.innerHTML = `<div style="color:#666">LOADING SEQUENCES...</div>`;
  container.appendChild(seqBox);

  try {
    const res = await fetch(`/api/batches/${batchId}/sequences`, {
      credentials: "same-origin"
    });
    const seqs = await res.json();

    seqBox.innerHTML = seqs.map(s => `
      <div style="padding:6px 0;color:#ccc;font-size:12px">
        ▸ SEQ ${s.sequence_id} | LEN ${s.length} | GC ${s.gc_percent?.toFixed(2)}%
      </div>
    `).join("");
  } catch {
    seqBox.innerHTML = `<div style="color:#ff3333">FAILED TO LOAD</div>`;
  }
}
document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById("fastaFile");
  const fileMsg = document.getElementById("fileNameDisplay");
  const dropZone = fileInput.closest('.file-wrapper'); // Get the wrapper


  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
        const file = e.target.files[0];
        const name = file.name.toUpperCase();
        const isValid = name.endsWith('.FASTA') || name.endsWith('.FA');

        fileMsg.textContent = name;

        if (isValid) {
            // Valid State (Cyan/Accent)
            fileMsg.style.color = "var(--accent)";
            fileMsg.style.borderColor = "var(--accent)";
            dropZone.classList.add("mounted");
            dropZone.style.borderColor = "var(--accent)";
        } else {
            // Invalid State (Red/Danger)
            fileMsg.style.color = "#ff3333";
            fileMsg.textContent = "⚠ INVALID FORMAT (" + name + ")";
            dropZone.classList.remove("mounted");
            dropZone.style.borderColor = "#ff3333";
        }
        
        fileMsg.style.fontWeight = "600";
        fileMsg.style.letterSpacing = "0.05em";
    }

  });


  const btn = document.getElementById('startBatch');
  const resultsArea = document.getElementById('resultsArea');
  const idleGraphic = document.getElementById('idleGraphic');

  btn.addEventListener('click', () => {
      if (fileInput.files.length > 0) {

          if (idleGraphic) idleGraphic.style.opacity = '0';


          setTimeout(() => {
              if (resultsArea) resultsArea.classList.add('active');
          }, 1000);
      } else {
          alert("PLEASE MOUNT A FASTA FILE FIRST.");
      }
  });
});
function tick() {
  const now = new Date();
  document.getElementById('clock').innerText = now.toLocaleTimeString('en-GB');
}
setInterval(tick, 1000); tick();

// Modal Logic
const modal = document.getElementById('exitModal');
function openModal() { modal.classList.add('active'); }
function closeModal() { modal.classList.remove('active'); }

// Close on backdrop click
modal.addEventListener('click', (e) => {
  if (e.target === modal) closeModal();
});


const logoutBtn = document.getElementById("logoutBtn");

if (logoutBtn) {
  logoutBtn.addEventListener("click", async () => {
      // 1. Visual Feedback: Freeze interface & indicate processing
      logoutBtn.style.pointerEvents = "none";
      const textLabel = logoutBtn.querySelector(".label-hover");
      const icon = logoutBtn.querySelector(".power-housing");

      if (textLabel) textLabel.innerText = "BYE...";
      if (icon) icon.style.opacity = "0.5";

      // 2. Perform Logout
      try {
          await fetch("/auth/logout", { method: "POST" });
      } catch (err) {
          console.warn("Logout fetch failed, forcing redirect anyway.");
      }

      // 3. Short Delay for "System Down" feel (0.5s)
      setTimeout(() => {
          window.location.href = "/auth";
      }, 500);
  });
}

function generateBatchPDF() {
    if (!batchReportData.summary) {
        alert("No batch data available.");
        return;
    }

    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const data = batchReportData;

    // --- STYLING ---
    const brandColor = [6, 182, 212]; // Cyan
    let yPos = 20;

    // --- HEADER ---
    doc.setFont("courier", "bold");
    doc.setFontSize(22);
    doc.setTextColor(...brandColor);
    doc.text("GENOSCOPE // BATCH CORE", 14, yPos);
    
    yPos += 8;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`Batch ID: ${data.summary.batch_id} | Automated Audit Report`, 14, yPos);
    doc.text(new Date().toLocaleString(), 196, yPos, { align: "right" });
    
    yPos += 15;
    doc.setDrawColor(...brandColor);
    doc.line(14, yPos, 196, yPos);
    yPos += 15;

    // --- SECTION 1: EXECUTIVE SUMMARY ---
    doc.setFont("helvetica", "bold");
    doc.setFontSize(12);
    doc.setTextColor(0);
    doc.text("1. BATCH MANIFEST", 14, yPos);
    yPos += 8;

    const summaryBody = [
        ["Total Sequences", data.summary.total_sequences],
        ["Average GC Content", `${data.summary.avg_gc}%`],
        ["Coding Candidates", `${data.summary.coding.count} (${data.summary.coding.percent}%)`],
        ["Promoter Detected", `${data.summary.promoter.count} (${data.summary.promoter.percent}%)`]
    ];

    doc.autoTable({
        startY: yPos,
        head: [['Metric', 'Value']],
        body: summaryBody,
        theme: 'grid',
        headStyles: { fillColor: brandColor, textColor: 255, fontStyle: 'bold' },
        styles: { fontSize: 10, cellPadding: 4 },
        columnStyles: { 0: { fontStyle: 'bold', width: 80 } }
    });

    yPos = doc.lastAutoTable.finalY + 15;

  
    doc.text("2. Regional Computation Results", 14, yPos);
    yPos += 8;


    const getStats = (arr) => {
        if (!arr || arr.length === 0) return ["N/A", "N/A", "N/A"];
        const min = Math.min(...arr).toFixed(2);
        const max = Math.max(...arr).toFixed(2);
        const avg = (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2);
        return [min, avg, max];
    };

    const codingStats = getStats(data.coding.confidences);
    const promoterStats = getStats(data.promoter.confidences);

    doc.autoTable({
        startY: yPos,
        head: [['Model Type', 'Min Confidence', 'Avg Confidence', 'Max Confidence']],
        body: [
            ['Coding Region (RF)', ...codingStats],
            ['Promoter Region (RF)', ...promoterStats]
        ],
        theme: 'striped',
        headStyles: { fillColor: [50, 50, 50] }
    });

    yPos = doc.lastAutoTable.finalY + 15;

    // --- SECTION 3: SEQUENCE DISTRIBUTION ---
    doc.text("3. NUCLEOTIDE DISTRIBUTION SAMPLE", 14, yPos);
    yPos += 6;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(9);
    doc.setTextColor(100);
    doc.text("(First 20 sequences sorted by GC content)", 14, yPos);
    yPos += 4;

    // Prepare table data from GC distribution (showing sample)
    const gcRows = data.gc.gc_values.slice(0, 20).map((val, index) => [
        `Seq_Index_${index + 1}`, 
        `${val.toFixed(2)}%`,
        val > 50 ? "High GC" : "Low GC"
    ]);

    doc.autoTable({
        startY: yPos,
        head: [['Sequence Ref', 'GC Content', 'Classification']],
        body: gcRows,
        theme: 'plain',
        headStyles: { fillColor: [220, 220, 220], textColor: 0 },
        margin: { bottom: 20 }
    });

    // --- FOOTER ---
    const pageCount = doc.internal.getNumberOfPages();
    for(let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(150);
        doc.text(`Genoscope Auto-Generated Report | Page ${i} of ${pageCount}`, 105, 290, { align: "center" });
    }

    doc.save(`Batch_${data.summary.batch_id}_Report.pdf`);
}