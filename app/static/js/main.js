document.addEventListener("DOMContentLoaded", () => {
  /* ---------- mega menus (Jobs / Companies) ---------- */
  const dds = document.querySelectorAll(".dd");
  const closeAll = () => dds.forEach(d => {
    d.classList.remove("open");
    d.querySelector(".dd__btn").setAttribute("aria-expanded", "false");
  });
  dds.forEach(d => {
    const btn = d.querySelector(".dd__btn");
    btn.addEventListener("click", e => {
      e.stopPropagation();
      const willOpen = !d.classList.contains("open");
      closeAll();
      d.classList.toggle("open", willOpen);
      btn.setAttribute("aria-expanded", String(willOpen));
    });
  });
  document.addEventListener("click", e => { if (!e.target.closest(".dd")) closeAll(); });

  /* ---------- login drawer ---------- */
  const drawer = document.getElementById("login-drawer");
  const overlay = document.querySelector(".overlay");
  let opener = null;

  const openLogin = trigger => {
    if (!drawer) return;
    opener = trigger || null;
    drawer.hidden = false;
    overlay.hidden = false;
    document.body.classList.add("lock");
    drawer.querySelector("input[name=email]").focus();
  };
  const closeLogin = () => {
    if (!drawer) return;
    drawer.hidden = true;
    overlay.hidden = true;
    document.body.classList.remove("lock");
    if (opener) opener.focus();
  };

  document.querySelectorAll("[data-open-login]").forEach(b => b.addEventListener("click", () => openLogin(b)));
  document.querySelectorAll("[data-close-login]").forEach(b => b.addEventListener("click", closeLogin));
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") { closeAll(); closeLogin(); }
  });
  // /?login=1 opens the drawer (useful after a protected page redirects here)
  if (new URLSearchParams(location.search).get("login") === "1") openLogin(null);

  /* ---------- show / hide password ---------- */
  document.querySelectorAll("[data-toggle-pass]").forEach(btn => {
    btn.addEventListener("click", () => {
      const input = document.getElementById(btn.getAttribute("aria-controls"));
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "Hide" : "Show";
    });
  });

  /* ---------- companies carousel arrows ---------- */
  const track = document.getElementById("company-track");
  document.querySelectorAll("[data-scroll]").forEach(btn => {
    btn.addEventListener("click", () => {
      if (!track) return;
      track.scrollBy({ left: Number(btn.dataset.scroll) * 480, behavior: "smooth" });
    });

    /* ---------- free-text location suggestions ---------- */
    const locationInput = document.getElementById("s-loc");
    const locationOptions = document.getElementById("location-options");
    let locationTimer = null;
    if (locationInput && locationOptions) {
      const loadLocations = async () => {
        const query = locationInput.value.trim();
        try {
          const response = await fetch(`/api/locations?q=${encodeURIComponent(query)}`);
          if (!response.ok) return;
          const data = await response.json();
          locationOptions.innerHTML = "";
          (data.locations || []).forEach(location => {
            const option = document.createElement("option");
            option.value = location;
            locationOptions.append(option);
          });
        } catch (_) {}
      };
      locationInput.addEventListener("focus", loadLocations);
      locationInput.addEventListener("input", () => {
        clearTimeout(locationTimer);
        locationTimer = setTimeout(loadLocations, 200);
      });
    }
  });
});