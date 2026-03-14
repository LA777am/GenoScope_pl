const $ = (id) => document.getElementById(id);
let lastSequenceId = null;


let globalAnalysisData = {
    gc: null,
    ml: null,
    promoter: null,
    orfs: null
};


let renderFlags = {
    gc: false,
    ml: false,
    promoter: false,
    orf: false
};
document.addEventListener("DOMContentLoaded", () => {
    const sections = document.querySelectorAll("section[id], div[id]");
    const navLinks = document.querySelectorAll(".nav-item");
    const mainContainer = document.querySelector("main"); 


    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({ 
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });


    function updateActiveNav() {
        const scrollPos = mainContainer.scrollTop + 50; // Reduced offset for better detection
        let current = '';
        let bestMatch = { id: '', score: -1 };


        sections.forEach(section => {
            if (!section.id) return;
            

            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionBottom = sectionTop + sectionHeight;
            

            const viewportTop = scrollPos;
            const viewportBottom = scrollPos + mainContainer.clientHeight;
            

            const overlapTop = Math.max(sectionTop, viewportTop);
            const overlapBottom = Math.min(sectionBottom, viewportBottom);
            const overlapHeight = Math.max(0, overlapBottom - overlapTop);
            

            const visibilityScore = overlapHeight / Math.min(sectionHeight, mainContainer.clientHeight);
            

            if (visibilityScore > bestMatch.score) {
                bestMatch = { id: section.id, score: visibilityScore };
            }
            

            if (scrollPos >= sectionTop && scrollPos < sectionBottom) {
                current = section.id;
            }
        });


        if (bestMatch.score > 0.1) { 
            current = bestMatch.id;
        }


        if (mainContainer.scrollTop < 50) {
            const firstSection = sections[0];
            if (firstSection && firstSection.id) {
                current = firstSection.id;
            }
        }


        navLinks.forEach(link => {
            link.classList.remove("nav-item-active");
        });


        if (current) {
            const activeLink = document.querySelector(`.nav-item[href="#${current}"]`);
            if (activeLink) {
                activeLink.classList.add("nav-item-active");
            }
        }
    }


    let scrollTimeout;
    mainContainer.addEventListener("scroll", () => {
        if (scrollTimeout) {
            clearTimeout(scrollTimeout);
        }
        scrollTimeout = setTimeout(updateActiveNav, 10); 
    });


    setTimeout(updateActiveNav, 200);

    const analyzeBtn = $("analyzeBtn");
    if (analyzeBtn) {
        analyzeBtn.addEventListener("click", async () => {
            const statusText = document.getElementById("statusIndicator");
            
           
            if(statusText) {
                statusText.innerText = "COMPUTING SEQUENCE...";
                statusText.classList.add("text-yellow-400");
            }
            analyzeBtn.disabled = true;

            try {
  
                await analyzeSequence();
                await runCodingClassifier();
                await runPromoterAnalysis();

                
                updateCinematicPreviews();

                
                activateSystemMode();

            } catch (error) {
                console.error(error);
                if(statusText) {
                    statusText.innerText = "SYSTEM ERROR";
                    statusText.classList.add("text-red-500");
                }
            } finally {
                analyzeBtn.disabled = false;
            }
        });
    }

    const uploadBtn = $("uploadBtn");
    const fastaFile = $("fastaFile");

    if (uploadBtn && fastaFile) {
        uploadBtn.addEventListener("click", () => fastaFile.click());

        fastaFile.addEventListener("change", async () => {
            const file = fastaFile.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append("file", file);

            const res = await fetch("/api/upload_fasta", {
                method: "POST",
                body: formData
            });

            const data = await res.json();
            if (data.error) return notify(data.error);

            $("seqInput").value = data.cleaned_sequence;
            notify("FASTA loaded successfully!", "success");
        });
    }
});


console.log("JS Loaded Successfully!");


function notify(msg, type = "error") {
    alert(msg); 
}


let gcChart = null;

function updateGCChart(gc) {
    const ctx = $("gcChart");

    if (gcChart) gcChart.destroy();

    gcChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["GC%", "AT%"],
            datasets: [{
                data: [gc, 100 - gc],
                backgroundColor: ["#E0C48A", "#242733"],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: "70%",
            plugins: { legend: { display: false } }
        }
    });

    $("gcValue").innerText = `${gc.toFixed(2)}% GC`;
    

    $("summaryGC").innerText = `${gc.toFixed(1)}%`;
}


let mlChart = null;

function updateMLProbability(prob) {
    const ctx = $("mlProbChart");

    if (mlChart) mlChart.destroy();

    mlChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Coding Probability"],
            datasets: [{
                data: [prob],
                backgroundColor: "rgba(224,196,138,0.65)"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 0,
                    max: 1,
                    ticks: { color: "#C5C7D3" }
                },
                x: {
                    ticks: { color: "#C5C7D3" }
                }
            },
            plugins: { legend: { display: false } }
        }
    });

    $("mlResult").innerText = prob >= 0.5 ? "Coding Region" : "Noncoding";
    
    // Update summary card
    $("summaryCoding").innerText = `${(prob * 100).toFixed(1)}%`;
}

let orfChart = null;

function updateORFChart(orfs) {
    const ctx = $("orfChart");

    if (orfChart) orfChart.destroy();

    // group longest ORF per frame
    const frames = [0, 0, 0];

    orfs.forEach(o => {
    if (typeof o.frame === "number") {
        const idx = o.frame - 1;
        frames[idx] = Math.max(frames[idx], o.aa_length * 3);
    }
    });

    orfChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["+1 (forward)", "+2 (forward)", "+3 (forward)"],
            datasets: [{
                label: "Longest ORF (bp)",
                data: frames,
                backgroundColor: [
                    "#E0C48A",
                    "#6F8CCF",
                    "#A37B3F"
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { ticks: { color: "#C5C7D3" } },
                x: { ticks: { color: "#C5C7D3" } }
            }
        }
    });


    const list = $("orfList");
    list.innerHTML = "";

    if (orfs.length === 0) {
        list.innerHTML = `<p class="text-textDim">No ORFs detected.</p>`;

        $("summaryORFs").innerText = "0";
        return;
    }

    orfs.forEach((o, i) => {
        list.innerHTML += `
            <p class="text-textSoft mb-1">
                <span class="text-champagne font-semibold">ORF ${i + 1}</span>  
                | Frame: ${o.frame} 
                | ${o.start_nt} → ${o.end_nt}
                | ${o.aa_length * 3} bp
            </p>
        `;
    });
    

    $("summaryORFs").innerText = orfs.length.toString();
}



async function analyzeSequence() {
    const seq = $("seqInput").value.trim();
    if (!seq) { notify("Please enter a DNA sequence."); throw new Error("Empty sequence"); }

    const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sequence: seq })
    });

    const analysis = await res.json();
    if (analysis.error) { notify(analysis.error); throw new Error(analysis.error); }

    lastSequenceId = analysis.sequence_id;


    globalAnalysisData.gc = analysis;
    globalAnalysisData.orfs = analysis.orfs_ui;


    updateGCChart(analysis.gc_percent);
    updateORFChart(analysis.orfs_ui);
}


async function runCodingClassifier() {
    const seq = $("seqInput").value.trim();

    
    const res = await fetch("/api/predict_coding", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sequence: seq, sequence_id: lastSequenceId })
    });

    const data = await res.json();
    if (data.error) return notify(data.error);


    globalAnalysisData.ml = data;

    updateMLProbability(data.probability);
}


async function runPromoterAnalysis() {
    const seq = $("seqInput").value.trim();
    if (!lastSequenceId) return;

    const res = await fetch("/api/predict_promoter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sequence: seq, sequence_id: lastSequenceId })
    });

    const data = await res.json();
    

    globalAnalysisData.promoter = data;

    renderPromoterResult(data);
}

async function loadBatchGcDistribution(batchId) {
    const res = await fetch(`/api/batches/${batchId}/gc_distribution`);
    const data = await res.json();

    const gcValues = data.gc_values;
    renderGcHistogram(gcValues);
}

function buildHistogram(values, binSize = 5) {
    const bins = {};
    for (let i = 0; i <= 100; i += binSize) {
        bins[`${i}-${i + binSize}`] = 0;
    }

    values.forEach(v => {
        const bin = Math.floor(v / binSize) * binSize;
        const key = `${bin}-${bin + binSize}`;
        if (bins[key] !== undefined) {
            bins[key]++;
        }
    });

    return {
        labels: Object.keys(bins),
        counts: Object.values(bins)
    };
}

function renderGcHistogram(gcValues) {
    const ctx = document.getElementById("batchGcChart");

    const { labels, counts } = buildHistogram(gcValues);

    if (window.batchGcChart) {
        window.batchGcChart.destroy();
    }

    window.batchGcChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Sequences",
                data: counts,
                backgroundColor: "rgba(218, 165, 32, 0.7)",
                borderColor: "rgba(218, 165, 32, 1)",
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    title: { display: true, text: "GC % Range" }
                },
                y: {
                    title: { display: true, text: "Count" },
                    beginAtZero: true
                }
            }
        }
    });
}


function computeFrequency(arr) {
    const freq = {};
    arr.forEach(v => {
        freq[v] = (freq[v] || 0) + 1;
    });
    return freq;
}

async function renderBatchOrfChart(batchId) {
    const res = await fetch(`/api/batches/${batchId}/orfs`);
    const data = await res.json();

    const lengths = data.orf_lengths;
    if (!lengths || lengths.length === 0) return;

    const freq = computeFrequency(lengths);

    const labels = Object.keys(freq).sort((a, b) => a - b);
    const counts = labels.map(l => freq[l]);

    drawBatchOrfChart(labels, counts);
}   


let batchOrfChart = null;

function drawBatchOrfChart(labels, counts) {
    const ctx = document.getElementById("batchOrfChart");
    if (!ctx) return;

    if (batchOrfChart) batchOrfChart.destroy();

    batchOrfChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "ORF Count",
                data: counts,
                backgroundColor: "rgba(255, 200, 120, 0.7)",
                borderColor: "rgba(255, 200, 120, 1)",
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "ORF Length (aa)"
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: "Frequency"
                    }
                }
            }
        }
    });
}


async function renderBatchPromoterChart(batchId) {
    const res = await fetch(`/api/batches/${batchId}/promoter_summary`);
    const data = await res.json();

    const counts = data.counts;
    drawBatchPromoterChart(
        ["Promoter", "Non-Promoter"],
        [counts.promoter, counts.non_promoter]
    );
}

let batchPromoterChart = null;

function drawBatchPromoterChart(labels, values) {
    const ctx = document.getElementById("batchPromoterChart");
    if (!ctx) return;

    if (batchPromoterChart) batchPromoterChart.destroy();

    batchPromoterChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    "rgba(120, 220, 180, 0.85)",
                    "rgba(220, 120, 120, 0.85)"
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "bottom"
                }
            }
        }
    });
}

async function renderBatchConfidence(batchId) {
    const res = await fetch(
        `/api/batches/${batchId}/confidence_distribution?model=coding`
    );
    const data = await res.json();
    drawConfidenceHistogram(data.confidences);
}
function drawConfidenceHistogram(values) {
    const bins = Array(10).fill(0); // 0.0–1.0 in 0.1 steps

    values.forEach(v => {
        const idx = Math.min(Math.floor(v * 10), 9);
        bins[idx]++;
    });

    const labels = bins.map((_, i) =>
        `${(i/10).toFixed(1)}–${((i+1)/10).toFixed(1)}`
    );

    const ctx = document.getElementById("batchConfidenceChart");
    if (!ctx) return;

    new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Prediction Count",
                data: bins,
                backgroundColor: "rgba(100, 180, 255, 0.85)"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

let promoterChart = null;

function updatePromoterGauge(prob) {
    const ctx = $("promoterGauge");

    if (promoterChart) promoterChart.destroy();

    promoterChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: ["Promoter", "Other"],
            datasets: [{
                data: [prob, 1 - prob],
                backgroundColor: ["#E0C48A", "#242733"],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: "70%",
            plugins: { legend: { display: false } }
        }
    });
}
function renderPromoterResult(data) {

    const status = $("promoterStatus");
    const reason = $("promoterReason");
    const motifList = $("motifList");
    const gauge = $("promoterGauge");

    if (!status || !reason || !motifList || !gauge) {
        console.warn("Promoter UI elements missing");
        return;
    }

    updatePromoterGauge(data.probability);

    if (data.is_promoter) {
        status.innerHTML = `<span class="text-champagne">Promoter Found</span>`;
        reason.innerText =
            `High confidence (${(data.probability * 100).toFixed(1)}%) due to motif presence`;
        // Update summary card with professional wording
        $("summaryPromoter").innerText = "Detected";
    } else {
        status.innerHTML = `<span class="text-textDim">No Promoter Detected</span>`;
        reason.innerText =
            `Low probability (${(data.probability * 100).toFixed(1)}%)`;
        // Update summary card with professional wording
        $("summaryPromoter").innerText = "Not Found";
    }

    motifList.innerHTML = "";

    ["-35", "-10"].forEach(key => {
        if (!data.motifs[key] || data.motifs[key].length === 0) {
            motifList.innerHTML += `<p>${key} motif: not found</p>`;
        } else {
            data.motifs[key].forEach(m => {
                motifList.innerHTML += `
                    <p>
                        <span class="text-champagne">${key}</span>
                        at ${m.pos}: ${m.seq}
                    </p>
                `;
            });
        }
    });
}




