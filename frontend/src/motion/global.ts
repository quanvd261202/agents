/**
 * Page-wide micro-interactions, installed once: a product "flies" to the cart when added, the
 * cart bumps and its count goes up, and toggles (favourites, filters) pop when pressed. They
 * work for any component: add buttons are recognised by their label or a data-cart-add marker.
 */
import { animate } from "motion";

const ADD = /\b(add to (cart|bag|basket)|quick add|add)\b/i;
const EASE: [number, number, number, number] = [0.22, 1, 0.36, 1];

function isAddButton(b: HTMLButtonElement): boolean {
  if (b.dataset.cartAdd !== undefined) return true;
  const label = `${b.getAttribute("aria-label") ?? ""} ${b.textContent ?? ""}`.trim();
  return ADD.test(label) && !/remove|save|favourite/i.test(label);
}

function bumpCount(target: Element) {
  const count = target.querySelector("[data-cart-count]");
  const text = count?.firstChild;
  if (text && text.nodeType === Node.TEXT_NODE) {
    const n = parseInt(text.nodeValue ?? "0", 10);
    if (Number.isFinite(n)) text.nodeValue = String(n + 1);
  }
}

function flyToCart(from: HTMLElement, target: HTMLElement, reduced: boolean) {
  if (reduced) { bumpCount(target); return; }
  const a = from.getBoundingClientRect(), b = target.getBoundingClientRect();
  const x0 = a.left + a.width / 2, y0 = a.top + a.height / 2, x1 = b.left + b.width / 2, y1 = b.top + b.height / 2;
  const dot = document.createElement("span");
  dot.setAttribute("aria-hidden", "true");
  Object.assign(dot.style, {
    position: "fixed", left: "0px", top: "0px", width: "14px", height: "14px", marginLeft: "-7px", marginTop: "-7px",
    borderRadius: "9999px", background: "var(--color-accent)", boxShadow: "var(--shadow-md)", zIndex: "9999", pointerEvents: "none",
  });
  document.body.appendChild(dot);
  const peak = Math.min(y0, y1) - 80;  // an arc, not a straight line
  animate(dot, {
    transform: [`translate(${x0}px, ${y0}px) scale(1)`, `translate(${(x0 + x1) / 2}px, ${peak}px) scale(1.25)`, `translate(${x1}px, ${y1}px) scale(0.45)`],
    opacity: [1, 1, 0.7],
  }, { duration: 0.7, ease: EASE }).then(() => {
    dot.remove();
    bumpCount(target);
    animate(target, { scale: [1, 1.18, 1] }, { duration: 0.35, ease: EASE });
  });
}

export function installGlobalMotion(isReduced: () => boolean): () => void {
  const onClick = (e: MouseEvent) => {
    const button = (e.target as Element | null)?.closest("button");
    if (!button) return;
    const reduced = isReduced();
    if (button.hasAttribute("aria-pressed") && !reduced) {
      // after React has applied the new pressed state
      requestAnimationFrame(() => animate(button, { scale: [1, 1.16, 1] }, { duration: 0.32, ease: EASE }));
    }
    if (isAddButton(button)) {
      const target = document.querySelector<HTMLElement>("[data-cart-target]");
      if (target && !target.contains(button)) flyToCart(button, target, reduced);
    }
  };
  document.addEventListener("click", onClick);
  return () => document.removeEventListener("click", onClick);
}
