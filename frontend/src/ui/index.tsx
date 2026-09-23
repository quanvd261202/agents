/**
 * UI primitives. Every section is composed from these, so spacing, radius, colour, type and
 * interaction states stay one system. They read only design tokens (Tailwind utilities backed by
 * the runtime CSS variables), never hard-coded colours.
 */
import { forwardRef, useCallback, useEffect, useId, useState, type ButtonHTMLAttributes, type ReactNode } from "react";
import { motion } from "motion/react";
import { cva, type VariantProps } from "class-variance-authority";
import * as Accordion from "@radix-ui/react-accordion";
import * as RadixTabs from "@radix-ui/react-tabs";
import * as ToggleGroup from "@radix-ui/react-toggle-group";
import useEmblaCarousel from "embla-carousel-react";
import { ArrowLeft, ArrowRight, ChevronDown, Minus, Plus, Star } from "lucide-react";
import { cn } from "../lib/cn";
import type { RenderNode } from "../types";

/* ------------------------------------------------------------------ props helpers */
/** A string prop from the model, or the fallback. */
export const prop = (n: RenderNode, key: string, fallback: string): string => {
  const v = n.props[key];
  return typeof v === "string" && v.trim() ? v : fallback;
};
/** A comma-separated list prop ("Coffee,Tea,Cold drinks"), or the fallback list. */
export const listProp = (n: RenderNode, key: string, fallback: string[]): string[] => {
  const v = n.props[key];
  return typeof v === "string" && v.trim() ? v.split(",").map((s) => s.trim()).filter(Boolean) : fallback;
};
export const variantOf = (n: RenderNode, fallback = "standard"): string => (n.props.variant as string) || fallback;
export const range = (n: number) => Array.from({ length: n }, (_, i) => i);
/** The sourced photograph for position `i` of an image slot, or undefined so the silhouette renders. */
export const imageAt = (n: RenderNode, slot: string, i = 0): { url: string; alt: string } | undefined => {
  const refs = (n.props.images as Record<string, { url: string; alt: string }[]> | undefined)?.[slot];
  const ref = refs?.[i];
  return ref && ref.url ? { url: ref.url, alt: ref.alt ?? "" } : undefined;
};

/* ------------------------------------------------------------------ layout shells */
/** Tones re-scope the colour roles (see styles.css), so anything placed inside adapts. */
const sectionTone = {
  default: "tone-default",
  surface: "tone-surface",
  alt: "tone-alt",
  inverse: "tone-inverse",
  accent: "tone-accent",
} as const;
export type Tone = keyof typeof sectionTone;

/** One section of a page: tone, vertical rhythm and the content container. */
export function Section({ children, tone = "default", size = "md", wide, label, className, innerClassName }: {
  children: ReactNode; tone?: Tone; size?: "sm" | "md" | "lg" | "none"; wide?: boolean; label: string;
  className?: string; innerClassName?: string;
}) {
  const pad = { none: "", sm: "py-10 md:py-14", md: "section-y", lg: "py-24 md:py-36" }[size];
  return (
    <section aria-label={label} className={cn(sectionTone[tone], pad, "page-x", className)}>
      <div className={cn(wide ? "container-wide" : "container-page", innerClassName)}>{children}</div>
    </section>
  );
}

export function Eyebrow({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn("text-caption font-semibold uppercase tracking-[0.18em] text-muted", className)}>{children}</p>;
}

/** Eyebrow, heading and supporting line, aligned as a unit. */
export function SectionHeader({ eyebrow, title, body, align = "start", action, className, as: H = "h2" }: {
  eyebrow?: string; title: string; body?: string; align?: "start" | "center"; action?: ReactNode;
  className?: string; as?: "h1" | "h2" | "h3";
}) {
  return (
    <div className={cn("mb-10 flex flex-wrap items-end justify-between gap-6 md:mb-14",
      align === "center" && "flex-col items-center text-center", className)}>
      <div className={cn("max-w-2xl space-y-4", align === "center" && "mx-auto")}>
        {eyebrow && <Eyebrow>{eyebrow}</Eyebrow>}
        <H className="font-heading-set text-h2 text-balance">{title}</H>
        {body && <p className="text-lead text-muted text-pretty">{body}</p>}
      </div>
      {action}
    </div>
  );
}

/* ------------------------------------------------------------------ actions */
export const buttonVariants = cva(
  "group/btn relative inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-button font-semibold " +
    "transition-[transform,background-color,color,box-shadow,border-color] duration-200 ease-brand " +
    "active:scale-[0.97] disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-2",
  {
    variants: {
      variant: {
        primary: "bg-primary text-primary-fg shadow-sm hover:-translate-y-0.5 hover:shadow-md",
        accent: "bg-accent text-accent-fg shadow-sm hover:-translate-y-0.5 hover:shadow-md",
        secondary: "border border-border bg-transparent text-fg hover:border-fg/40 hover:bg-fg/[0.04]",
        inverse: "bg-primary-fg text-primary hover:-translate-y-0.5 hover:shadow-md",
        ghost: "bg-transparent text-fg hover:bg-fg/[0.06]",
        link: "h-auto px-0 text-fg underline-offset-[6px] hover:underline",
      },
      size: { sm: "h-10 px-4 text-small", md: "h-12 px-6 text-body", lg: "h-14 px-8 text-body", icon: "size-11" },
    },
    // A link sits on the text edge: no size may pad it. Kept 44px tall so it stays a real target.
    compoundVariants: [{ variant: "link", className: "h-11 px-0" }],
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export const Button = forwardRef<HTMLButtonElement,
  ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof buttonVariants> & { arrow?: boolean }>(
  ({ className, variant, size, arrow, children, ...rest }, ref) => (
    <button ref={ref} type="button" className={cn(buttonVariants({ variant, size }), className)}
      data-motion-cta={!variant || variant === "primary" || variant === "accent" || variant === "inverse" ? "" : undefined} {...rest}>
      {children}
      {arrow && <ArrowRight aria-hidden className="size-4 transition-transform duration-200 group-hover/btn:translate-x-0.5" />}
    </button>
  ));
Button.displayName = "Button";

export const badgeVariants = cva("inline-flex items-center gap-1 rounded-pill px-2.5 py-1 text-caption font-semibold tracking-wide", {
  variants: {
    tone: {
      neutral: "bg-surface-alt text-fg",
      accent: "bg-accent text-accent-fg",
      primary: "bg-primary text-primary-fg",
      outline: "border border-current/30 text-current",
      success: "bg-success text-bg",
    },
  },
  defaultVariants: { tone: "neutral" },
});
export function Badge({ children, tone, className }: { children: ReactNode; className?: string } & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ tone }), className)}>{children}</span>;
}

/* ------------------------------------------------------------------ surfaces */
export function Card({ children, className, interactive, as: Tag = "article" }: {
  children: ReactNode; className?: string; interactive?: boolean; as?: "article" | "div" | "li";
}) {
  return (
    <Tag data-motion-card="" className={cn("rounded-card border border-border bg-surface p-6 text-fg",
      interactive && "transition-[transform,box-shadow,border-color] duration-300 ease-brand hover:-translate-y-1 hover:border-fg/20 hover:shadow-lg",
      className)}>{children}</Tag>
  );
}

/* ------------------------------------------------------------------ media */
export type Subject = "cup" | "bag" | "leaf" | "glass" | "abstract" | "person" | "space" | "device" | "chart" | "product";
const SUBJECTS: Subject[] = ["cup", "bag", "leaf", "glass", "abstract", "person", "space", "device", "chart", "product"];
/** An image slot names what the photograph shows; the first known subject word picks the silhouette. */
export const subjectOf = (value: string, fallback: Subject): Subject =>
  (value.toLowerCase().split(/[^a-z]+/).find((w) => (SUBJECTS as string[]).includes(w)) as Subject | undefined) ?? fallback;

/** Low-contrast silhouettes: they suggest the subject without pretending to be a photo. */
const SILHOUETTES: Record<Subject, ReactNode> = {
  cup: <g><path d="M30 44h34v16a17 17 0 0 1-34 0z" /><path d="M64 48h4a7 7 0 0 1 0 14h-5" fill="none" strokeWidth="3.5" stroke="currentColor" /><ellipse cx="47" cy="79" rx="26" ry="4" /><path d="M40 36c-3-4 3-6 0-10M48 36c-3-4 3-6 0-10M56 36c-3-4 3-6 0-10" fill="none" strokeWidth="2.5" stroke="currentColor" strokeLinecap="round" /></g>,
  bag: <g><path d="M34 26h32l4 8v44a4 4 0 0 1-4 4H34a4 4 0 0 1-4-4V34z" /><rect x="38" y="46" width="24" height="18" rx="2" opacity="0.45" /><path d="M34 26l4 8h24l4-8" opacity="0.6" /></g>,
  leaf: <g><path d="M50 82C28 70 24 42 50 18c26 24 22 52 0 64z" /><path d="M50 82V30" fill="none" strokeWidth="2" stroke="currentColor" opacity="0.5" /></g>,
  glass: <g><path d="M34 28h32l-4 50a4 4 0 0 1-4 4H42a4 4 0 0 1-4-4z" /><rect x="42" y="44" width="8" height="8" rx="2" opacity="0.5" /><rect x="51" y="54" width="7" height="7" rx="2" opacity="0.5" /><path d="M58 28l6-12" fill="none" strokeWidth="3" stroke="currentColor" strokeLinecap="round" /></g>,
  abstract: <g><circle cx="38" cy="42" r="18" /><circle cx="62" cy="60" r="14" opacity="0.6" /><rect x="52" y="22" width="16" height="16" rx="4" opacity="0.4" /></g>,
  person: <g><circle cx="50" cy="38" r="13" /><path d="M24 84c2-16 13-24 26-24s24 8 26 24z" /></g>,
  space: <g><path d="M30 84V44a20 20 0 0 1 40 0v40z" opacity="0.8" /><rect x="18" y="84" width="64" height="3" /></g>,
  device: <g><rect x="18" y="28" width="64" height="40" rx="4" /><rect x="22" y="32" width="56" height="32" rx="2" opacity="0.35" /><path d="M12 72h76l-4 6H16z" /></g>,
  chart: <g><rect x="22" y="56" width="10" height="24" rx="2" /><rect x="38" y="44" width="10" height="36" rx="2" /><rect x="54" y="32" width="10" height="48" rx="2" /><rect x="70" y="22" width="10" height="58" rx="2" /></g>,
  product: <g><rect x="32" y="22" width="36" height="58" rx="8" /><rect x="38" y="40" width="24" height="16" rx="2" opacity="0.45" /></g>,
};

/**
 * Imagery. With `src` it is the photograph over the palette duotone (which shows while it loads);
 * without one it is the art-directed placeholder: duotone, soft light, film grain and a subject
 * silhouette. Callers pass `src={imageAt(node, slot, i)?.url}` and the subject as the fallback.
 */
export function Media({ ratio = "4/3", subject = "abstract", label, className, tone = 0, zoom = true, src, children }: {
  ratio?: string; subject?: Subject; label: string; className?: string; tone?: number; zoom?: boolean; src?: string; children?: ReactNode;
}) {
  const angle = [150, 200, 120, 240][tone % 4];
  const light = ["28% 22%", "72% 18%", "50% 30%", "20% 70%"][tone % 4];
  return (
    <div role="img" aria-label={label} style={{ aspectRatio: ratio }} data-motion-media=""
      className={cn("group/media relative isolate w-full overflow-hidden rounded-media bg-media-b", className)}>
      {/* Two layers: CSS owns the hover zoom on the outer one, the motion runtime owns scroll
          zoom and parallax on the inner one, so the two never fight over one transform. */}
      <div className={cn("absolute inset-0 transition-transform duration-700 ease-brand", zoom && "group-hover:scale-[1.04] group-hover/media:scale-[1.04]")}>
        <div data-motion-layer="" className="absolute inset-0 will-change-transform"
          style={{ background: `radial-gradient(120% 90% at ${light}, color-mix(in srgb, var(--color-media-a) 70%, white) 0%, transparent 55%), linear-gradient(${angle}deg, var(--color-media-a), var(--color-media-b))` }}>
          {src ? <img src={src} alt="" loading="eager" decoding="async" className="absolute inset-0 h-full w-full object-cover" /> : (
          <svg viewBox="0 0 100 100" aria-hidden className="absolute left-1/2 top-1/2 h-[62%] max-h-[420px] -translate-x-1/2 -translate-y-1/2"
            style={{ color: "color-mix(in srgb, var(--color-media-b) 78%, black)", fill: "currentColor", opacity: 0.42 }}>
            {SILHOUETTES[subject]}
          </svg>)}
        </div>
      </div>
      <div aria-hidden className="pointer-events-none absolute inset-0 opacity-[0.18] mix-blend-overlay"
        style={{ backgroundImage: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")" }} />
      {children}
    </div>
  );
}

/* ------------------------------------------------------------------ commerce bits */
export function Price({ value, compareAt, className }: { value: string; compareAt?: string; className?: string }) {
  return (
    <p className={cn("flex items-baseline gap-2 font-semibold tabular-nums", className)}>
      <span>{value}</span>
      {compareAt && <span className="text-small font-normal text-muted line-through">{compareAt}</span>}
    </p>
  );
}

export function Rating({ value = 4.8, count, className }: { value?: number; count?: number; className?: string }) {
  return (
    <div className={cn("flex items-center gap-1.5 text-small", className)} aria-label={`Rated ${value} out of 5${count ? ` from ${count} reviews` : ""}`}>
      <span className="flex" aria-hidden>{range(5).map((i) => (
        <Star key={i} className={cn("size-4", i < Math.round(value) ? "fill-current text-accent" : "text-border")} />))}</span>
      <span className="font-semibold">{value.toFixed(1)}</span>
      {count !== undefined && <span className="text-muted">({count})</span>}
    </div>
  );
}

export function QuantityStepper({ id, label = "Quantity", initial = 1 }: { id: string; label?: string; initial?: number }) {
  const [qty, setQty] = useState(initial);
  return (
    <div className="inline-flex h-12 items-center rounded-button border border-border" role="group" aria-labelledby={`${id}-label`}>
      <span id={`${id}-label`} className="sr-only">{label}</span>
      <button type="button" aria-label="Decrease quantity" onClick={() => setQty((q) => Math.max(1, q - 1))}
        className="grid size-11 place-items-center rounded-button text-fg transition-colors hover:bg-fg/[0.06]"><Minus className="size-4" /></button>
      <output aria-live="polite" className="w-8 overflow-hidden text-center font-semibold tabular-nums">
        <motion.span key={qty} className="inline-block" initial={{ y: "-60%", opacity: 0 }} animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}>{qty}</motion.span>
      </output>
      <button type="button" aria-label="Increase quantity" onClick={() => setQty((q) => q + 1)}
        className="grid size-11 place-items-center rounded-button text-fg transition-colors hover:bg-fg/[0.06]"><Plus className="size-4" /></button>
    </div>
  );
}

/** Single-choice chips (size, temperature, milk...): a Radix toggle group, keyboard accessible. */
export function ChoiceChips({ label, options, initial, className }: { label: string; options: string[]; initial?: string; className?: string }) {
  const [value, setValue] = useState(initial ?? options[0]);
  const groupId = useId();
  return (
    <fieldset className={cn("space-y-3", className)}>
      <legend className="text-small font-semibold">{label} <span className="font-normal text-muted">· {value}</span></legend>
      <ToggleGroup.Root type="single" value={value} onValueChange={(v) => v && setValue(v)} aria-label={label} className="flex flex-wrap gap-2">
        {options.map((o) => (
          <ToggleGroup.Item key={o} value={o}
            className="relative isolate h-11 min-w-11 rounded-button border border-border px-4 text-small font-medium transition-[color,border-color,transform,background-color] duration-200 ease-brand hover:border-fg/40 active:scale-[0.97] data-[state=on]:border-primary data-[state=on]:bg-primary data-[state=on]:text-primary-fg data-[state=on]:delay-150">
            {/* The selection is one shape that slides between options (a shared layout transition);
                the chip's own fill arrives just after it, so the settled state is a solid colour. */}
            {value === o && <motion.span layoutId={`chip-${groupId}`} aria-hidden className="absolute inset-0 -z-10 rounded-button bg-primary"
              transition={{ type: "spring", stiffness: 500, damping: 38 }} />}
            {o}
          </ToggleGroup.Item>))}
      </ToggleGroup.Root>
    </fieldset>
  );
}

/* ------------------------------------------------------------------ disclosure & navigation */
export function Disclosure({ items, className }: { items: { q: string; a: string }[]; className?: string }) {
  return (
    <Accordion.Root type="single" collapsible defaultValue="item-0" className={cn("divide-y divide-border border-y border-border", className)}>
      {items.map((it, i) => (
        <Accordion.Item key={it.q} value={`item-${i}`}>
          <Accordion.Header>
            <Accordion.Trigger className="group flex w-full items-center justify-between gap-6 py-5 text-left text-h4 font-heading-set">
              {it.q}
              <ChevronDown aria-hidden className="size-5 shrink-0 transition-transform duration-300 ease-brand group-data-[state=open]:rotate-180" />
            </Accordion.Trigger>
          </Accordion.Header>
          <Accordion.Content className="overflow-hidden pb-5 text-muted data-[state=closed]:hidden">{it.a}</Accordion.Content>
        </Accordion.Item>))}
    </Accordion.Root>
  );
}

export function Tabs({ tabs, label, className }: { tabs: { id: string; label: string; content: ReactNode }[]; label: string; className?: string }) {
  return (
    <RadixTabs.Root defaultValue={tabs[0]?.id} className={className}>
      <RadixTabs.List aria-label={label} className="mb-8 flex gap-1 overflow-x-auto border-b border-border">
        {tabs.map((t) => (
          <RadixTabs.Trigger key={t.id} value={t.id}
            className="relative -mb-px min-h-11 shrink-0 border-b-2 border-transparent px-4 text-small font-semibold text-muted transition-colors hover:text-fg data-[state=active]:border-fg data-[state=active]:text-fg">
            {t.label}
          </RadixTabs.Trigger>))}
      </RadixTabs.List>
      {tabs.map((t) => (
        <RadixTabs.Content key={t.id} value={t.id} className="motion-safe:animate-[uib-tab-in_380ms_var(--ease-brand)]">{t.content}</RadixTabs.Content>))}
    </RadixTabs.Root>
  );
}

/** Horizontally scrolling rail with arrow controls (Embla). Slides keep their own width classes. */
export function Carousel({ children, label, className }: { children: ReactNode[]; label: string; className?: string }) {
  const [ref, api] = useEmblaCarousel({ align: "start", containScroll: "trimSnaps" });
  const [edges, setEdges] = useState({ prev: false, next: true });
  const update = useCallback(() => api && setEdges({ prev: api.canScrollPrev(), next: api.canScrollNext() }), [api]);
  useEffect(() => { if (!api) return; update(); api.on("select", update).on("reInit", update); }, [api, update]);
  return (
    <div className={cn("relative", className)} role="region" aria-roledescription="carousel" aria-label={label}>
      <div className="overflow-hidden" ref={ref}>
        <div className="-ml-5 flex touch-pan-y">{children.map((c, i) => <div key={i} className="min-w-0 shrink-0 pl-5" aria-roledescription="slide">{c}</div>)}</div>
      </div>
      <div className="mt-8 flex justify-end gap-2">
        <Button variant="secondary" size="icon" aria-label="Previous" disabled={!edges.prev} onClick={() => api?.scrollPrev()}><ArrowLeft className="size-4" /></Button>
        <Button variant="secondary" size="icon" aria-label="Next" disabled={!edges.next} onClick={() => api?.scrollNext()}><ArrowRight className="size-4" /></Button>
      </div>
    </div>
  );
}

/** Infinite horizontal band. Motion stops entirely under prefers-reduced-motion. */
export function Marquee({ children, className, speed = 40 }: { children: ReactNode; className?: string; speed?: number }) {
  return (
    <div className={cn("group relative flex overflow-hidden [mask-image:linear-gradient(90deg,transparent,black_10%,black_90%,transparent)]", className)}>
      {[0, 1].map((k) => (
        <div key={k} aria-hidden={k === 1} className="flex shrink-0 items-center gap-12 pr-12 motion-safe:animate-[uib-marquee_var(--speed)_linear_infinite] group-hover:[animation-play-state:paused]"
          style={{ ["--speed" as string]: `${speed}s` }}>{children}</div>))}
    </div>
  );
}

export function Avatar({ name, className }: { name: string; className?: string }) {
  const initials = name.split(" ").map((w) => w[0]).slice(0, 2).join("");
  return <span aria-hidden className={cn("grid size-11 shrink-0 place-items-center rounded-pill bg-surface-alt text-small font-semibold text-fg", className)}>{initials}</span>;
}

/* ------------------------------------------------------------------ forms */
export function Field({ id, label, type = "text", placeholder, autoComplete, className }: {
  id: string; label: string; type?: string; placeholder?: string; autoComplete?: string; className?: string;
}) {
  return (
    <div className={cn("space-y-2", className)}>
      <label htmlFor={id} className="block text-small font-semibold">{label}</label>
      <input id={id} type={type} placeholder={placeholder ?? label} autoComplete={autoComplete}
        className="h-12 w-full rounded-button border border-border bg-bg px-4 text-body text-fg placeholder:text-muted/70 transition-[border-color,box-shadow] duration-200 focus:border-ring focus:outline-none focus:ring-4 focus:ring-ring/15" />
    </div>
  );
}
