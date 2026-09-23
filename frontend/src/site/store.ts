/**
 * Runtime state: what the visitor does on the site. One small external store, read through
 * `useRuntime()`, persisted per viewer in localStorage so a reload keeps the cart. The renderer
 * seeds it for screenshots through `window.__uibState` or the `uib:state` event, so a cart page
 * is captured with lines in it without those lines living in any model.
 */
import { useSyncExternalStore } from "react";
import { EMPTY_STATE, type RuntimeState } from "./types";

declare global { interface Window { __uibState?: Partial<RuntimeState> } }

let state: RuntimeState = { ...EMPTY_STATE, ...(window.__uibState ?? {}) };
let storageKey: string | null = null;
const listeners = new Set<() => void>();

const emit = () => { listeners.forEach((l) => l()); };
const persist = () => {
  if (!storageKey) return;
  try { localStorage.setItem(storageKey, JSON.stringify(state)); } catch { /* private mode, quota: the session still works */ }
};

function set(next: Partial<RuntimeState>) {
  state = { ...state, ...next };
  persist();
  emit();
}

export const runtime = {
  get: () => state,
  subscribe(l: () => void) { listeners.add(l); return () => { listeners.delete(l); }; },
  /** Called once a site is known: loads the viewer's saved state unless a seed was given. */
  attach(key: string) {
    storageKey = `uib:state:${key}`;
    if (window.__uibState) return;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) { state = { ...EMPTY_STATE, ...(JSON.parse(raw) as Partial<RuntimeState>) }; emit(); }
    } catch { /* unreadable: start empty */ }
  },
  seed(next: Partial<RuntimeState>) { state = { ...EMPTY_STATE, ...next }; emit(); },
  reset() { set({ ...EMPTY_STATE }); },
  addToCart(item: string, qty = 1) {
    const line = state.cart.find((l) => l.item === item);
    set({ cart: line ? state.cart.map((l) => (l.item === item ? { ...l, qty: l.qty + qty } : l)) : [...state.cart, { item, qty }] });
  },
  setQty(item: string, qty: number) {
    set({ cart: qty <= 0 ? state.cart.filter((l) => l.item !== item) : state.cart.map((l) => (l.item === item ? { ...l, qty } : l)) });
  },
  remove(item: string) { set({ cart: state.cart.filter((l) => l.item !== item) }); },
  toggleFilter(tag: string) {
    set({ filters: state.filters.includes(tag) ? state.filters.filter((t) => t !== tag) : [...state.filters, tag] });
  },
  setFilters(filters: string[]) { set({ filters }); },
  setQuery(query: string) { set({ query }); },
};

export function useRuntime(): RuntimeState {
  return useSyncExternalStore(runtime.subscribe, runtime.get, runtime.get);
}

export const cartCount = (s: RuntimeState) => s.cart.reduce((n, l) => n + l.qty, 0);

window.addEventListener("uib:state", (e) => runtime.seed((e as CustomEvent<Partial<RuntimeState>>).detail ?? {}));
