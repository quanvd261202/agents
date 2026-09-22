import { Component, useEffect, useState, type ErrorInfo, type ReactNode } from "react";
import { COMPONENTS, type NodeProps } from "./components";
import { Animated } from "./animate";
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

function Node({ node, bp, reduced }: { node: RenderNode; bp: Breakpoint; reduced: boolean }) {
  const Impl = COMPONENTS[node.implementation];
  if (!Impl) {
    const err = { node: node.id, implementation: node.implementation, message: "no implementation registered" };
    if (!window.__uibErrors.some((e) => e.node === err.node)) window.__uibErrors.push(err);
    return <div data-render-error={node.id} role="alert" style={{ padding: 16, border: "2px solid #dc2626", color: "#dc2626" }}>
      Unknown implementation “{node.implementation}”</div>;
  }
  const { style, hideSecondary } = layoutStyle(node.layout, bp);
  const children = node.children.map((c) => <Node key={c.id} node={c} bp={bp} reduced={reduced} />);
  const props: NodeProps = { node, children, hasChildren: node.children.length > 0 };
  const inner = <NodeBoundary node={node}><Impl {...props} /></NodeBoundary>;
  const hasLayout = node.layout !== null;
  if (!hasLayout && !node.animation) return <div data-node={node.id} data-semantic={node.semantic_type}>{inner}</div>;
  return (
    <Animated id={node.id} animation={node.animation} forceReduced={reduced}
      className={hideSecondary ? "uib-hidden-secondary" : undefined}
      style={hasLayout ? { ...style, ...Object.fromEntries(Object.entries(node.tokens).map(([k, v]) => [`--component-${k}`, v])) } : undefined}>
      {inner}
    </Animated>
  );
}

export default function App() {
  const [model, setModel] = useState<RenderModel | undefined>(window.__uibModel);
  const [bp, setBp] = useState<Breakpoint>(currentBreakpoint(window.innerWidth));

  useEffect(() => {
    const onResize = () => setBp(currentBreakpoint(window.innerWidth));
    const onModel = (e: Event) => { window.__uibErrors = []; setModel((e as CustomEvent<RenderModel>).detail); };
    window.addEventListener("resize", onResize);
    window.addEventListener("uib:model", onModel as EventListener);
    return () => { window.removeEventListener("resize", onResize); window.removeEventListener("uib:model", onModel as EventListener); };
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
  return <div data-screen={model.screen_id} data-breakpoint={bp}><Node node={model.root} bp={bp} reduced={model.reduced_motion} /></div>;
}
