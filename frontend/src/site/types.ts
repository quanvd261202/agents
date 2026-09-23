/**
 * The site as the frontend sees it (M13). `SiteModel` mirrors app/models/site.py: the site map,
 * the content model and one RenderModel per screen id. `RuntimeState` is separate on purpose:
 * cart, filters and search are what the visitor does, never part of a RenderModel.
 */
import type { RenderModel } from "../types";

export interface Link { intent: string; to: string }
export interface SiteScreen { id: string; route: string; nav_label: string | null; links: Link[] }
export interface NavItem { screen: string; label: string; href: string }
export interface SiteMap { entry: string; screens: SiteScreen[] }

export interface ContentItem {
  id: string; title: string; subtitle: string; price: string | null; badge: string | null; image: string;
  tags: string[]; attributes: Record<string, string>;
  /** A photograph found for this item on some screen, when there is one. */
  image_url?: string | null;
}
export interface Collection { id: string; item_label: string; items: ContentItem[] }
export interface ContentModel { brand: string; collections: Collection[] }

export interface SiteModel {
  site: SiteMap;
  content: ContentModel | null;
  /** RenderModels by screen id. */
  screens: Record<string, RenderModel>;
}

export interface CartLine { item: string; qty: number }
export interface RuntimeState {
  cart: CartLine[];
  /** Active tag filters on a listing. */
  filters: string[];
  /** Search query on a listing. */
  query: string;
}

export const EMPTY_STATE: RuntimeState = { cart: [], filters: [], query: "" };
