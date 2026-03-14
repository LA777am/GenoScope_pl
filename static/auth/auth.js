document.addEventListener("DOMContentLoaded", () => {
    
    // 1. Maintain the cool Reticule Mouse Tracker
    const reticule = document.getElementById('reticule');
    if (reticule) {
        document.addEventListener('mousemove', (e) => {
            const x = e.clientX;
            const y = e.clientY;

            setTimeout(() => {
                reticule.style.left = x + 'px';
                reticule.style.top = y + 'px';
            }, 50);
        });
    }

    // 2. Initial Boot Sequence Text
    const statusText = document.getElementById('systemStatus');
    if (statusText) {
        setTimeout(() => {
            statusText.innerText = "AWAITING BIO-SIGNATURE (OAUTH)";
        }, 1500);
    }
});

// 3. THE GOOGLE CALLBACK (Must be attached to 'window' so Google's script can trigger it)
window.handleCredentialResponse = async function(response) {
    const statusText = document.getElementById('systemStatus');
    const statusDot = document.getElementById('statusDot');

    // Change terminal to "working" state
    if (statusText) {
        statusText.innerText = "VERIFYING CRYPTOGRAPHIC TOKEN...";
        statusText.style.color = "var(--champagne)";
    }
    if (statusDot) {
        statusDot.style.backgroundColor = "var(--champagne)";
        statusDot.style.boxShadow = "0 0 10px var(--champagne)";
    }

    try {
        // Send Google JWT to Python Backend
        const res = await fetch('/auth/google', {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ credential: response.credential })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.error || "AUTH FAILED");
        }

        // --- THE LOADING FORWARD LOGIC ---
        if (data.success) {
            
            // Terminal Success State
            if (statusText) {
                statusText.innerText = "ACCESS GRANTED. INITIALIZING...";
                statusText.style.color = "var(--cyan)";
            }
            if (statusDot) {
                statusDot.style.backgroundColor = "var(--cyan)";
                statusDot.style.boxShadow = "0 0 10px var(--cyan)";
            }

            // Cinematic fade-out
            document.body.style.transition = "opacity 0.8s ease";
            document.body.style.opacity = 0;

            // Redirect to dashboard (mode-select)
            setTimeout(() => {
                window.location.href = "/mode-select";
            }, 800);
            
        } else {
            throw new Error(data.error || "UNKNOWN ERROR");
        }

    } catch (err) {
        // Terminal Error State
        if (statusText) {
            statusText.innerText = "ACCESS DENIED: " + err.message;
            statusText.style.color = "var(--danger)";
        }
        if (statusDot) {
            statusDot.style.backgroundColor = "var(--danger)";
            statusDot.style.boxShadow = "0 0 10px var(--danger)";
        }
    }
};