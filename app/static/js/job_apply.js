document.addEventListener("DOMContentLoaded", () => {
  const drawer = document.getElementById("apply-drawer");
  const overlay = document.querySelector(".apply-overlay");
  if (!drawer) return;
  const openDrawer = () => {
    drawer.hidden = false;
    overlay.hidden = false;
    document.body.classList.add("lock");
    drawer.querySelector("input, select, textarea")?.focus();
  };
  const closeDrawer = () => {
    drawer.hidden = true;
    overlay.hidden = true;
    document.body.classList.remove("lock");
  };
  document.querySelectorAll("[data-open-apply]").forEach(button => button.addEventListener("click", openDrawer));
  document.querySelectorAll("[data-close-apply]").forEach(button => button.addEventListener("click", closeDrawer));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") closeDrawer();
  });
});
