document.addEventListener("DOMContentLoaded", () => {
  const drop = document.querySelector("[data-drop]");
  if (!drop) return;

  const btn  = drop.querySelector(".filter-toggle");
  const menu = drop.querySelector(".filter-menu");

  btn.addEventListener("click", () => {
    const open = menu.hidden;
    menu.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
  });

  document.addEventListener("click", (e) => {
    if (!drop.contains(e.target)) {
      menu.hidden = true;
      btn.setAttribute("aria-expanded", "false");
    }
  });

  menu.addEventListener("change", () => {
    if (window.matchMedia("(max-width: 640px)").matches) {
      menu.hidden = true;
      btn.setAttribute("aria-expanded", "false");
    }
  });
});