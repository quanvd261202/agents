import { Component, useEffect, useState, type ErrorInfo, type ReactNode } from "react";
import { COMPONENTS, CONTAINERS, type NodeProps } from "./components";
import { Animated } from "./animate";
import { attachMotion, settleAll } from "./motion/runtime";
import { installGlobalMotion } from "./motion/global";
import { currentBreakpoint, layoutStyle } from "./layout";
import type { Breakpoint, RenderModel, RenderNode } from "./types";

export interface RenderError { node: string; implementation: string; message: string; }
declare global { interface Window { __uibErrors: RenderError[]; __uibModel?: RenderModel; __uibReady?: boolean } }
window.__uibErrors ??= [];

class NodeBoundary extends Component<{ node: RenderNode; children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: Error, _info: ErrorInfo) {
    window.__uibErrors.push({ node: this.props.node.id, implementation: this.props.node.implementation, message: error.message });
  }
  render() {
    if (!this.state.failed) return this.props.children;
    // Structured, visible failure: never a silent fallback that hides the error from the verifier.
    return <div data-render-error={this.props.node.id} role="alert"
      style={{ padding: 16, border: "2px solid #dc2626", color: "#dc2626", background: "#fef2f2" }}>
      Failed to render “{this.props.node.semantic_type}” ({this.props.node.implementation})</div>;
  }
}

const prefersReduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Run the section's choreographed behaviours (node.motion) on its wrapper element. */
function useSectionMotion(node: RenderNode, reduced: boolean) {
  const behaviors = node.motion ?? [];
  const key = JSON.stringify(behaviors);
  useEffect(() => {
    if (!behaviors.length) return;
    const el = document.querySelector<HTMLElement>(`[data-node="${CSS.escape(node.id)}"]`);
    return el ? attachMotion(el, behaviors, reduced || prefersReduced()) : undefined;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [node.id, key, reduced]);
}

/** Components that stay on screen while the page scrolls, and which edge they hold. */
function stickyEdge(node: RenderNode): "top" | "bottom" | null {
  const variant = node.props.variant as string | undefined;
  if (node.implementation === "NavBar" && variant !== "transparent") return "top";
  if (node.implementation === "StickyCtaBar") return "bottom";
  return null;
}

function Node({ node, bp, reduced }: { node: RenderNode; bp: Breakpoint; reduced: boolean }) {
  useSectionMotion(node, reduced);
  const Impl = COMPONENTS[node.implementation];
  if (!Impl) {
    const err = { node: node.id, implementation: node.implementation, message: "no implementation registered" };
    if (!window.__uibErrors.some((e) => e.node === err.node)) window.__uibErrors.push(err);
    return <div data-render-error={node.id} role="alert" style={{ padding: 16, border: "2px solid #dc2626", color: "#dc2626" }}>
      Unknown implementation “{node.implementation}”</div>;
  }
  const { style, hideSecondary, columns } = layoutStyle(node.layout, bp);
  const children = node.children.map((c) => <Node key={c.id} node={c} bp={bp} reduced={reduced} />);
  const hasLayout = node.layout !== null;
  const tokenVars = Object.fromEntries(Object.entries(node.tokens).map(([k, v]) => [`--component-${k}`, v]));
  if (CONTAINERS.has(node.implementation)) {
    // The container element carries the layout itself, so its grid tracks apply to the child nodes.
    return <NodeBoundary node={node}>
      <Impl node={node} children={children} hasChildren={node.children.length > 0} columns={columns}
        className={hideSecondary ? "uib-hidden-secondary" : undefined}
        style={hasLayout ? { ...style, ...tokenVars } : undefined} />
    </NodeBoundary>;
  }
  const props: NodeProps = {
    node, children, hasChildren: node.children.length > 0, columns,
    tracks: typeof style.gridTemplateColumns === "string" ? style.gridTemplateColumns : undefined,
    gap: typeof style.gap === "string" ? style.gap : undefined,
  };
  const inner = <NodeBoundary node={node}><Impl {...props} /></NodeBoundary>;
  // Each section sits in its own wrapper, so a sticky component can only stick if the wrapper is
  // the sticky element: inside a box exactly its own height, position:sticky has nowhere to go.
  const sticky = stickyEdge(node);
  const wrapperStyle = sticky ? { ...tokenVars, position: "sticky" as const, [sticky]: 0, zIndex: 40 } : tokenVars;
  if (!node.animation) return <div data-node={node.id} data-semantic={node.semantic_type} style={wrapperStyle}>{inner}</div>;
  return (
    <Animated id={node.id} animation={node.animation} forceReduced={reduced} style={wrapperStyle}>{inner}</Animated>
  );
}

export default function App() {
  const [model, setModel] = useState<RenderModel | undefined>(window.__uibModel);
  const [version, setVersion] = useState(0);
  const [bp, setBp] = useState<Breakpoint>(currentBreakpoint(window.innerWidth));

  useEffect(() => {
    // `uib view` opens `/?model=<url>`; the renderer pushes models with the uib:model event instead.
    const src = new URLSearchParams(window.location.search).get("model");
    if (src) fetch(src).then((r) => r.json()).then((m: RenderModel) => { document.title = m.screen_id; setModel(m); });
  }, []);

  useEffect(() => {
    const onResize = () => setBp(currentBreakpoint(window.innerWidth));
    // A new model remounts the tree: the motion runtime rewrites headline DOM, which must not be
    // patched in place by React.
    const onModel = (e: Event) => { window.__uibErrors = []; setVersion((v) => v + 1); setModel((e as CustomEvent<RenderModel>).detail); };
    const uninstall = installGlobalMotion(() => !!window.__uibModel?.reduced_motion || prefersReduced());
    window.addEventListener("resize", onResize);
    window.addEventListener("uib:model", onModel as EventListener);
    window.addEventListener("uib:settle", settleAll);  // the renderer settles motion before capture
    return () => {
      uninstall();
      window.removeEventListener("resize", onResize);
      window.removeEventListener("uib:model", onModel as EventListener);
      window.removeEventListener("uib:settle", settleAll);
    };
  }, []);

  useEffect(() => {
    if (!model) return;
    const root = document.documentElement;
    for (const [k, v] of Object.entries(model.css_variables)) {
      const [name, scope] = k.split("@");
      if (!scope || scope === bp) root.style.setProperty(name, v);
    }
    root.dataset.theme = model.theme;
    window.__uibReady = false;
    const id = requestAnimationFrame(() => requestAnimationFrame(() => { window.__uibReady = true; }));
    return () => cancelAnimationFrame(id);
  }, [model, bp]);

  if (!model) return <div data-empty>Waiting for a render model…</div>;
  return <div key={version} data-screen={model.screen_id} data-breakpoint={bp}><Node node={model.root} bp={bp} reduced={model.reduced_motion} /></div>;
}
