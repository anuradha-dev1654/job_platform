(() => {
  const form = document.getElementById("reg-form");
  if (!form) return;

  const $ = id => document.getElementById(id);
  const steps = [...form.querySelectorAll(".step")];
  const tabs = [...document.querySelectorAll("[data-step-tab]")];
  const csrf = form.querySelector("input[name=csrf_token]").value;

  const FREE = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "rediffmail.com", "proton.me", "protonmail.com"];
  const ID_RE = {
    PAN: /^[A-Z]{5}[0-9]{4}[A-Z]$/,
    GST: /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/,
    CIN: /^[LU][0-9]{5}[A-Z]{2}[0-9]{4}[A-Z]{3}[0-9]{6}$/,
  };
  const MAX = 5 * 1024 * 1024;
  const OK_EXT = [".pdf", ".png", ".jpg", ".jpeg"];

  let current = 1;
  let verifiedEmail = (form.dataset.verifiedEmail || "").toLowerCase();

  /* ---------- error helpers ---------- */
  const holder = el => el.closest(".fld, .doc") || el.parentElement;
  function clearError(el) {
    holder(el).querySelectorAll(".err").forEach(n => n.remove());
    el.removeAttribute("aria-invalid");
  }
  function setError(el, msg) {
    clearError(el);
    const p = document.createElement("p");
    p.className = "err";
    p.setAttribute("role", "alert");
    p.textContent = msg;
    holder(el).appendChild(p);
    el.setAttribute("aria-invalid", "true");
  }
  form.addEventListener("input", e => clearError(e.target));
  form.addEventListener("change", e => clearError(e.target));

  /* ---------- steps ---------- */
  function show(n) {
    current = n;
    steps.forEach((s, i) => (s.hidden = i !== n - 1));
    tabs.forEach((t, i) => {
      t.classList.toggle("is-current", i === n - 1);
      t.classList.toggle("is-done", i < n - 1);
    });
    $("summary-email").textContent = verifiedEmail ? "Email verified: " + verifiedEmail : "Email not verified";
    window.scrollTo({ top: form.closest(".reg").offsetTop - 10, behavior: "smooth" });
  }

  function fileProblem(f) {
    const ext = f.name.slice(f.name.lastIndexOf(".")).toLowerCase();
    if (!OK_EXT.includes(ext)) return "Only PDF, PNG or JPG files are allowed.";
    if (f.size > MAX) return "File must be 5 MB or smaller.";
    return "";
  }

  function validateStep(n) {
    const sec = steps[n - 1];
    let first = null;
    const fail = (el, msg) => { setError(el, msg); first = first || el; };
    const clean = el => !el.hasAttribute("aria-invalid");

    sec.querySelectorAll("[data-req]").forEach(el => {
      clearError(el);
      if (el.type === "file") {
        if (!el.files.length) return fail(el, "Upload this document.");
        const p = fileProblem(el.files[0]);
        if (p) fail(el, p);
      } else if (el.type === "checkbox") {
        if (!el.checked) fail(el, "Please tick this box to continue.");
      } else if (!el.value.trim()) {
        fail(el, "This field is required.");
      }
    });

    if (n === 1) {
      const em = $("rep_email"), val = em.value.trim().toLowerCase();
      if (clean(em)) {
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(val)) {
          fail(em, "Enter a valid company email.");
        }
      }
    }
    if (n === 2) {
      const type = $("corporate_id_type").value, id = $("corporate_id");
      if (id.value.trim() && type && clean(id) && !ID_RE[type].test(id.value.trim().toUpperCase())) fail(id, `Enter a valid ${type} number.`);
      const site = $("website");
      if (site.value.trim() && clean(site)) { try { const u = new URL(site.value.trim()); if (!/^https?:$/.test(u.protocol)) throw 0; } catch { fail(site, "Enter the full address, e.g. https://example.com"); } }
      const ph = $("phone");
      if (ph.value.trim() && clean(ph) && !/^[6-9]\d{9}$/.test(ph.value.trim())) fail(ph, "Enter a valid 10-digit mobile number.");
    }
    if (n === 4) {
      const pw = $("password"), cf = $("confirm_password");
      if (clean(pw) && pw.value.length < 8) fail(pw, "Password must be at least 8 characters.");
      if (clean(cf) && cf.value !== pw.value) fail(cf, "Passwords do not match.");
    }

    if (first) first.focus();
    return !first;
  }

  form.querySelectorAll("[data-next]").forEach(b => b.addEventListener("click", () => { if (validateStep(current)) show(current + 1); }));
  form.querySelectorAll("[data-back]").forEach(b => b.addEventListener("click", () => show(current - 1)));
  tabs.forEach((t, i) => t.addEventListener("click", () => { if (i + 1 < current) show(i + 1); }));

  form.addEventListener("submit", e => {
    for (let n = 1; n <= 4; n++) {
      if (!validateStep(n)) { e.preventDefault(); show(n); return; }
    }
    const btn = $("submit-btn");
    btn.disabled = true;
    btn.textContent = "Submitting…";
  });

  /* ---------- OTP ---------- */
  const emailEl = $("rep_email"), sendBtn = $("send-otp"), verifyBtn = $("verify-otp");
  const otpRow = $("otp-row"), otpEl = $("otp"), status = $("email-status");
  let timer = null;

  async function post(url, body) {
    try {
      const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": csrf }, body: JSON.stringify(body) });
      const d = await r.json().catch(() => ({}));
      return { ok: r.ok && d.ok, error: d.error || "Something went wrong. Try again." };
    } catch { return { ok: false, error: "Network error. Check your connection." }; }
  }

  function cooldown(sec) {
    let s = sec;
    sendBtn.disabled = true;
    sendBtn.textContent = `Resend in ${s}s`;
    clearInterval(timer);
    timer = setInterval(() => {
      if (--s <= 0) { clearInterval(timer); sendBtn.disabled = false; sendBtn.textContent = "Resend OTP"; }
      else sendBtn.textContent = `Resend in ${s}s`;
    }, 1000);
  }

  function markVerified() {
    status.hidden = false;
    status.textContent = "Email verified";
    otpRow.hidden = true;
    clearInterval(timer);
    sendBtn.disabled = true;
    sendBtn.textContent = "Verified";
  }
  function resetVerified() {
    verifiedEmail = "";
    status.hidden = true;
    sendBtn.disabled = false;
    sendBtn.textContent = "Send OTP";
  }

  sendBtn.addEventListener("click", async () => {
    const val = emailEl.value.trim().toLowerCase();
    clearError(emailEl);
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(val) || FREE.includes(val.split("@")[1])) {
      return setError(emailEl, "Use your official company email, not Gmail or Yahoo.");
    }
    sendBtn.disabled = true;
    const res = await post(form.dataset.sendUrl, { email: val });
    if (!res.ok) { sendBtn.disabled = false; return setError(emailEl, res.error); }
    otpRow.hidden = false;
    otpEl.value = "";
    otpEl.focus();
    cooldown(30);
  });

  verifyBtn.addEventListener("click", async () => {
    const val = emailEl.value.trim().toLowerCase(), code = otpEl.value.trim();
    clearError(otpEl);
    if (!/^\d{6}$/.test(code)) return setError(otpEl, "Enter the 6-digit code.");
    verifyBtn.disabled = true;
    const res = await post(form.dataset.verifyUrl, { email: val, otp: code });
    verifyBtn.disabled = false;
    if (!res.ok) return setError(otpEl, res.error);
    verifiedEmail = val;
    markVerified();
  });

  emailEl.addEventListener("input", () => {
    if (verifiedEmail && emailEl.value.trim().toLowerCase() !== verifiedEmail) resetVerified();
  });
  if (verifiedEmail && emailEl.value.trim().toLowerCase() === verifiedEmail) markVerified();

  /* ---------- company logo preview ---------- */
  const logoInput = $("company_logo");
  const logoPreview = document.querySelector("[data-logo-preview]");
  if (logoInput && logoPreview) {
    logoInput.addEventListener("change", () => {
      const file = logoInput.files[0];
      if (!file) {
        logoPreview.textContent = "CB";
        logoPreview.innerHTML = "CB";
        return;
      }
      if (![".jpg", ".jpeg", ".png"].includes(file.name.slice(file.name.lastIndexOf(".")).toLowerCase())) {
        setError(logoInput, "Upload a JPG or PNG logo.");
        return;
      }
      if (file.size > MAX) {
        setError(logoInput, "Logo must be 5 MB or smaller.");
        return;
      }
      clearError(logoInput);
      const image = document.createElement("img");
      image.alt = "Company logo preview";
      image.src = URL.createObjectURL(file);
      logoPreview.innerHTML = "";
      logoPreview.append(image);
    });
  }

  /* ---------- document cards: choose or drag & drop ---------- */
  form.querySelectorAll("[data-doc]").forEach(card => {
    const input = card.querySelector("input[type=file]"), state = card.querySelector("[data-state]");
    const update = () => {
      const f = input.files[0];
      card.classList.remove("is-ok");
      if (!f) { state.textContent = "No file chosen. PDF, PNG or JPG, up to 5 MB."; return; }
      const p = fileProblem(f);
      if (p) { setError(input, p); state.textContent = f.name; return; }
      state.textContent = `${f.name} (${(f.size / 1024).toFixed(0)} KB)`;
      card.classList.add("is-ok");
    };
    input.addEventListener("change", update);
    ["dragenter", "dragover"].forEach(ev => card.addEventListener(ev, e => { e.preventDefault(); card.classList.add("is-over"); }));
    ["dragleave", "drop"].forEach(ev => card.addEventListener(ev, e => { e.preventDefault(); card.classList.remove("is-over"); }));
    card.addEventListener("drop", e => {
      if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; update(); }
    });
  });

  /* ---------- show / hide password ---------- */
  form.querySelectorAll("[data-toggle-pass]").forEach(b => b.addEventListener("click", () => {
    const input = $(b.dataset.togglePass), show = input.type === "password";
    input.type = show ? "text" : "password";
    b.textContent = show ? "Hide" : "Show";
  }));

  /* ---------- start: jump to the step that has a server-side error ---------- */
  const firstErr = form.querySelector(".err");
  show(firstErr ? steps.indexOf(firstErr.closest(".step")) + 1 : 1);
})();