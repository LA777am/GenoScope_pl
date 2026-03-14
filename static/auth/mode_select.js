document.addEventListener("DOMContentLoaded", () => {
  // --- 1. SELECTIONS ---
  const cards = document.querySelectorAll(".tech-card");
  const reticule = document.getElementById("reticule");
  const container = document.querySelector(".modules-container");

  // --- 2. RETICULE MOVEMENT LOGIC ---
  document.addEventListener("mousemove", (e) => {
    // Cinematic lag effect (40ms)
    setTimeout(() => {
      if (reticule) {
        reticule.style.left = `${e.clientX}px`;
        reticule.style.top = `${e.clientY}px`;
      }
    }, 40);

    // Hover detection to change reticule shape
    const hovered = e.target.closest(".tech-card");
    if (hovered) {
      reticule.classList.add("active");
    } else {
      reticule.classList.remove("active");
    }
  });

  // --- 3. CARD CLICK / NAVIGATION LOGIC ---
  cards.forEach(card => {
    card.addEventListener("click", () => {
      const target = card.dataset.target; // Gets /single, /batch, /compare, or /mutation
      
      // A. Visual Feedback - Freeze Cursor
      document.body.style.cursor = "wait";
      
      // B. Dim other cards (Focus effect)
      cards.forEach(c => {
        if (c !== card) c.classList.add("module-dimmed");
      });

      // C. Highlight Selected Card
      card.classList.add("module-selected");
      
      // D. Update Button Text
      const btn = card.querySelector(".btn-activate");
      if (btn) btn.innerText = "SYSTEM MOUNTED";
      
      // E. Execute Navigation with Delay (Cinematic Wait)
      setTimeout(() => {
        // Optional: Fade out body for smooth transition
        document.body.style.opacity = "0";
        document.body.style.transition = "opacity 0.5s ease";

        setTimeout(() => {
          window.location.href = target;
        }, 100);
      }, 800);
    });
  });

  // --- 4. LOGOUT LOGIC (Restored Exact) ---
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {

          // 1. Visual Feedback
          logoutBtn.style.pointerEvents = "none";
          const textLabel = logoutBtn.querySelector(".label-hover");
          const icon = logoutBtn.querySelector(".power-housing");
          
          if(textLabel) textLabel.innerText = "BYE...";
          if(icon) icon.style.opacity = "0.5";

          // 2. Perform Logout Request
          try {
              await fetch("/auth/logout", { method: "POST" });
          } catch (err) {
              console.warn("Logout fetch failed, forcing redirect anyway.");
          }

          // 3. Redirect
          setTimeout(() => {
              window.location.href = "/auth";
          }, 500);
      });
  }
});