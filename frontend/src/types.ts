export type Breakpoint = "mobile" | "tablet" | "desktop" | "wide";
export interface ResolvedLayout { type: string; props: Record<string, any>; responsive: Partial<Record<Breakpoint, Record<string, any>>>; }
export interface ResolvedAnimation { name: string; engine: string; config: Record<string, any>; reduced_motion_config: Record<string, any>; }
export interface RenderNode { id: string; semantic_type: string; implementation: string; props: Record<string, any>; tokens: Record<string, string>; layout: ResolvedLayout | null; animation: ResolvedAnimation | null; children: RenderNode[]; }
export interface RenderModel { screen_id: string; theme: string; css_variables: Record<string, string>; root: RenderNode; reduced_motion: boolean; }
