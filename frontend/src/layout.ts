import type { Breakpoint, ResolvedLayout } from "./types";
const ORDER: Breakpoint[] = ["mobile", "tablet", "desktop", "wide"];
const MIN: Record<Breakpoint, number> = { mobile: 0, tablet: 640, desktop: 1024, wide: 1440 };

export function currentBreakpoint(width: number): Breakpoint {
  let bp: Breakpoint = "mobile";
  for (const b of ORDER) if (width >= MIN[b]) bp = b;
  return bp;
}

/** Merge base props with every responsive override up to and including the current breakpoint (mobile-first). */
export function layoutStyle(layout: ResolvedLayout | null, bp: Breakpoint): { style: React.CSSProperties; hideSecondary: boolean } {
  if (!layout) return { style: {}, hideSecondary: false };
  const merged: Record<string, any> = { ...layout.props };
  for (const b of ORDER) {
    if (ORDER.indexOf(b) > ORDER.indexOf(bp)) break;
    Object.assign(merged, layout.responsive[b] ?? {});
  }
  const { columns, ratio, secondaryHidden, ...css } = merged;
  const style: React.CSSProperties = { ...css };
  if (style.display === "grid" && !style.gridTemplateColumns && columns) style.gridTemplateColumns = `repeat(${columns}, minmax(0,1fr))`;
  if (layout.type !== "full_bleed" && layout.type !== "sidebar" && layout.type !== "stack") { style.marginInline = "auto"; style.width = "100%"; }
  return { style, hideSecondary: !!secondaryHidden };
}
