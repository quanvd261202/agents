/* Deterministic DOM checks. Runs in page; returns findings the verifier treats as authoritative. */
(() => {
  const out = [];
  const add = (severity, dimension, target, issue, suggestion, data) =>
    out.push({ severity, dimension, target, issue, suggestion, data: data || {} });

  const nodeId = (el) => { const n = el.closest("[data-node]"); return n ? n.getAttribute("data-node") : "page"; };
  const visible = (el) => { const s = getComputedStyle(el); const r = el.getBoundingClientRect();
    return s.display !== "none" && s.visibility !== "hidden" && s.opacity !== "0" && r.width > 0 && r.height > 0; };

  /* 1. render errors reported by the React boundary */
  for (const e of (window.__uibErrors || []))
    add("critical", "layout", e.node, `component failed to render: ${e.message}`, `fix or replace ${e.implementation}`, e);

  /* 2. horizontal overflow of the document and of individual elements */
  const docW = document.documentElement.clientWidth;
  if (document.documentElement.scrollWidth > docW + 1)
    add("critical", "layout", "page", `page scrolls horizontally (${document.documentElement.scrollWidth}px > ${docW}px)`,
        "reduce columns or allow the layout to collapse at this breakpoint", { scrollWidth: document.documentElement.scrollWidth, clientWidth: docW });
  const transformed = (el) => { let n = el; while (n && n !== document.documentElement) {
      if (getComputedStyle(n).transform !== "none") return true; n = n.parentElement; } return false; };
  for (const el of document.querySelectorAll("[data-node]")) {
    if (!visible(el) || transformed(el)) continue;
    const r = el.getBoundingClientRect();
    if (r.right > docW + 1 || r.left < -1)
      add("critical", "layout", nodeId(el), `element extends outside the viewport (left ${Math.round(r.left)}px, right ${Math.round(r.right)}px)`,
          "reduce columns or switch to a stacked layout at this breakpoint", { left: r.left, right: r.right });
  }

  /* 3. clipped text: content taller/wider than its scroll container */
  for (const el of document.querySelectorAll("p, h1, h2, h3, td, th, li, button, a, summary")) {
    if (!visible(el)) continue;
    const s = getComputedStyle(el);
    if (s.overflow !== "visible" && el.scrollHeight > el.clientHeight + 2 && s.overflowY !== "auto" && s.overflowY !== "scroll")
      add("major", "layout", nodeId(el), `text is clipped in <${el.tagName.toLowerCase()}>`, "increase the container height or reduce the text", {});
  }

  /* 4. grid tracks too narrow for the content they hold. Columns that do not overflow can still
        be unusable: minmax(0,1fr) happily shrinks a card to 45px and simply wraps the text. */
  const MIN_TRACK = 150;
  for (const el of document.querySelectorAll("[data-node], .uib-grid")) {
    if (!visible(el) || getComputedStyle(el).display !== "grid") continue;
    const tracks = getComputedStyle(el).gridTemplateColumns.split(" ").map(parseFloat).filter((n) => !isNaN(n));
    if (tracks.length < 2 || !el.textContent.trim()) continue;
    const min = Math.min(...tracks);
    if (min < MIN_TRACK)
      add("critical", "layout", nodeId(el), `grid columns are ${Math.round(min)}px wide, too narrow for their content`,
          `reduce the column count at this breakpoint (currently ${tracks.length})`, { columns: tracks.length, trackWidth: min });
  }

  /* 5. contrast (WCAG 2.1 AA) for visible text */
  /* Any CSS colour syntax (rgb, oklab, oklch, color(srgb ...), color-mix results) -> [r, g, b, a].
     Painting one pixel lets the browser do the conversion, so the check never misreads a modern
     colour as rgb numbers. */
  const ctx2d = Object.assign(document.createElement("canvas"), { width: 1, height: 1 }).getContext("2d", { willReadFrequently: true });
  const parseCache = new Map();
  const parse = (c) => {
    if (!c) return null;
    if (parseCache.has(c)) return parseCache.get(c);
    ctx2d.clearRect(0, 0, 1, 1); ctx2d.fillStyle = "#000"; ctx2d.fillStyle = c; ctx2d.fillRect(0, 0, 1, 1);
    const [r, g, b, a] = ctx2d.getImageData(0, 0, 1, 1).data;
    const out = [r, g, b, a / 255];
    parseCache.set(c, out); return out;
  };
  const lum = ([r, g, b]) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const bgOf = (el) => { let n = el; while (n && n !== document.documentElement) {
      const c = parse(getComputedStyle(n).backgroundColor); if (c && c[3] > 0.5) return c; n = n.parentElement; }
    return parse(getComputedStyle(document.body).backgroundColor) || [255, 255, 255, 1]; };
  const seen = new Set();
  for (const el of document.querySelectorAll("p, h1, h2, h3, h4, h5, h6, span, a, button, td, th, li, strong, em, label, summary, legend, dt, dd, figcaption, blockquote, cite, small, output, time")) {
    if (!visible(el) || !el.textContent.trim()) continue;
    if ([...el.children].some((c) => c.textContent.trim() === el.textContent.trim())) continue;
    const s = getComputedStyle(el), fg = parse(s.color), bg = bgOf(el);
    if (!fg || !bg) continue;
    const L1 = lum(fg), L2 = lum(bg), ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    const size = parseFloat(s.fontSize), bold = parseInt(s.fontWeight, 10) >= 700;
    const required = size >= 24 || (size >= 18.66 && bold) ? 3 : 4.5;
    if (ratio < required) {
      const key = nodeId(el) + "|" + s.color + "|" + Math.round(size);
      if (seen.has(key)) continue; seen.add(key);
      add("major", "accessibility", nodeId(el), `text contrast ${ratio.toFixed(2)}:1 is below the ${required}:1 minimum`,
          "use a darker foreground token or a lighter surface token", { ratio: +ratio.toFixed(2), required, fontSize: size });
    }
  }

  /* 6. interactive target size (WCAG 2.5.8, 24x24 CSS px).
        Exceptions: a control wrapped in a large-enough label, and inline links inside running text. */
  for (const el of document.querySelectorAll("button, a, input, select, summary, [role=button]")) {
    if (!visible(el)) continue;
    const r = el.getBoundingClientRect();
    const label = el.closest("label");
    if (label && label !== el) { const lr = label.getBoundingClientRect(); if (lr.width >= 24 && lr.height >= 24) continue; }
    if (el.tagName === "A" && getComputedStyle(el).display === "inline") continue;
    if (r.width < 24 || r.height < 24)
      add("major", "accessibility", nodeId(el), `interactive target is ${Math.round(r.width)}x${Math.round(r.height)}px, below 24x24`,
          "increase padding or min-height on this control", { width: r.width, height: r.height });
  }

  /* 7. accessible names and heading order */
  for (const el of document.querySelectorAll("button, a[href]")) {
    if (!visible(el)) continue;
    const name = (el.getAttribute("aria-label") || el.textContent || "").trim();
    if (!name) add("major", "accessibility", nodeId(el), `<${el.tagName.toLowerCase()}> has no accessible name`, "add visible text or an aria-label", {});
  }
  // A form control is named by aria-*, a wrapping <label> (implicit), or a <label for=id>.
  const NO_LABEL_NEEDED = new Set(["hidden", "submit", "button", "image", "reset"]);
  const labelled = (el) => {
    if (el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") || el.title) return true;
    if (NO_LABEL_NEEDED.has(el.type)) return true;
    if (el.closest("label")) return true;
    const id = el.getAttribute("id");
    return !!(id && document.querySelector(`label[for="${CSS.escape(id)}"]`));
  };
  for (const el of document.querySelectorAll("img:not([alt])"))
    if (visible(el)) add("minor", "accessibility", nodeId(el), "<img> is missing alt text", "add alt text, or alt=\"\" if decorative", {});
  for (const el of document.querySelectorAll("input, select, textarea"))
    if (visible(el) && !labelled(el))
      add("minor", "accessibility", nodeId(el), `<${el.tagName.toLowerCase()}> has no associated label`, "wrap it in a <label>, point a <label for> at it, or add an aria-label", {});
  const h1s = [...document.querySelectorAll("h1")].filter(visible);
  if (h1s.length === 0) add("major", "ux", "page", "the screen has no level-1 heading", "give the primary section a headline", {});
  if (h1s.length > 1) add("minor", "visual", "page", `the screen has ${h1s.length} level-1 headings`, "demote secondary headings to h2", {});

  /* 8. empty sections */
  for (const el of document.querySelectorAll("[data-node]")) {
    if (!visible(el)) continue;
    if (el.getBoundingClientRect().height < 8 && !el.querySelector("[data-node]"))
      add("major", "layout", nodeId(el), "section renders with almost no height", "check that the component received content", {});
  }

  /* 9. motion: layout stability, main-thread cost, and the continuous-animation budget */
  const perf = window.__uibPerf;
  if (perf && perf.cls > 0.1)
    add("major", "layout", "page", `cumulative layout shift ${perf.cls.toFixed(3)} exceeds 0.1`,
        "reserve space for content that loads or animates in", { cls: perf.cls });
  if (perf && perf.longTaskMs > 400)
    add("minor", "ux", "page", `the main thread was blocked for ${Math.round(perf.longTaskMs)}ms while loading`,
        "reduce the script and animation work done on load", { longTaskMs: perf.longTaskMs });
  const marquees = new Set(document.getAnimations()
    .filter((a) => a.animationName === "uib-marquee" && a.playState === "running")
    .map((a) => a.effect && a.effect.target && a.effect.target.parentElement)).size;
  const loops = ((window.__uibMotion && window.__uibMotion.peakContinuous) || 0) + marquees;
  if (loops > 4)
    add("major", "ux", "page", `${loops} continuous animations run at once (budget 4)`,
        "keep ambient motion to one or two per page", { loops });

  return {
    findings: out,
    outline: [...document.querySelectorAll("[data-node]")].filter(visible).map((el) => {
      const r = el.getBoundingClientRect();
      return { id: el.getAttribute("data-node"), semantic: el.getAttribute("data-semantic") || "",
               top: Math.round(r.top + window.scrollY), height: Math.round(r.height), width: Math.round(r.width) };
    }),
    documentHeight: document.documentElement.scrollHeight,
  };
})();
