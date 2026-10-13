// Layer.is docs: before/after sliders, copy buttons and the look switcher.

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
    slider.setPointerCapture(event.pointerId);
    fromPointer(event);
    range.focus({ preventScroll: true });
  });
  slider.addEventListener("pointermove", (event) => {
    if (slider.hasPointerCapture(event.pointerId)) fromPointer(event);
  });
}

for (const button of document.querySelectorAll("[data-copy]")) {
  button.addEventListener("click", async () => {
    const code = button.parentElement.querySelector("pre").innerText;
    try {
      await navigator.clipboard.writeText(code);
      button.textContent = "Copied";
    } catch {
      button.textContent = "Press Ctrl+C";
    }
    button.dataset.copied = "";
    setTimeout(() => {
      button.textContent = "Copy";
      delete button.dataset.copied;
    }, 1600);
  });
}

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
