/**
 * What a section may know about the site it is on: the site model, the current screen and its
 * route parameters. Without a site (a single-screen screenshot, the gallery) every hook returns
 * nothing and the components fall back to their props, exactly as before M13.
 */
import { createContext, useContext } from "react";
import type { RenderNode } from "../types";
import { fillRoute } from "./router";
import type { Collection, ContentItem, SiteModel } from "./types";

export interface SiteState {
  site: SiteModel | null;
  /** Current screen id, when a site is loaded and the path matched. */
  screen: string | null;
  params: Record<string, string>;
  path: string;
}

export const SiteContext = createContext<SiteState>({ site: null, screen: null, params: {}, path: "/" });
export const useSite = () => useContext(SiteContext);

/** The href the resolver wired for a role the component emits, or undefined (dead control). */
export const hrefOf = (node: RenderNode, role: string): string | undefined => {
  const links = node.props.hrefs as Record<string, string> | undefined;
  return links?.[role];
};

export function findItem(site: SiteModel | null, id: string | undefined): { collection: Collection; item: ContentItem } | null {
  if (!site?.content || !id) return null;
  for (const collection of site.content.collections) {
    const item = collection.items.find((i) => i.id === id);
    if (item) return { collection, item };
  }
  return null;
}

/** The item a bound section shows: the route's `:id` on a per-item screen, else its binding. */
export function useItem(node: RenderNode): ContentItem | null {
  const { site, params } = useSite();
  const binding = node.props.binding as { collection: string; item: string } | undefined;
  const fromRoute = findItem(site, params.id)?.item;
  return fromRoute ?? findItem(site, binding?.item)?.item ?? null;
}

/** The route's item on a per-item screen (the product the visitor opened), if any. */
export function useRouteItem(): ContentItem | null {
  const { site, params } = useSite();
  return findItem(site, params.id)?.item ?? null;
}

/** The first collection: what the listing, filters and search operate on. */
export function useCollection(): Collection | null {
  const { site } = useSite();
  return site?.content?.collections[0] ?? null;
}

/** href of an item's own page from the current screen, via its `open_item` link. */
export function useItemHref(): (itemId: string) => string | undefined {
  const { site, screen } = useSite();
  if (!site || !screen) return () => undefined;
  const current = site.site.screens.find((s) => s.id === screen);
  const target = current?.links.find((l) => l.intent === "open_item")?.to;
  const route = site.site.screens.find((s) => s.id === target)?.route;
  return (itemId) => (route ? fillRoute(route, { id: itemId }) : undefined);
}

/** Items of the collection that pass the active filters and query. */
export function filterItems(items: ContentItem[], filters: string[], query: string): ContentItem[] {
  const q = query.trim().toLowerCase();
  return items.filter((i) =>
    filters.every((f) => i.tags.includes(f)) &&
    (!q || [i.title, i.subtitle, ...i.tags].some((t) => t.toLowerCase().includes(q))));
}
