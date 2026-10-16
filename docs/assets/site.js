// Layer.is docs: theme toggle, mobile menu, sidebar section highlighting,
// before/after sliders, copy buttons, the look switcher, the examples filter
// and the blend-mode "peek" at the base photo.

const root = document.documentElement;
const THEME_KEY = "layeris-docs-theme";
const prefersDark = matchMedia("(prefers-color-scheme: dark)");
const wideScreen = matchMedia("(min-width: 880px)");

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

const currentTheme = () => root.dataset.theme || (prefersDark.matches ? "dark" : "light");
const themeToggles = document.querySelectorAll("[data-theme-toggle]");

function labelThemeToggles() {
  const label = currentTheme() === "dark" ? "Switch to light theme" : "Switch to dark theme";
  for (const button of themeToggles) {
    button.setAttribute("aria-label", label);
    button.title = label;
  }
}

for (const button of themeToggles) {
  button.addEventListener("click", () => {
    const theme = currentTheme() === "dark" ? "light" : "dark";
    root.dataset.theme = theme;
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {}
    labelThemeToggles();
  });
}
prefersDark.addEventListener("change", labelThemeToggles);
labelThemeToggles();

// ---------------------------------------------------------------------------
// Mobile menu: the sidebar becomes a full-screen panel below the header
// ---------------------------------------------------------------------------

const menuToggle = document.querySelector("[data-menu-toggle]");
const sidebar = document.querySelector(".sidebar");

function setMenu(open) {
  root.classList.toggle("menu-open", open);
  menuToggle.setAttribute("aria-expanded", String(open));
  menuToggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
}

if (menuToggle && sidebar) {
  menuToggle.addEventListener("click", () => setMenu(!root.classList.contains("menu-open")));
  sidebar.addEventListener("click", (event) => {
    if (event.target.closest("a")) setMenu(false);
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && root.classList.contains("menu-open")) {
      setMenu(false);
      menuToggle.focus();
    }
  });
  wideScreen.addEventListener("change", () => setMenu(false));
}

// ---------------------------------------------------------------------------
// Highlight the section in view in the sidebar
// ---------------------------------------------------------------------------

const sectionLinks = [...document.querySelectorAll(".sidenav__sections a[href^='#']")];
const sectionTargets = sectionLinks.map((link) =>
  document.getElementById(decodeURIComponent(link.hash.slice(1))),
);
let activeLink = null;

function keepInView(link) {
  if (!wideScreen.matches) return;
  const box = sidebar.getBoundingClientRect();
  const rect = link.getBoundingClientRect();
  if (rect.top < box.top + 80) sidebar.scrollTop -= box.top + 80 - rect.top;
  else if (rect.bottom > box.bottom - 80) sidebar.scrollTop += rect.bottom - box.bottom + 80;
}

function updateActiveSection() {
  const offset = (wideScreen.matches ? 24 : 76) + 48;
  const atEnd = innerHeight + scrollY >= root.scrollHeight - 4;
  let current = null;
  sectionTargets.forEach((target, i) => {
    if (!target || !target.getClientRects().length) return; // hidden by the filter
    const top = target.getBoundingClientRect().top;
    if (top - offset <= 0 || (atEnd && top < innerHeight * 0.5)) current = sectionLinks[i];
  });
  if (current === activeLink) return;
  activeLink?.classList.remove("is-active");
  current?.classList.add("is-active");
  activeLink = current;
  if (current) keepInView(current);
}

if (sectionLinks.length) {
  let pending = 0;
  addEventListener(
    "scroll",
    () => {
      if (pending) return;
      pending = setTimeout(() => {
        pending = 0;
        updateActiveSection();
      }, 60);
    },
    { passive: true },
  );
  addEventListener("resize", updateActiveSection);
  addEventListener("load", updateActiveSection);
  updateActiveSection();
}

// ---------------------------------------------------------------------------
// Before/after sliders: drag anywhere on the photo, or use the arrow keys
// ---------------------------------------------------------------------------

for (const slider of document.querySelectorAll(".compare")) {
  const range = slider.querySelector(".compare__range");
  const set = (value) => {
    const pos = Math.min(100, Math.max(0, value));
    slider.style.setProperty("--pos", `${pos}%`);
    range.value = String(Math.round(pos));
  };
  const fromPointer = (event) => {
    const box = slider.getBoundingClientRect();
    set(((event.clientX - box.left) / box.width) * 100);
  };

  range.addEventListener("input", () => set(Number(range.value)));
  slider.addEventListener("pointerdown", (event) => {
    event.preventDefault(); // keep focus on the range so the arrow keys work after a drag
    slider.setPointerCapture(event.pointerId);
    fromPointer(event);
    range.focus({ preventScroll: true });
  });
  slider.addEventListener("pointermove", (event) => {
    if (slider.hasPointerCapture(event.pointerId)) fromPointer(event);
  });
}

// ---------------------------------------------------------------------------
// Copy buttons
// ---------------------------------------------------------------------------

for (const button of document.querySelectorAll("[data-copy]")) {
  button.addEventListener("click", async () => {
    const code = button.parentElement.querySelector("pre").innerText;
    try {
      await navigator.clipboard.writeText(code);
      button.textContent = "Copied";
    } catch {
      button.textContent = "Press Ctrl+C";
    }
    setTimeout(() => {
      button.textContent = "Copy";
    }, 1600);
  });
}

// ---------------------------------------------------------------------------
// Look switcher on the overview page
// ---------------------------------------------------------------------------

for (const looks of document.querySelectorAll("[data-looks]")) {
  const tabs = looks.querySelectorAll(".looks__tab");
  for (const tab of tabs) {
    tab.addEventListener("click", () => {
      const key = tab.dataset.look;
      for (const other of tabs) other.setAttribute("aria-pressed", String(other === tab));
      for (const el of looks.querySelectorAll("img[data-look], .looks__panel")) {
        el.hidden = el.dataset.look !== key;
      }
    });
  }
}

// ---------------------------------------------------------------------------
// Examples: filter the recipes by the layeris method they use
// ---------------------------------------------------------------------------

const filter = document.querySelector("[data-filter]");
if (filter) {
  const recipes = [...document.querySelectorAll(".recipe[data-uses]")];
  const categories = [...document.querySelectorAll("[data-category]")];
  const buttons = [...filter.querySelectorAll(".filter__btn")];
  const summary = filter.querySelector(".filter__summary");
  const summaryText = summary.querySelector("[data-filter-summary]");
  const summaryRef = summary.querySelector("[data-filter-ref]");
  let current = "";

  const apply = (key) => {
    current = key;
    for (const button of buttons) {
      button.setAttribute("aria-pressed", String(button.dataset.filterKey === key));
    }
    for (const recipe of recipes) {
      recipe.hidden = Boolean(key) && !recipe.dataset.uses.split(" ").includes(key);
    }
    let shown = 0;
    for (const category of categories) {
      const visible = [...category.querySelectorAll(".recipe")].filter((r) => !r.hidden);
      visible.forEach((recipe, i) => recipe.classList.toggle("recipe--first", i === 0));
      category.hidden = visible.length === 0;
      shown += visible.length;
      const link = document.querySelector(`[data-category-link="${category.id}"]`);
      if (link) {
        link.hidden = category.hidden;
        link.querySelector(".toc__count").textContent = String(visible.length);
      }
    }
    const active = key && buttons.find((button) => button.dataset.filterKey === key);
    summary.hidden = !active;
    if (active) {
      summaryText.textContent =
        `${shown} of ${recipes.length} examples use ${active.dataset.filterName}.`;
      summaryRef.href = active.dataset.filterRef;
      summaryRef.textContent = active.dataset.filterRefLabel;
    }
    updateActiveSection();
  };

  for (const button of buttons) {
    button.addEventListener("click", () => {
      const key = button.dataset.filterKey;
      apply(key === current ? "" : key);
    });
  }
  for (const button of document.querySelectorAll(".uses__btn")) {
    button.addEventListener("click", () => {
      apply(button.dataset.filterKey);
      filter.scrollIntoView({ block: "start" });
    });
  }
  filter.querySelector("[data-filter-clear]").addEventListener("click", () => apply(""));
}

// ---------------------------------------------------------------------------
// Blend modes: press and hold a result to see the base photo (hover works
// through CSS on devices with a mouse)
// ---------------------------------------------------------------------------

for (const peek of document.querySelectorAll(".peek")) {
  const off = () => peek.classList.remove("is-peeking");
  peek.addEventListener("pointerdown", () => peek.classList.add("is-peeking"));
  for (const type of ["pointerup", "pointerleave", "pointercancel"]) {
    peek.addEventListener(type, off);
  }
  peek.addEventListener("contextmenu", (event) => event.preventDefault());
}
