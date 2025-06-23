document.addEventListener("DOMContentLoaded", () => {
  const drop = document.querySelector("[data-drop]");
  if (!drop) return;

  const btn  = drop.querySelector(".filter-toggle");
  const menu = drop.querySelector(".filter-menu");

  function openMenu() {
    menu.hidden = false;
    btn.setAttribute("aria-expanded", "true");

    const natural = menu.scrollWidth;
    menu.style.width = natural + "px";
  }

  function closeMenu() {
    menu.hidden = true;
    btn.setAttribute("aria-expanded", "false");
  }

  btn.addEventListener("click", () =>
    menu.hidden ? openMenu() : closeMenu()
  );

  document.addEventListener("click", (e) => {
    if (!drop.contains(e.target)) closeMenu();
  });

  menu.addEventListener("change", () => {
    if (window.matchMedia("(max-width: 640px)").matches) closeMenu();
  });
});