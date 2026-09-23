/**
 * The motion runtime: executes the behaviours the resolver's choreographer put on each section
 * (node.motion). Behaviours find their targets through markers the UI primitives set
 * (data-motion-media / -layer / -cta / -card / -item / -number), so every component gains motion
 * without knowing about it.
 *
 * Every behaviour
 *   - does nothing under reduced motion (the entrance's own reduced config still applies),
 *   - registers a finisher, so the renderer can settle the page to its resting state before a
 *     screenshot ("uib:settle"), which keeps captures deterministic,
 *   - returns a cleanup, and never leaves inline styles that would block a component's hover.
 */
import { animate, inView, scroll, stagger } from "motion";

export interface Behavior { name: string; params: Record<string, number | string> }
type Cleanup = () => void;
type Run = (el: HTMLElement, p: Record<string, number | string>) => Cleanup;

const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];
const num = (p: Record<string, number | string>, key: string, fallback: number) =>
  typeof p[key] === "number" ? (p[key] as number) : fallback;

/* ------------------------------------------------------------------ settle + budget bookkeeping */
interface MotionState { settled: boolean; finishers: Set<() => void>; continuous: number; peakContinuous: number }
declare global { interface Window { __uibMotion?: MotionState } }
const state = (): MotionState =>
  (window.__uibMotion ??= { settled: false, finishers: new Set(), continuous: 0, peakContinuous: 0 });

/** Motion commits an animation's final value after complete() returns, so a clean-up that must
 * win runs now and again on the next frame. */
const afterCommit = (fn: () => void) => { fn(); requestAnimationFrame(fn); };

/** Register how to jump a behaviour to its resting state. Runs at once if the page already settled. */
function onSettle(fn: () => void): Cleanup {
  const s = state();
  if (s.settled) { fn(); return () => {}; }
  s.finishers.add(fn);
  return () => s.finishers.delete(fn);
}
function continuous(): Cleanup {
  const s = state();
  s.continuous += 1;
  s.peakContinuous = Math.max(s.peakContinuous, s.continuous);
  return () => { s.continuous -= 1; };
}
export function settleAll() {
  const s = state();
  s.settled = true;
  for (const fn of [...s.finishers]) fn();
  s.finishers.clear();
}

/* ------------------------------------------------------------------ target discovery */
const visible = (e: Element) => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
const largest = (els: Element[]) =>
  [...els].filter(visible).sort((a, b) => {
    const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
    return rb.width * rb.height - ra.width * ra.height;
  });

/** Repeated items: explicit markers, else the container with the most same-kind children. */
function findItems(el: HTMLElement): HTMLElement[] {
  const marked = [...el.querySelectorAll<HTMLElement>("[data-motion-item]")];
  if (marked.length >= 2) return marked;
  let best: HTMLElement[] = [];
  for (const c of el.querySelectorAll<HTMLElement>("ul, ol, div")) {
    if (c.closest("nav, [role=tablist], [aria-roledescription=carousel]")) continue;
    const kids = [...c.children].filter((k): k is HTMLElement => k instanceof HTMLElement && visible(k));
    if (kids.length < 3 || kids.length > 24) continue;
    const tags = new Set(kids.map((k) => k.tagName));
    if (tags.size === 1 && kids.length > best.length) best = kids;
  }
  return best;
}

/* ------------------------------------------------------------------ behaviours */
const stagger_: Run = (el, p) => {
  const items = findItems(el);
  if (items.length < 2) return () => {};
  const d = num(p, "distance", 16), dur = num(p, "duration_ms", 400) / 1000, step = num(p, "stagger_ms", 80) / 1000;
  const clear = () => items.forEach((i) => { i.style.opacity = ""; i.style.transform = ""; });
  items.forEach((i) => { i.style.opacity = "0"; i.style.transform = `translateY(${d}px)`; });
  let anim: ReturnType<typeof animate> | undefined;
  const stop = inView(el, () => {
    anim = animate(items, { opacity: [0, 1], transform: [`translateY(${d}px)`, "translateY(0px)"] },
      { duration: dur, delay: stagger(step), ease: EASE });
    anim.then(() => afterCommit(clear));  // hand hover transforms back to the components
  }, { amount: 0.15 });
  const unsettle = onSettle(() => { stop(); anim?.complete(); afterCommit(clear); });
  return () => { stop(); unsettle(); anim?.cancel(); clear(); };
};

/** Wrap each word of the section's headline in a mask. Only text nodes are split; inline
 * elements (a highlighted phrase) move as one unit, and their own nodes are kept. */
function splitWords(h: HTMLElement): HTMLElement[] {
  if (h.dataset.uibSplit) return [...h.querySelectorAll<HTMLElement>(".uib-word-inner")];
  h.dataset.uibSplit = "1";
  const inners: HTMLElement[] = [];
  const wrap = (content: Node) => {
    const outer = document.createElement("span"); outer.className = "uib-word";
    const inner = document.createElement("span"); inner.className = "uib-word-inner";
    outer.appendChild(inner); inner.appendChild(content); inners.push(inner);
    return outer;
  };
  for (const child of [...h.childNodes]) {
    if (child.nodeType === Node.TEXT_NODE) {
      const parts = (child.nodeValue ?? "").split(/(\s+)/);
      const frag = document.createDocumentFragment();
      for (const part of parts) {
        if (!part) continue;
        frag.appendChild(/^\s+$/.test(part) ? document.createTextNode(part) : wrap(document.createTextNode(part)));
      }
      h.replaceChild(frag, child);
    } else if (child instanceof HTMLElement && child.tagName !== "BR") {
      // Move, never clone: a clone would lose React's bindings (a link inside a headline would
      // stop responding), while the moved original keeps working inside its mask.
      const outer = wrap(document.createTextNode(""));
      h.insertBefore(outer, child);
      outer.firstElementChild!.replaceChildren(child);
    }
  }
  return inners;
}

const headlineReveal: Run = (el, p) => {
  const h = el.querySelector<HTMLElement>("h1, h2");
  if (!h || !h.textContent?.trim()) return () => {};
  const words = splitWords(h);
  const d = num(p, "distance", 110), dur = num(p, "duration_ms", 900) / 1000, step = num(p, "stagger_ms", 50) / 1000;
  const rest = () => { words.forEach((w) => { w.style.transform = ""; }); h.classList.add("uib-revealed"); };
  words.forEach((w) => { w.style.transform = `translateY(${d}%)`; });
  let anim: ReturnType<typeof animate> | undefined;
  const stop = inView(h, () => {
    anim = animate(words, { transform: [`translateY(${d}%)`, "translateY(0%)"] }, { duration: dur, delay: stagger(step), ease: EASE });
    anim.then(() => afterCommit(rest));
  }, { amount: 0.3 });
  const unsettle = onSettle(() => { stop(); anim?.complete(); afterCommit(rest); });
  return () => { stop(); unsettle(); anim?.cancel(); };
};

const NUMBER = /^([^\d-]{0,3})(-?\d{1,3}(?:[,.]\d{3})+|-?\d+(?:[.,]\d+)?)(\s?[^\d\s]{0,4})$/;
const numberTicker: Run = (el, p) => {
  const marked = [...el.querySelectorAll<HTMLElement>("[data-motion-number]")];
  const candidates = marked.length ? marked : [...el.querySelectorAll<HTMLElement>("p, dd, dt, span, strong, div")]
    .filter((e) => e.childElementCount === 0 && NUMBER.test(e.textContent?.trim() ?? "") && parseFloat(getComputedStyle(e).fontSize) >= 22);
  const targets = candidates.slice(0, 8).map((e) => {
    const text = e.textContent!.trim(); const [, pre, raw, post] = text.match(NUMBER)!;
    const thousands = /^-?\d{1,3}([,.]\d{3})+$/.test(raw) ? raw.match(/[,.]/)![0] : "";
    const value = parseFloat(thousands ? raw.split(thousands).join("") : raw.replace(",", "."));
    const decimals = !thousands && /[.,]\d+$/.test(raw) ? raw.split(/[.,]/)[1].length : 0;
    const node = e.firstChild as Text | null;
    const fmt = (v: number) => {
      const fixed = v.toFixed(decimals);
      const [int, frac] = fixed.split(".");
      const grouped = thousands ? int.replace(/\B(?=(\d{3})+(?!\d))/g, thousands) : int;
      return `${pre}${grouped}${frac ? (raw.includes(",") && !thousands ? "," : ".") + frac : ""}${post}`;
    };
    // Reserve the final width so counting never shifts the layout.
    e.style.fontVariantNumeric = "tabular-nums";
    if (getComputedStyle(e).display !== "inline") e.style.minWidth = `${e.getBoundingClientRect().width}px`;
    return { node, value, fmt, final: text };
  }).filter((t) => t.node && t.node.nodeType === Node.TEXT_NODE && Number.isFinite(t.value));
  if (!targets.length) return () => {};
  const set = (t: (typeof targets)[number], v: number) => { t.node!.nodeValue = t.fmt(v); };
  const rest = () => targets.forEach((t) => { t.node!.nodeValue = t.final; });
  targets.forEach((t) => set(t, 0));
  const anims: ReturnType<typeof animate>[] = [];
  const stop = inView(el, () => {
    for (const t of targets) anims.push(animate(0, t.value, { duration: num(p, "duration_ms", 1200) / 1000, ease: EASE, onUpdate: (v) => set(t, v), onComplete: () => { t.node!.nodeValue = t.final; } }));
  }, { amount: 0.3 });
  const unsettle = onSettle(() => { stop(); anims.forEach((a) => a.stop()); rest(); });
  return () => { stop(); unsettle(); anims.forEach((a) => a.stop()); rest(); };
};

/** Scroll-linked effect on the section's largest image layers. */
function scrollLinked(el: HTMLElement, count: number, build: (layer: HTMLElement, root: HTMLElement) => Cleanup): Cleanup {
  const roots = largest([...el.querySelectorAll("[data-motion-media]")]).slice(0, count) as HTMLElement[];
  const cleanups = roots.map((root) => {
    const layer = root.querySelector<HTMLElement>("[data-motion-layer]");
    return layer ? build(layer, root) : () => {};
  });
  return () => cleanups.forEach((c) => c());
}

const scrollZoom: Run = (el, p) => scrollLinked(el, 2, (layer, root) => {
  const from = num(p, "scale_from", 1.12);
  const cancel = scroll(animate(layer, { scale: [from, 1] }, { ease: "linear" }), { target: root, offset: ["start end", "center center"] });
  const rest = () => { cancel(); layer.style.transform = ""; };
  const unsettle = onSettle(rest);
  return () => { unsettle(); rest(); };
});

const parallax: Run = (el, p) => scrollLinked(el, 2, (layer, root) => {
  const a = Math.min(num(p, "amplitude", 0.12) * 60, 12);  // percent of the image's own height
  const cancel = scroll(animate(layer, { transform: [`translateY(-${a}%) scale(1.2)`, `translateY(${a}%) scale(1.2)`] }, { ease: "linear" }),
    { target: root, offset: ["start end", "end start"] });
  const rest = () => { cancel(); layer.style.transform = ""; };
  const unsettle = onSettle(rest);
  return () => { unsettle(); rest(); };
});

const scrollFade: Run = (el, p) => {
  const content = el.firstElementChild as HTMLElement | null;
  if (!content) return () => {};
  const d = num(p, "distance", 40), from = num(p, "opacity_from", 0.35);
  const cancel = scroll(animate(content, { opacity: [from, 1], transform: [`translateY(${d}px)`, "translateY(0px)"] }, { ease: "linear" }),
    { target: el, offset: ["start end", "start 0.6"] });
  const rest = () => { cancel(); content.style.opacity = ""; content.style.transform = ""; };
  const unsettle = onSettle(rest);
  return () => { unsettle(); rest(); };
};

/** The section pins while the next one slides over it, receding slightly as it is covered. */
const stack: Run = (el, p) => {
  const next = el.nextElementSibling as HTMLElement | null;
  const content = el.firstElementChild as HTMLElement | null;
  if (!next || !content) return () => {};
  Object.assign(el.style, { position: "sticky", top: "0px", zIndex: "0" });
  Object.assign(next.style, { position: "relative", zIndex: "1" });
  const to = num(p, "scale_from", 0.94);
  const cancel = scroll(animate(content, { scale: [1, to], opacity: [1, 0.55] }, { ease: "linear" }), { target: next, offset: ["start end", "start start"] });
  const rest = () => { cancel(); content.style.transform = ""; content.style.opacity = ""; };
  const unsettle = onSettle(rest);
  return () => { unsettle(); rest(); el.style.position = el.style.top = el.style.zIndex = ""; next.style.position = next.style.zIndex = ""; };
};

const finePointer = () => matchMedia("(hover: hover) and (pointer: fine)").matches;

const lift: Run = (el, p) => {
  const cards = [...el.querySelectorAll<HTMLElement>("[data-motion-card]")];
  const targets = cards.length ? cards : findItems(el);
  targets.forEach((c) => { c.classList.add("uib-lift"); c.style.setProperty("--uib-lift", `${num(p, "distance", 6)}px`); });
  return () => targets.forEach((c) => c.classList.remove("uib-lift"));
};

const tilt: Run = (el, p) => {
  const [target] = largest([...el.querySelectorAll("[data-motion-media]")]) as HTMLElement[];
  if (!target || !finePointer()) return () => {};
  const deg = num(p, "amplitude", 6);
  const move = (e: PointerEvent) => {
    const r = target.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
    target.style.transition = "transform 120ms ease-out";
    target.style.transform = `perspective(900px) rotateX(${(-y * deg * 2).toFixed(2)}deg) rotateY(${(x * deg * 2).toFixed(2)}deg)`;
  };
  const leave = () => { target.style.transition = "transform 500ms cubic-bezier(0.22,1,0.36,1)"; target.style.transform = ""; };
  target.addEventListener("pointermove", move); target.addEventListener("pointerleave", leave);
  const unsettle = onSettle(leave);
  return () => { target.removeEventListener("pointermove", move); target.removeEventListener("pointerleave", leave); unsettle(); leave(); };
};

const magnetic: Run = (el, p) => {
  const ctas = [...el.querySelectorAll<HTMLElement>("[data-motion-cta]")].filter(visible).slice(0, 2);
  if (!ctas.length || !finePointer()) return () => {};
  const strength = num(p, "amplitude", 8);
  const move = (e: PointerEvent) => {
    for (const b of ctas) {
      const r = b.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + r.height / 2;
      const dx = e.clientX - cx, dy = e.clientY - cy, dist = Math.hypot(dx, dy);
      const pull = dist < 140 ? 1 - dist / 140 : 0;
      b.style.transition = pull ? "transform 90ms linear" : "transform 450ms cubic-bezier(0.22,1,0.36,1)";
      b.style.transform = pull ? `translate(${(dx / 140) * strength * pull * 2}px, ${(dy / 140) * strength * pull * 2}px)` : "";
    }
  };
  const reset = () => ctas.forEach((b) => { b.style.transform = ""; });
  el.addEventListener("pointermove", move); el.addEventListener("pointerleave", reset);
  return () => { el.removeEventListener("pointermove", move); el.removeEventListener("pointerleave", reset); reset(); };
};

/** A layer inside the section, above its background and below its content. */
function ambientLayer(el: HTMLElement, background: string): HTMLElement | null {
  const section = el.querySelector<HTMLElement>("section") ?? el;
  if (getComputedStyle(section).position === "static") section.style.position = "relative";
  section.style.isolation = "isolate"; section.style.overflow = "hidden";
  const layer = document.createElement("div");
  layer.className = "uib-drift"; layer.setAttribute("aria-hidden", "true"); layer.style.background = background;
  section.prepend(layer);
  return layer;
}

const gradientDrift: Run = (el, p) => {
  const a = num(p, "amplitude", 0.25);
  const layer = ambientLayer(el, `radial-gradient(40% 50% at 25% 30%, color-mix(in srgb, var(--color-accent) ${Math.round(a * 100)}%, transparent), transparent 70%), radial-gradient(35% 45% at 75% 70%, color-mix(in srgb, var(--color-media-a) ${Math.round(a * 120)}%, transparent), transparent 70%)`);
  if (!layer) return () => {};
  const done = continuous();
  const anim = animate(layer, { transform: ["translate(-4%, -3%) rotate(0deg)", "translate(4%, 3%) rotate(8deg)"] },
    { duration: num(p, "duration_ms", 12000) / 1000, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" });
  const rest = () => { anim.cancel(); layer.style.transform = ""; };
  const unsettle = onSettle(rest);
  return () => { unsettle(); rest(); done(); layer.remove(); };
};

const float: Run = (el, p) => {
  const [target] = largest([...el.querySelectorAll("[data-motion-media]")]) as HTMLElement[];
  if (!target) return () => {};
  const a = num(p, "amplitude", 8);
  const done = continuous();
  const anim = animate(target, { y: [-a, a] }, { duration: num(p, "duration_ms", 3500) / 1000, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" });
  const rest = () => { anim.cancel(); target.style.transform = ""; };
  const unsettle = onSettle(rest);
  return () => { unsettle(); rest(); done(); };
};

const glow: Run = (el, p) => {
  const layer = ambientLayer(el, "radial-gradient(30% 40% at 50% 50%, color-mix(in srgb, var(--color-accent) 45%, transparent), transparent 70%)");
  if (!layer) return () => {};
  const a = num(p, "amplitude", 0.4);
  const done = continuous();
  const anim = animate(layer, { opacity: [1 - a, 1] }, { duration: num(p, "duration_ms", 2500) / 1000, repeat: Infinity, repeatType: "reverse", ease: "easeInOut" });
  const rest = () => { anim.cancel(); layer.style.opacity = ""; };
  const unsettle = onSettle(rest);
  return () => { unsettle(); rest(); done(); layer.remove(); };
};

/* Component-level behaviours: the component (Marquee primitive, layout transitions) already runs them. */
const handledByComponent: Run = () => () => {};

export const BEHAVIORS: Record<string, Run> = {
  stagger: stagger_, headline_reveal: headlineReveal, number_ticker: numberTicker,
  scroll_zoom: scrollZoom, parallax, scroll_fade: scrollFade, stack,
  lift, tilt, magnetic, gradient_drift: gradientDrift, float, glow,
  marquee: handledByComponent, morph: handledByComponent,
};

/** Attach a section's behaviours; returns one cleanup for all of them. */
export function attachMotion(el: HTMLElement, behaviors: Behavior[], reduced: boolean): Cleanup {
  if (reduced || !behaviors.length) return () => {};
  const cleanups = behaviors.map((b) => {
    const run = BEHAVIORS[b.name];
    if (!run) { console.warn(`[uib motion] unknown behaviour ${b.name}`); return () => {}; }
    try { return run(el, b.params); } catch (e) { console.warn(`[uib motion] ${b.name} failed`, e); return () => {}; }
  });
  return () => cleanups.forEach((c) => c());
}
