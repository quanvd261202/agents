/**
 * The component map the tree walker dispatches on: the two page containers plus every section
 * implementation, one file per catalog module in ../sections/.
 */
import type { FC } from "react";
import type { NodeProps } from "../sections/types";
import { SECTIONS as STRUCTURE } from "../sections/structure";
import { SECTIONS as MARKETING } from "../sections/marketing";
import { SECTIONS as COMMERCE } from "../sections/commerce";
import { SECTIONS as CONTENT } from "../sections/content";
import { SECTIONS as DATA } from "../sections/data";
import { SECTIONS as FORMS } from "../sections/forms";
import { SECTIONS as STORYTELLING } from "../sections/storytelling";

export type { NodeProps };

/** Pure containers: the resolved layout applies to their own element so grid tracks reach the children. */
export const CONTAINERS = new Set(["Page", "Main"]);

const Page: FC<NodeProps> = ({ children, style, className, node }) => (
  <div data-page data-node={node.id} style={style} className={className}>{children}</div>
);
const Main: FC<NodeProps> = ({ children, style, className, node }) => (
  <main data-node={node.id} style={style} className={className}>{children}</main>
);

export const COMPONENTS: Record<string, FC<NodeProps>> = {
  Page, Main, ...STRUCTURE, ...MARKETING, ...COMMERCE, ...CONTENT, ...DATA, ...FORMS, ...STORYTELLING,
};
