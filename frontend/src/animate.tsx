import { motion, useReducedMotion } from "motion/react";
import type { ResolvedAnimation } from "./types";
import type { PropsWithChildren, CSSProperties } from "react";

/** Applies a resolved Motion config. Falls back to reduced-motion config when the OS asks or the model says so. */
export function Animated({ animation, forceReduced, style, className, id, children, as = "div" }:
  PropsWithChildren<{ animation: ResolvedAnimation | null; forceReduced: boolean; style?: CSSProperties; className?: string; id?: string; as?: "div" | "section" }>) {
  const osReduced = useReducedMotion();
  const Tag = as === "section" ? motion.section : motion.div;
  const Plain = as;
  if (!animation) return <Plain id={id} style={style} className={className} data-node={id}>{children}</Plain>;
  const cfg = (osReduced || forceReduced) ? animation.reduced_motion_config : animation.config;
  if (cfg.disabled || cfg.static || Object.keys(cfg).length === 0)
    return <Plain id={id} style={style} className={className} data-node={id} data-anim={animation.name}>{children}</Plain>;
  const inView = cfg.trigger === "in_view";
  const transition = cfg.transition?.repeat === "Infinity" ? { ...cfg.transition, repeat: Infinity } : cfg.transition;
  return (
    <Tag id={id} className={className} style={style} data-node={id} data-anim={animation.name}
      initial={cfg.initial} animate={inView ? undefined : cfg.animate} whileInView={inView ? cfg.animate : undefined}
      viewport={inView ? { once: cfg.once ?? true, amount: 0.2 } : undefined} whileHover={cfg.whileHover}
      transition={cfg.stagger ? { ...transition, ...cfg.stagger } : transition}>
      {children}
    </Tag>
  );
}
