/**
 * A small History API router. Routes come from the site map (`/`, `/shop`, `/products/:id`);
 * a screen id is the identity, the route a property, so matching returns the screen id and
 * the parameters the route captured.
 */
import { useEffect, useState } from "react";
import type { SiteScreen } from "./types";

export interface Match { screen: string; params: Record<string, string> }

const NAVIGATE = "uib:navigate";

export function matchRoute(screens: SiteScreen[], path: string): Match | null {
  const parts = path.replace(/\/+$/, "").split("/").filter(Boolean);
  // Static routes win over parameterised ones of the same length.
  const ranked = [...screens].sort((a, b) => Number(a.route.includes(":")) - Number(b.route.includes(":")));
  for (const s of ranked) {
    const segs = s.route.split("/").filter(Boolean);
    if (segs.length !== parts.length) continue;
    const params: Record<string, string> = {};
    let ok = true;
    for (let i = 0; i < segs.length; i++) {
      if (segs[i].startsWith(":")) params[segs[i].slice(1)] = decodeURIComponent(parts[i]);
      else if (segs[i] !== parts[i]) { ok = false; break; }
    }
    if (ok) return { screen: s.id, params };
  }
  return null;
}

export const fillRoute = (route: string, params: Record<string, string>) =>
  route.split("/").map((seg) => (seg.startsWith(":") ? encodeURIComponent(params[seg.slice(1)] ?? "") : seg)).join("/") || "/";

export function navigate(href: string, replace = false) {
  if (href === window.location.pathname) return;
  if (replace) window.history.replaceState(null, "", href); else window.history.pushState(null, "", href);
  window.scrollTo(0, 0);
  window.dispatchEvent(new Event(NAVIGATE));
}

/** True for a same-origin path link a click handler should route instead of reloading. */
export function isInternal(a: HTMLAnchorElement): boolean {
  const href = a.getAttribute("href") ?? "";
  return href.startsWith("/") && !href.startsWith("//") && (!a.target || a.target === "_self") && !a.hasAttribute("download");
}

export function usePath(): string {
  const [path, setPath] = useState(window.location.pathname);
  useEffect(() => {
    const on = () => setPath(window.location.pathname);
    window.addEventListener("popstate", on);
    window.addEventListener(NAVIGATE, on);
    return () => { window.removeEventListener("popstate", on); window.removeEventListener(NAVIGATE, on); };
  }, []);
  return path;
}
