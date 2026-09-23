import type { CSSProperties, FC, ReactNode } from "react";
import type { RenderNode } from "../types";

/** What every semantic component receives from the tree walker in App.tsx. */
export interface NodeProps {
  node: RenderNode; children: ReactNode; hasChildren: boolean;
  /** Resolved by the layout engine for the current breakpoint. */
  columns?: number; tracks?: string; gap?: string;
  style?: CSSProperties; className?: string;
}
export type SectionMap = Record<string, FC<NodeProps>>;
