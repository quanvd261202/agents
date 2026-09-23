/**
 * Data sections. Keys are the catalog's implementation.root names. See sections/README.md.
 *
 * These live inside an app shell next to a sidebar, so they size themselves with container
 * queries (`@container` on the panel, `@3xl:` etc. on grids) rather than viewport breakpoints:
 * a stats row decides its columns from the width it actually has.
 */
import { useId, useLayoutEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent, type ReactNode } from "react";
import * as ToggleGroup from "@radix-ui/react-toggle-group";
import {
  AlertTriangle, Archive, ArrowDownRight, ArrowUpRight, Banknote, Bell, Check, CheckCircle2, ChevronLeft, ChevronRight,
  ChevronsUpDown, Download, FolderOpen, Info, MessageSquare, MoreHorizontal, Plus, Repeat, Search, ShoppingBag,
  SlidersHorizontal, Star, UserPlus, Users, Wallet, X, XCircle, type LucideIcon,
} from "lucide-react";
import { Avatar, Button, listProp, hrefOf, prop, range, variantOf } from "../ui";
import { cn } from "../lib/cn";
import type { RenderNode } from "../types";
import type { NodeProps, SectionMap } from "./types";

/* ================================================================== shared shells */

/** A dashboard band: tight vertical rhythm (panels stack in an app shell) and a query container. */
function Panel({ label, children, className }: { label: string; children: ReactNode; className?: string }) {
  return (
    <section aria-label={label} className={cn("page-x py-3 md:py-4", className)}>
      <div className="container-wide @container">{children}</div>
    </section>
  );
}

/** The card every panel sits on, with a title row (h2) and optional trailing action. */
function PanelCard({ title, subtitle, action, children, className, bodyClassName }: {
  title: string; subtitle?: string; action?: ReactNode; children: ReactNode; className?: string; bodyClassName?: string;
}) {
  return (
    <div className={cn("rounded-card border border-border bg-surface text-fg shadow-sm", className)}>
      <div className="flex flex-wrap items-start justify-between gap-x-6 gap-y-3 px-5 pt-5 md:px-6 md:pt-6">
        <div className="min-w-0 space-y-1">
          <h2 className="text-body font-semibold tracking-tight">{title}</h2>
          {subtitle && <p className="text-small text-muted">{subtitle}</p>}
        </div>
        {action}
      </div>
      <div className={cn("px-5 pb-5 pt-4 md:px-6 md:pb-6", bodyClassName)}>{children}</div>
    </div>
  );
}

/** Compact segmented control for time ranges and filters (Radix toggle group, keyboard accessible). */
function Segmented({ label, options, value, onChange }: {
  label: string; options: string[]; value: string; onChange: (v: string) => void;
}) {
  return (
    <ToggleGroup.Root type="single" value={value} onValueChange={(v) => v && onChange(v)} aria-label={label}
      className="inline-flex rounded-button border border-border bg-bg p-0.5">
      {options.map((o) => (
        <ToggleGroup.Item key={o} value={o}
          className="h-8 min-w-10 rounded-[calc(var(--radius-button)-2px)] px-3 text-caption font-semibold text-muted transition-[background-color,color] duration-200 ease-brand hover:text-fg data-[state=on]:bg-surface-alt data-[state=on]:text-fg">
          {o}
        </ToggleGroup.Item>))}
    </ToggleGroup.Root>
  );
}

/** Direction of a delta string: "+12.4%" up, "-0.4%" / "−3" down. */
const isDown = (d: string) => /^[-−–]/.test(d.trim());

/** Trend pill. `good` decides the colour (falling churn is good); the arrow always shows direction. */
function Trend({ delta, good, className }: { delta: string; good?: boolean; className?: string }) {
  const down = isDown(delta);
  const positive = good ?? !down;
  const Icon = down ? ArrowDownRight : ArrowUpRight;
  return (
    <span className={cn("inline-flex items-center gap-0.5 font-semibold tabular-nums", positive ? "text-success" : "text-danger", className)}>
      <Icon aria-hidden className="size-4" />{delta}
      <span className="sr-only">{positive ? "(improving)" : "(worsening)"}</span>
    </span>
  );
}

type StatusTone = "success" | "warning" | "danger" | "neutral" | "info";
const STATUS_CLASS: Record<StatusTone, string> = {
  success: "text-success border-success/25 bg-success/[0.08]",
  warning: "text-warning border-warning/30 bg-warning/[0.08]",
  danger: "text-danger border-danger/25 bg-danger/[0.07]",
  info: "text-fg border-border bg-bg",
  neutral: "text-muted border-border bg-fg/[0.03]",
};
const STATUS_DOT: Record<StatusTone, string> = {
  success: "bg-success", warning: "bg-warning", danger: "bg-danger", info: "bg-accent", neutral: "bg-muted",
};
const toneOfStatus = (s: string): StatusTone => {
  const k = s.toLowerCase();
  if (/(active|paid|complete|done|on track|live|delivered)/.test(k)) return "success";
  if (/(past due|failed|overdue|churn|cancel|blocked|off track)/.test(k)) return "danger";
  if (/(pending|at risk|low|review|due)/.test(k)) return "warning";
  if (/(trial|new|draft|invited)/.test(k)) return "info";
  return "neutral";
};

/** Status badge: colour plus a dot plus the word, so state never rests on colour alone. */
export function StatusBadge({ children, tone }: { children: string; tone?: StatusTone }) {
  const t = tone ?? toneOfStatus(children);
  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-pill border px-2 py-0.5 text-caption font-semibold", STATUS_CLASS[t])}>
      <span aria-hidden className={cn("size-1.5 rounded-pill", STATUS_DOT[t])} />{children}
    </span>
  );
}

/* ================================================================== charts */

/** Width of an element, tracked, so charts draw in real pixels (crisp text, true 2px lines). */
function useWidth<T extends HTMLElement>(initial = 0) {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(initial);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    setWidth(el.clientWidth);
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width] as const;
}

/** Evenly stepped y ticks on round numbers, choosing 3-5 intervals so the top tick hugs the data. */
const niceTicks = (max: number) => {
  let best: number[] = [];
  for (const count of [4, 5, 3]) {
    const raw = Math.max(max, 1) / count;
    const mag = 10 ** Math.floor(Math.log10(raw));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= raw) ?? raw;
    const ticks = range(count + 1).map((i) => i * step);
    if (!best.length || ticks[count] < best[best.length - 1]) best = ticks;
  }
  return best;
};

/** Short axis numbers: 12500 -> 12.5k. */
const compact = (v: number) =>
  Math.abs(v) >= 1e6 ? `${+(v / 1e6).toFixed(1)}M` : Math.abs(v) >= 1e3 ? `${+(v / 1e3).toFixed(1)}k` : `${+v.toFixed(1)}`;

/** Numbers from a comma list slot, or the fallback when the slot is absent or malformed. */
const numbers = (n: RenderNode, key: string, fallback: number[]) => {
  const v = listProp(n, key, []).map((s) => Number(s.replace(/[^0-9.-]/g, ""))).filter((x) => Number.isFinite(x));
  return v.length >= 2 ? v : fallback;
};

type SeriesTone = "accent" | "muted";
interface Series { name: string; values: number[]; tone: SeriesTone }
/** Series colours are roles, not hex: the brand accent for "now", a quiet ink for the comparison. */
const SERIES_COLOR: Record<SeriesTone, string> = {
  accent: "var(--color-accent)",
  muted: "color-mix(in srgb, var(--color-fg) 34%, var(--color-surface))",
};

function Legend({ series }: { series: Series[] }) {
  if (series.length < 2) return null;
  return (
    <ul className="flex flex-wrap items-center gap-x-5 gap-y-1 text-caption text-muted">
      {series.map((s) => (
        <li key={s.name} className="flex items-center gap-2">
          <svg aria-hidden width="16" height="4"><line x1="1" y1="2" x2="15" y2="2" stroke={SERIES_COLOR[s.tone]} strokeWidth="2.5"
            strokeLinecap="round" strokeDasharray={s.tone === "muted" ? "3 3" : undefined} /></svg>
          {s.name}
        </li>))}
    </ul>
  );
}

const barPath = (cx: number, w: number, top: number, base: number, r: number) => {
  const rr = Math.max(0, Math.min(r, w / 2, base - top));
  const l = cx - w / 2, rt = cx + w / 2;
  return `M${l},${base}V${top + rr}Q${l},${top} ${l + rr},${top}H${rt - rr}Q${rt},${top} ${rt},${top + rr}V${base}Z`;
};

/**
 * Line, area and bar charts on one set of axes: recessive gridlines, a firmer baseline, y ticks
 * on nice numbers, thinned x labels, a crosshair + tooltip on hover, and an optional goal line.
 */
function XYChart({ kind, labels, series, format = compact, height = 240, target, targetLabel = "Goal", label }: {
  kind: "line" | "area" | "bar"; labels: string[]; series: Series[]; format?: (v: number) => string;
  height?: number; target?: number; targetLabel?: string; label: string;
}) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = useState<number | null>(null);
  const gid = useId().replace(/:/g, "");
  const n = Math.min(labels.length, ...series.map((s) => s.values.length));
  const m = { l: 44, r: 8, t: 10, b: 28 };
  const pw = Math.max(width - m.l - m.r, 40), ph = height - m.t - m.b;
  const ticks = niceTicks(Math.max(...series.flatMap((s) => s.values.slice(0, n)), target ?? 0));
  const top = ticks[ticks.length - 1];
  const y = (v: number) => m.t + ph - (v / top) * ph;
  const band = pw / n;
  const x = (i: number) => (kind === "bar" ? m.l + band * (i + 0.5) : m.l + (n === 1 ? pw / 2 : (i / (n - 1)) * pw));
  const every = Math.max(1, Math.ceil((n * 46) / pw));
  const base = m.t + ph;

  const onMove = (e: ReactPointerEvent<SVGSVGElement>) => {
    const px = e.clientX - e.currentTarget.getBoundingClientRect().left - m.l;
    const i = kind === "bar" ? Math.floor(px / band) : Math.round((px / pw) * (n - 1));
    setHover(Math.max(0, Math.min(n - 1, i)));
  };
  const summary = `${label}. ${series.map((s) => `${s.name}: ${labels.slice(0, n).map((l, i) => `${l} ${format(s.values[i])}`).join(", ")}`).join(". ")}`;
  const barW = Math.min(band * (series.length > 1 ? 0.34 : 0.56), 36);

  return (
    <div ref={ref} className="relative w-full min-w-0 select-none" style={{ height }}>
      {width > 0 && <svg role="img" aria-label={summary} width={width} height={height} className="block overflow-visible"
        onPointerMove={onMove} onPointerLeave={() => setHover(null)}>
        <defs>
          <linearGradient id={`fill-${gid}`} x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.22" />
            <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0" />
          </linearGradient>
        </defs>
        {ticks.map((t, i) => (
          <g key={t}>
            <line x1={m.l} x2={m.l + pw} y1={y(t)} y2={y(t)} stroke={i === 0 ? "color-mix(in srgb, var(--color-fg) 22%, var(--color-surface))" : "var(--color-border)"}
              strokeDasharray={i === 0 ? undefined : "2 4"} />
            <text x={m.l - 10} y={y(t)} textAnchor="end" dominantBaseline="middle" fontSize="11" fill="var(--color-muted)" className="tabular-nums">{format(t)}</text>
          </g>))}
        {labels.slice(0, n).map((l, i) => (i % every === 0 || i === n - 1) && (i === n - 1 || n - 1 - i >= every) ? (
          <text key={l + i} x={x(i)} y={height - 8} textAnchor={kind !== "bar" && i === 0 ? "start" : kind !== "bar" && i === n - 1 ? "end" : "middle"}
            fontSize="11" fill={hover === i ? "var(--color-fg)" : "var(--color-muted)"}>{l}</text>) : null)}

        {kind === "bar" ? series.map((s, si) => s.values.slice(0, n).map((v, i) => {
          const offset = series.length > 1 ? (si - (series.length - 1) / 2) * (barW + 3) : 0;
          return <path key={`${si}-${i}`} d={barPath(x(i) + offset, barW, y(v), base, 4)} fill={SERIES_COLOR[s.tone]}
            className="transition-opacity duration-200" opacity={hover === null || hover === i ? 1 : 0.4} />;
        })) : series.map((s) => {
          const pts = s.values.slice(0, n).map((v, i) => `${x(i)},${y(v)}`);
          return (
            <g key={s.name}>
              {kind === "area" && s.tone === "accent" && <path d={`M${x(0)},${base}L${pts.join("L")}L${x(n - 1)},${base}Z`} fill={`url(#fill-${gid})`} />}
              <path d={`M${pts.join("L")}`} fill="none" stroke={SERIES_COLOR[s.tone]} strokeWidth={s.tone === "accent" ? 2 : 1.5}
                strokeLinejoin="round" strokeLinecap="round" strokeDasharray={s.tone === "muted" ? "4 4" : undefined} />
            </g>
          );
        })}
        {kind !== "bar" && hover === null && series[0] && (
          <circle cx={x(n - 1)} cy={y(series[0].values[n - 1])} r="4" fill={SERIES_COLOR[series[0].tone]} stroke="var(--color-surface)" strokeWidth="2" />)}

        {target !== undefined && (
          <g>
            <line x1={m.l} x2={m.l + pw} y1={y(target)} y2={y(target)} stroke="var(--color-fg)" strokeOpacity="0.55" strokeDasharray="6 4" />
            <rect x={m.l + 4} y={y(target) - 10} width={targetLabel.length * 6.5 + format(target).length * 6.5 + 20} height="20" rx="10"
              fill="var(--color-bg)" stroke="var(--color-border)" />
            <text x={m.l + 14} y={y(target)} dominantBaseline="middle" fontSize="11" fontWeight="600" fill="var(--color-fg)">{targetLabel} {format(target)}</text>
          </g>)}

        {hover !== null && (
          <g aria-hidden>
            {kind !== "bar" && <line x1={x(hover)} x2={x(hover)} y1={m.t} y2={base} stroke="var(--color-fg)" strokeOpacity="0.25" />}
            {kind !== "bar" && series.map((s) => (
              <circle key={s.name} cx={x(hover)} cy={y(s.values[hover])} r="4.5" fill={SERIES_COLOR[s.tone]} stroke="var(--color-surface)" strokeWidth="2" />))}
          </g>)}
        {/* Hit area larger than the marks. */}
        <rect x={m.l} y={m.t} width={pw} height={ph} fill="transparent" />
      </svg>}
      {hover !== null && (
        <div aria-hidden className="pointer-events-none absolute top-0 z-10 min-w-32 rounded-button border border-border bg-bg px-3 py-2 text-small shadow-md"
          style={{ left: Math.min(Math.max(x(hover), 70), width - 70), transform: "translateX(-50%)" }}>
          <p className="mb-1 text-caption font-semibold text-muted">{labels[hover]}</p>
          {series.map((s) => (
            <p key={s.name} className="flex items-center justify-between gap-4">
              <span className="flex items-center gap-2"><span className="size-2 rounded-pill" style={{ background: SERIES_COLOR[s.tone] }} />{s.name}</span>
              <span className="font-semibold tabular-nums">{format(s.values[hover])}</span>
            </p>))}
        </div>)}
    </div>
  );
}

/** Segment colours for part-to-whole: accent, primary, then two quieter steps. Legend carries identity. */
const DONUT_COLORS = [
  "var(--color-accent)",
  "var(--color-primary)",
  "color-mix(in srgb, var(--color-accent) 45%, var(--color-surface))",
  "color-mix(in srgb, var(--color-fg) 20%, var(--color-surface))",
];

function Donut({ labels, values, total, totalLabel, format, label }: {
  labels: string[]; values: number[]; total: string; totalLabel: string; format: (v: number) => string; label: string;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const sum = values.reduce((a, b) => a + b, 0) || 1;
  const r = 70, sw = 18, C = 2 * Math.PI * r, gap = 3;
  let acc = 0;
  const segs = values.map((v, i) => { const len = (v / sum) * C; const s = { i, len, off: acc }; acc += len; return s; });
  const pct = (v: number) => `${Math.round((v / sum) * 100)}%`;
  return (
    <div className="grid items-center gap-8 @xl:grid-cols-[auto_minmax(0,1fr)] @xl:gap-12">
      <div className="relative mx-auto size-48">
        <svg role="img" aria-label={`${label}: ${labels.map((l, i) => `${l} ${pct(values[i])}`).join(", ")}`} viewBox="0 0 180 180" className="size-full -rotate-90">
          <circle cx="90" cy="90" r={r} fill="none" stroke="var(--color-border)" strokeWidth={sw} opacity="0.5" />
          {segs.map((s) => (
            <circle key={s.i} cx="90" cy="90" r={r} fill="none" stroke={DONUT_COLORS[s.i % DONUT_COLORS.length]}
              strokeWidth={hover === s.i ? sw + 5 : sw} strokeDasharray={`${Math.max(s.len - gap, 0)} ${C}`} strokeDashoffset={-s.off}
              className="transition-[stroke-width,opacity] duration-200 ease-brand" opacity={hover === null || hover === s.i ? 1 : 0.45}
              onPointerEnter={() => setHover(s.i)} onPointerLeave={() => setHover(null)} />))}
        </svg>
        <div className="pointer-events-none absolute inset-0 grid place-content-center text-center">
          <p className="font-heading-set text-h4 tabular-nums">{hover === null ? total : format(values[hover])}</p>
          <p className="text-caption text-muted">{hover === null ? totalLabel : labels[hover]}</p>
        </div>
      </div>
      <ul className="divide-y divide-border">
        {labels.map((l, i) => (
          <li key={l} onPointerEnter={() => setHover(i)} onPointerLeave={() => setHover(null)}
            className={cn("grid grid-cols-[auto_minmax(0,1fr)_auto_auto] items-center gap-3 py-3 text-small transition-opacity duration-200",
              hover !== null && hover !== i && "opacity-60")}>
            <span aria-hidden className="size-2.5 rounded-sm" style={{ background: DONUT_COLORS[i % DONUT_COLORS.length] }} />
            <span className="truncate font-medium">{l}</span>
            <span className="tabular-nums text-muted">{format(values[i])}</span>
            <span className="w-12 text-right font-semibold tabular-nums">{pct(values[i])}</span>
          </li>))}
      </ul>
    </div>
  );
}

/** Tiny trend line for stat cards: no axes, the shape is the message. */
function Sparkline({ values, label, className }: { values: number[]; label: string; className?: string }) {
  const gid = useId().replace(/:/g, "");
  const w = 120, h = 40, min = Math.min(...values), max = Math.max(...values), span = max - min || 1;
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * w},${h - 3 - ((v - min) / span) * (h - 8)}`);
  return (
    <svg role="img" aria-label={label} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className={cn("h-10 w-28 overflow-visible", className)}>
      <defs><linearGradient id={`sp-${gid}`} x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.2" /><stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0" />
      </linearGradient></defs>
      <path d={`M0,${h}L${pts.join("L")}L${w},${h}Z`} fill={`url(#sp-${gid})`} />
      <path d={`M${pts.join("L")}`} fill="none" stroke="var(--color-accent)" strokeWidth="2" vectorEffect="non-scaling-stroke" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

/* ================================================================== stats */

const STATS: { label: string; value: string; delta: string; good?: boolean; icon: LucideIcon; spark: number[] }[] = [
  { label: "Revenue", value: "$48,210", delta: "+12.4%", icon: Wallet, spark: [22, 26, 24, 30, 29, 34, 33, 38, 41, 40, 46, 49] },
  { label: "Orders", value: "1,284", delta: "+8.1%", icon: ShoppingBag, spark: [40, 38, 44, 42, 47, 45, 50, 49, 53, 55, 54, 58] },
  { label: "Returning customers", value: "62.8%", delta: "+3.2%", icon: Repeat, spark: [51, 53, 52, 55, 54, 57, 56, 58, 60, 59, 61, 63] },
  { label: "Refund rate", value: "1.6%", delta: "-0.4%", good: true, icon: Users, spark: [2.4, 2.3, 2.3, 2.1, 2.2, 2, 1.9, 1.9, 1.8, 1.7, 1.7, 1.6] },
];

function Stats({ node, columns }: NodeProps) {
  const variant = variantOf(node);
  const labels = listProp(node, "labels", STATS.map((s) => s.label));
  const values = listProp(node, "values", STATS.map((s) => s.value));
  const deltas = listProp(node, "deltas", STATS.map((s) => s.delta));
  const period = prop(node, "period", "vs last month");
  const items = labels.map((label, i) => {
    const s = STATS[i % STATS.length];
    const delta = deltas[i] ?? s.delta;
    return { ...s, label, value: values[i] ?? s.value, delta, good: labels[i] === s.label ? s.good : undefined };
  });
  const cols = columns ?? Math.min(items.length, 4);
  const grid = "grid grid-cols-1 gap-3 @lg:grid-cols-2 @4xl:grid-cols-[repeat(var(--cols),minmax(0,1fr))] md:gap-4";
  const title = prop(node, "title", "Key metrics");

  if (variant === "compact") {
    // One strip, cells separated by hairlines: the densest read, for the top of a busy page.
    return (
      <Panel label={title}>
        <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-card border border-border bg-border shadow-sm @md:grid-cols-2 @4xl:grid-cols-[repeat(var(--cols),minmax(0,1fr))]"
          style={{ ["--cols" as string]: cols }}>
          {items.map((s) => (
            <div key={s.label} className="flex items-baseline justify-between gap-3 bg-surface px-5 py-4 @4xl:flex-col @4xl:items-start @4xl:gap-1">
              <dt className="text-small text-muted">{s.label}</dt>
              <dd className="flex items-baseline gap-2">
                <span className="font-heading-set text-h4 tabular-nums">{s.value}</span>
                <Trend delta={s.delta} good={s.good} className="text-caption" />
              </dd>
            </div>))}
        </dl>
      </Panel>
    );
  }
  if (variant === "with_trend") {
    return (
      <Panel label={title}>
        <ul className={grid} style={{ ["--cols" as string]: cols }}>
          {items.map((s) => (
            <li key={s.label} className="flex flex-col gap-4 rounded-card border border-border bg-surface p-5 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <p className="text-small font-medium text-muted">{s.label}</p>
                <Trend delta={s.delta} good={s.good} className="rounded-pill bg-fg/[0.04] px-2 py-0.5 text-caption" />
              </div>
              <div className="flex items-end justify-between gap-4">
                <p className="shrink-0 font-heading-set text-h3 tabular-nums leading-none">{s.value}</p>
                <Sparkline values={s.spark} label={`${s.label} over the last 12 months, trending ${isDown(s.delta) ? "down" : "up"}`} className="w-auto min-w-0 max-w-28 flex-1" />
              </div>
              <p className="text-caption text-muted">{period}</p>
            </li>))}
        </ul>
      </Panel>
    );
  }
  return (
    <Panel label={title}>
      <ul className={grid} style={{ ["--cols" as string]: cols }}>
        {items.map((s) => {
          const Icon = s.icon;
          return (
            <li key={s.label} className="rounded-card border border-border bg-surface p-5 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <p className="text-small font-medium text-muted">{s.label}</p>
                <span aria-hidden className="grid size-8 place-items-center rounded-button border border-border bg-bg text-muted"><Icon className="size-4" /></span>
              </div>
              <p className="mt-3 font-heading-set text-h3 tabular-nums">{s.value}</p>
              <p className="mt-2 flex flex-wrap items-center gap-x-2 text-small">
                <Trend delta={s.delta} good={s.good} /><span className="text-muted">{period}</span>
              </p>
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}

/* ================================================================== chart panel */

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const money = (v: number) => `$${compact(v)}`;

const CHART_SAMPLES = {
  line: { title: "Revenue", subtitle: "Monthly, compared with last year", value: "$128.4k", delta: "+12.4%", note: "vs last year",
    labels: MONTHS, series: ["This year", "Last year"], a: [7.2, 8.1, 7.8, 9.4, 10.2, 9.8, 11.6, 12.4, 11.9, 13.1, 12.8, 14.2].map((v) => v * 1000),
    b: [6.4, 6.9, 7.1, 7.6, 8.2, 8.4, 9.1, 9.4, 9.9, 10.2, 10.6, 11.4].map((v) => v * 1000), format: money },
  area: { title: "Visitors", subtitle: "Daily unique visitors, last 30 days", value: "48,210", delta: "+6.8%", note: "vs previous 30 days",
    labels: range(30).map((i) => `Sep ${i + 1}`), series: ["Visitors"],
    a: range(30).map((i) => Math.round(1250 + i * 14 + Math.sin(i / 1.6) * 180 + (i % 7 === 5 ? 260 : 0))), b: [], format: compact },
  bar: { title: "Orders", subtitle: "Completed orders per month", value: "1,284", delta: "+8.1%", note: "vs last month",
    labels: MONTHS, series: ["Orders"], a: [82, 91, 88, 104, 112, 108, 121, 118, 126, 132, 128, 140], b: [], format: compact },
  donut: { title: "Sales by channel", subtitle: "Share of revenue, this quarter", value: "$84.6k", delta: "+4.2%", note: "vs last quarter",
    labels: ["In store", "Online", "Wholesale", "Events"], series: [], a: [35500, 26200, 14400, 8500], b: [], format: money },
};

function ChartPanel({ node }: NodeProps) {
  const variant = (["line", "bar", "area", "donut"].includes(variantOf(node, "line")) ? variantOf(node, "line") : "line") as keyof typeof CHART_SAMPLES;
  const s = CHART_SAMPLES[variant];
  const ranges = listProp(node, "ranges", ["7D", "30D", "12M"]);
  const [range_, setRange] = useState(ranges[variant === "area" ? 1 : ranges.length - 1] ?? ranges[0]);
  const title = prop(node, "title", s.title);
  const labels = listProp(node, "labels", s.labels);
  const names = listProp(node, "series", s.series);
  const a = numbers(node, "values", s.a);
  const b = numbers(node, "compare_values", s.b);
  const delta = prop(node, "delta", s.delta);
  const series: Series[] = [{ name: names[0] ?? title, values: a, tone: "accent" }];
  if (variant === "line" && b.length) series.push({ name: names[1] ?? "Previous period", values: b, tone: "muted" });
  // Axis values read as money only when the panel is about money: a lessons-per-week chart must not say "$3".
  const headline = prop(node, "value", s.value);
  const format = /[$€£¥]/.test(headline) || /revenue|sales|income|spend|cost|price|mrr|arr|payout/i.test(title) ? money : compact;

  return (
    <Panel label={title}>
      <PanelCard title={title} subtitle={prop(node, "subtitle", s.subtitle)}
        action={variant === "donut" ? undefined : <Segmented label="Time range" options={ranges} value={range_} onChange={setRange} />}>
        {variant !== "donut" && (
          <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <p className="font-heading-set text-h2 tabular-nums leading-none">{prop(node, "value", s.value)}</p>
              <p className="text-small"><Trend delta={delta} /> <span className="text-muted">{prop(node, "note", s.note)}</span></p>
            </div>
            <Legend series={series} />
          </div>)}
        {variant === "donut"
          ? <Donut labels={labels} values={a} total={prop(node, "value", s.value)} totalLabel={prop(node, "note", "Total revenue")} format={format} label={title} />
          : <XYChart kind={variant} labels={labels} series={series} format={format} label={title} height={variant === "bar" ? 220 : 240} />}
      </PanelCard>
    </Panel>
  );
}

/* ================================================================== KPI hero */

function KpiHero({ node }: NodeProps) {
  const variant = variantOf(node);
  const label = prop(node, "label", "Net revenue");
  const value = prop(node, "value", "$312,480");
  const delta = prop(node, "delta", "+18.2%");
  const context = prop(node, "context", "vs $264,300 in the same period last year");
  const a = numbers(node, "values", [18.2, 19.4, 21.1, 20.6, 23.8, 24.9, 26.1, 25.4, 27.8, 28.6, 30.2, 31.9].map((v) => v * 1000));
  const b = numbers(node, "compare_values", [15.1, 16.2, 17.4, 17.9, 19.6, 20.3, 21.4, 21.8, 22.9, 23.6, 24.2, 25.7].map((v) => v * 1000));
  const labels = listProp(node, "labels", MONTHS);
  const [range_, setRange] = useState("12M");

  if (variant === "split") {
    const breakdown = [
      { label: listProp(node, "breakdown", ["Average order", "Orders", "Conversion"])[0] ?? "Average order", value: "$38.40", delta: "+4.1%" },
      { label: listProp(node, "breakdown", ["Average order", "Orders", "Conversion"])[1] ?? "Orders", value: "8,137", delta: "+13.5%" },
      { label: listProp(node, "breakdown", ["Average order", "Orders", "Conversion"])[2] ?? "Conversion", value: "3.9%", delta: "-0.2%" },
    ];
    const target = Number(prop(node, "target", "30000").replace(/[^0-9.]/g, "")) || undefined;
    return (
      <Panel label={label}>
        <div className="grid overflow-hidden rounded-card border border-border bg-surface shadow-sm @4xl:grid-cols-[minmax(0,5fr)_minmax(0,8fr)]">
          <div className="flex flex-col gap-6 border-b border-border p-6 @4xl:border-b-0 @4xl:border-r md:p-8">
            <div className="space-y-3">
              <h2 className="text-small font-semibold text-muted">{label}</h2>
              <p className="font-heading-set text-h1 tabular-nums leading-none">{value}</p>
              <p className="text-small"><Trend delta={delta} /> <span className="text-muted">{context}</span></p>
            </div>
            <dl className="mt-auto divide-y divide-border border-t border-border">
              {breakdown.map((r) => (
                <div key={r.label} className="flex items-center justify-between gap-4 py-3 text-small">
                  <dt className="text-muted">{r.label}</dt>
                  <dd className="flex items-center gap-3"><span className="font-semibold tabular-nums">{r.value}</span><Trend delta={r.delta} className="w-16 justify-end text-caption" /></dd>
                </div>))}
            </dl>
          </div>
          <div className="p-6 md:p-8">
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <p className="text-small font-semibold">{prop(node, "chart_title", "Monthly against goal")}</p>
              <Segmented label="Time range" options={["6M", "12M"]} value={range_} onChange={setRange} />
            </div>
            <XYChart kind="bar" labels={range_ === "6M" ? labels.slice(-6) : labels} series={[{ name: label, values: range_ === "6M" ? a.slice(-6) : a, tone: "accent" }]}
              format={money} target={target} targetLabel={prop(node, "target_label", "Goal")} label={`${label} by month`} height={260} />
          </div>
        </div>
      </Panel>
    );
  }
  return (
    <Panel label={label}>
      <div className="relative overflow-hidden rounded-card border border-border bg-surface shadow-sm">
        <div aria-hidden className="pointer-events-none absolute inset-x-0 top-0 h-40 opacity-60"
          style={{ background: "radial-gradient(60% 100% at 0% 0%, color-mix(in srgb, var(--color-accent) 14%, transparent), transparent)" }} />
        <div className="relative flex flex-wrap items-start justify-between gap-6 p-6 md:p-8">
          <div className="space-y-4">
            <h2 className="flex items-center gap-2 text-small font-semibold text-muted">
              <span aria-hidden className="size-2 rounded-pill bg-accent" />{label}
            </h2>
            <p className="font-heading-set text-display tabular-nums leading-none">{value}</p>
            <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-small">
              <Trend delta={delta} className="rounded-pill border border-border bg-bg px-2.5 py-1" />
              <span className="text-muted">{context}</span>
            </p>
          </div>
          <div className="flex flex-col items-end gap-4">
            <Segmented label="Time range" options={["3M", "6M", "12M"]} value={range_} onChange={setRange} />
            <Legend series={[{ name: prop(node, "series", "This year"), values: [], tone: "accent" }, { name: prop(node, "compare_series", "Last year"), values: [], tone: "muted" }]} />
          </div>
        </div>
        <div className="relative px-4 pb-5 md:px-6">
          {(() => {
            const k = range_ === "3M" ? 3 : range_ === "6M" ? 6 : 12;
            return <XYChart kind="area" labels={labels.slice(-k)} label={`${label} by month`} format={money} height={220}
              series={[{ name: prop(node, "series", "This year"), values: a.slice(-k), tone: "accent" }, { name: prop(node, "compare_series", "Last year"), values: b.slice(-k), tone: "muted" }]} />;
          })()}
        </div>
      </div>
    </Panel>
  );
}

/* ================================================================== data table */

const CUSTOMERS = [
  { name: "Maya Chen", email: "maya@northfield.co", status: "Active", plan: "Annual", spend: 2480, last: "Today, 9:41" },
  { name: "Jonas Weber", email: "jonas@weber.studio", status: "Trial", plan: "Monthly", spend: 120, last: "Yesterday" },
  { name: "Priya Nair", email: "priya@lumen.shop", status: "Past due", plan: "Monthly", spend: 640, last: "Sep 18" },
  { name: "Leo Martin", email: "leo@martinandco.com", status: "Active", plan: "Wholesale", spend: 12900, last: "Sep 17" },
  { name: "Ava Rossi", email: "ava@rossi.design", status: "Paused", plan: "Annual", spend: 1560, last: "Sep 12" },
  { name: "Sam Okafor", email: "sam@okafor.org", status: "Active", plan: "Monthly", spend: 890, last: "Sep 9" },
  { name: "Nora Lind", email: "nora@lindhaus.se", status: "Pending", plan: "Wholesale", spend: 7420, last: "Sep 8" },
  { name: "Kenji Sato", email: "kenji@sato.jp", status: "Active", plan: "Annual", spend: 3110, last: "Sep 6" },
  { name: "Elena Duarte", email: "elena@duarte.mx", status: "Trial", plan: "Monthly", spend: 60, last: "Sep 4" },
  { name: "Tom Becker", email: "tom@becker.de", status: "Active", plan: "Monthly", spend: 1045, last: "Sep 2" },
];
const usd = (v: number) => `$${v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

function RowMenu({ name }: { name: string }) {
  return (
    <button type="button" aria-label={`More actions for ${name}`}
      className="grid size-9 place-items-center rounded-button text-muted transition-colors duration-200 hover:bg-fg/[0.06] hover:text-fg">
      <MoreHorizontal className="size-4" />
    </button>
  );
}

function DataTable({ node }: NodeProps) {
  const variant = variantOf(node);
  const dense = variant === "dense";
  const toolbar = variant === "with_toolbar";
  const title = prop(node, "title", "Customers");
  const headers = listProp(node, "columns", ["Customer", "Status", "Plan", "Spend", "Last active"]);
  const filters = listProp(node, "filters", ["All", "Active", "Trial", "Past due"]);
  const [filter, setFilter] = useState(filters[0]);
  const [query, setQuery] = useState("");
  const [sortDesc, setSortDesc] = useState<boolean | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set(toolbar ? ["Leo Martin"] : []));
  const searchId = useId();

  const rows = useMemo(() => {
    let r = CUSTOMERS.slice(0, dense ? 10 : 6);
    if (toolbar && filter !== filters[0]) r = r.filter((c) => c.status.toLowerCase() === filter.toLowerCase());
    if (query.trim()) r = r.filter((c) => `${c.name} ${c.email}`.toLowerCase().includes(query.trim().toLowerCase()));
    if (sortDesc !== null) r = [...r].sort((x, y) => (sortDesc ? y.spend - x.spend : x.spend - y.spend));
    return r;
  }, [dense, toolbar, filter, filters, query, sortDesc]);

  const allOn = rows.length > 0 && rows.every((r) => selected.has(r.name));
  const toggle = (name: string) => setSelected((s) => { const n = new Set(s); if (n.has(name)) n.delete(name); else n.add(name); return n; });
  const cell = cn(dense ? "px-4 py-2" : "px-5 py-3.5", "first:pl-5 last:pr-5 md:first:pl-6 md:last:pr-4");
  const h = (i: number, fb: string) => headers[i] ?? fb;

  const actions = (
    <div className="flex flex-wrap items-center gap-2">
      <Button variant="secondary" size="sm"><Download aria-hidden className="size-4" />{prop(node, "secondary_cta", "Export")}</Button>
      <Button size="sm"><Plus aria-hidden className="size-4" />{prop(node, "cta", "Add customer")}</Button>
    </div>
  );

  return (
    <Panel label={title}>
      <div className="overflow-hidden rounded-card border border-border bg-surface text-fg shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 px-5 pt-5 md:px-6">
          <div className="min-w-0">
            <h2 className="flex items-center gap-2 text-body font-semibold tracking-tight">
              {title}<span className="rounded-pill bg-fg/[0.06] px-2 py-0.5 text-caption font-semibold tabular-nums text-muted">248</span>
            </h2>
            {!dense && <p className="mt-1 text-small text-muted">{prop(node, "subtitle", "Everyone who has bought from you in the last 90 days.")}</p>}
          </div>
          {!toolbar && actions}
        </div>

        {toolbar && (
          <div className="mt-4 flex flex-col gap-3 border-y border-border bg-bg/60 px-5 py-3 md:px-6 @3xl:flex-row @3xl:items-center">
            <div className="relative min-w-0 flex-1 @3xl:max-w-xs">
              <label htmlFor={searchId} className="sr-only">Search {title.toLowerCase()}</label>
              <Search aria-hidden className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted" />
              <input id={searchId} type="search" value={query} onChange={(e) => setQuery(e.target.value)}
                placeholder={prop(node, "search_placeholder", "Search by name or email")}
                className="h-10 min-h-0 w-full rounded-button border border-border bg-bg pl-9 pr-3 text-small text-fg placeholder:text-muted transition-[border-color,box-shadow] duration-200 focus:border-ring focus:outline-none focus:ring-4 focus:ring-ring/15" />
            </div>
            <div className="-mx-1 overflow-x-auto px-1"><Segmented label="Filter by status" options={filters} value={filter} onChange={setFilter} /></div>
            <Button variant="secondary" size="sm" className="self-start @3xl:self-auto"><SlidersHorizontal aria-hidden className="size-4" />More filters</Button>
            <div className="@3xl:ml-auto">{actions}</div>
          </div>)}

        {toolbar && selected.size > 0 && (
          <div className="flex flex-wrap items-center gap-3 border-b border-border px-5 py-2 text-small md:px-6" aria-live="polite">
            <span className="font-semibold">{selected.size} selected</span>
            <Button variant="ghost" size="sm" onClick={() => setSelected(new Set())}>Clear</Button>
            <Button variant="ghost" size="sm"><Archive aria-hidden className="size-4" />Archive</Button>
          </div>)}

        <div role="region" aria-label={`${title} table`} tabIndex={0} className={cn("relative overflow-x-auto focus-visible:outline-offset-[-2px]", !toolbar && "mt-4 border-t border-border")}>
          <table className={cn("w-full min-w-[720px] border-collapse text-left", dense ? "text-small" : "text-small")}>
            <thead className="bg-bg/60">
              <tr className="border-b border-border text-caption font-semibold uppercase tracking-[0.06em] text-muted">
                {toolbar && (
                  <th scope="col" className={cn(cell, "w-10 pr-0")}>
                    <label className="-m-2 inline-grid size-9 cursor-pointer place-items-center align-middle">
                      <input type="checkbox" aria-label="Select all rows" checked={allOn}
                        onChange={() => setSelected(allOn ? new Set() : new Set(rows.map((r) => r.name)))} className="size-4 min-h-0 cursor-pointer p-0 accent-[var(--color-accent)]" />
                    </label>
                  </th>)}
                <th scope="col" className={cn(cell, "font-semibold")}>{h(0, "Customer")}</th>
                <th scope="col" className={cn(cell, "font-semibold")}>{h(1, "Status")}</th>
                <th scope="col" className={cn(cell, "font-semibold")}>{h(2, "Plan")}</th>
                <th scope="col" className={cn(cell, "text-right font-semibold")} aria-sort={sortDesc === null ? "none" : sortDesc ? "descending" : "ascending"}>
                  <button type="button" onClick={() => setSortDesc((d) => !(d ?? false))}
                    className="-mx-2 inline-flex min-h-7 items-center gap-1 rounded-sm px-2 uppercase tracking-[0.06em] transition-colors hover:text-fg">
                    {h(3, "Spend")}<ChevronsUpDown aria-hidden className="size-3.5" />
                  </button>
                </th>
                <th scope="col" className={cn(cell, "font-semibold")}>{h(4, "Last active")}</th>
                <th scope="col" className={cn(cell, "w-12")}><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {rows.map((c) => {
                const on = selected.has(c.name);
                return (
                  <tr key={c.name} className={cn("transition-colors duration-150 hover:bg-fg/[0.025]", on && "bg-accent/[0.05] hover:bg-accent/[0.07]")}>
                    {toolbar && (
                      <td className={cn(cell, "pr-0")}>
                        <label className="-m-2 inline-grid size-9 cursor-pointer place-items-center align-middle">
                          <input type="checkbox" aria-label={`Select ${c.name}`} checked={on} onChange={() => toggle(c.name)} className="size-4 min-h-0 cursor-pointer p-0 accent-[var(--color-accent)]" />
                        </label>
                      </td>)}
                    <td className={cell}>
                      {dense ? <span className="font-medium">{c.name}</span> : (
                        <div className="flex items-center gap-3">
                          <Avatar name={c.name} className="size-9 text-caption" />
                          <div className="min-w-0">
                            <p className="truncate font-semibold">{c.name}</p>
                            <p className="truncate text-caption text-muted">{c.email}</p>
                          </div>
                        </div>)}
                    </td>
                    <td className={cell}><StatusBadge>{c.status}</StatusBadge></td>
                    <td className={cn(cell, "text-muted")}>{c.plan}</td>
                    <td className={cn(cell, "text-right font-semibold tabular-nums")}>{usd(c.spend)}</td>
                    <td className={cn(cell, "whitespace-nowrap text-muted")}>{c.last}</td>
                    <td className={cn(cell, "py-1 text-right")}><RowMenu name={c.name} /></td>
                  </tr>
                );
              })}
              {rows.length === 0 && (
                <tr><td colSpan={toolbar ? 7 : 6} className="px-6 py-12 text-center text-small text-muted">No {title.toLowerCase()} match these filters.</td></tr>)}
            </tbody>
          </table>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border px-5 py-3 text-small md:px-6">
          <p className="text-muted">Showing <span className="font-semibold text-fg tabular-nums">1–{rows.length}</span> of <span className="font-semibold text-fg tabular-nums">248</span></p>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" disabled aria-label="Previous page"><ChevronLeft aria-hidden className="size-4" />Previous</Button>
            <Button variant="secondary" size="sm" aria-label="Next page">Next<ChevronRight aria-hidden className="size-4" /></Button>
          </div>
        </div>
      </div>
    </Panel>
  );
}

/* ================================================================== activity feed */

type FeedEvent = { actor: string; action: string; target?: string; time: string; icon: LucideIcon; tone?: StatusTone; comment?: string; day: string };
const EVENTS: FeedEvent[] = [
  { actor: "Maya Chen", action: "placed order", target: "#4821", time: "2m ago", icon: ShoppingBag, day: "Today" },
  { actor: "Priya Nair", action: "commented on", target: "Autumn menu launch", time: "38m ago", icon: MessageSquare, day: "Today",
    comment: "Photos look wonderful. Could we move the tasting to Thursday so the whole team can join?" },
  { actor: "Payouts", action: "sent $2,840.00 to the account ending", target: "4410", time: "2h ago", icon: Banknote, tone: "success", day: "Today" },
  { actor: "Jonas Weber", action: "left a 5-star review on", target: "Morning Ritual", time: "Yesterday, 16:20", icon: Star, day: "Yesterday" },
  { actor: "Inventory", action: "Garden Reserve is running low:", target: "12 left", time: "Yesterday, 11:05", icon: AlertTriangle, tone: "warning", day: "Yesterday" },
  { actor: "Leo Martin", action: "invited", target: "2 teammates", time: "Yesterday, 09:12", icon: UserPlus, day: "Yesterday" },
];
const EVENT_TONE: Record<StatusTone, string> = {
  success: "text-success", warning: "text-warning", danger: "text-danger", info: "text-fg", neutral: "text-muted",
};

function ActivityFeed({ node }: NodeProps) {
  const variant = variantOf(node);
  const title = prop(node, "title", "Recent activity");
  const custom = listProp(node, "items", []);
  const events: FeedEvent[] = custom.length
    ? custom.map((t, i) => ({ ...EVENTS[i % EVENTS.length], actor: "", action: t, target: undefined, comment: undefined }))
    : EVENTS;
  const cta = <Button variant="ghost" size="sm">{prop(node, "cta", "View all")}<ChevronRight aria-hidden className="size-4" /></Button>;
  const Line = ({ e }: { e: FeedEvent }) => (
    <>{e.actor && <span className="font-semibold">{e.actor} </span>}<span className="text-muted">{e.action}</span>
      {e.target && <span className="font-medium"> {e.target}</span>}</>
  );

  if (variant === "compact") {
    return (
      <Panel label={title}>
        <PanelCard title={title} action={cta} bodyClassName="pt-2">
          <ul className="divide-y divide-border">
            {events.map((e, i) => (
              <li key={i} className="flex items-center gap-3 py-2.5 text-small">
                <span aria-hidden className={cn("size-2 shrink-0 rounded-pill", e.tone ? STATUS_DOT[e.tone] : "bg-border")} />
                <p className="min-w-0 flex-1 truncate"><Line e={e} /></p>
                <span className="shrink-0 text-caption tabular-nums text-muted">{e.time}</span>
              </li>))}
          </ul>
        </PanelCard>
      </Panel>
    );
  }
  const days = [...new Set(events.map((e) => e.day))];
  return (
    <Panel label={title}>
      <PanelCard title={title} subtitle={prop(node, "subtitle", "What changed across your workspace.")} action={cta}>
        <div className="space-y-6">
          {days.map((d) => (
            <div key={d}>
              <p className="mb-3 text-caption font-semibold uppercase tracking-[0.14em] text-muted">{d}</p>
              <ol className="relative">
                {events.filter((e) => e.day === d).map((e, i, arr) => {
                  const Icon = e.icon;
                  return (
                    <li key={i} className="relative flex gap-4 pb-5 last:pb-0">
                      {i < arr.length - 1 && <span aria-hidden className="absolute bottom-0 left-[17px] top-10 w-px bg-border" />}
                      {e.tone || !e.actor || e.actor === "Payouts" || e.actor === "Inventory"
                        ? <span aria-hidden className={cn("grid size-9 shrink-0 place-items-center rounded-pill border border-border bg-bg", EVENT_TONE[e.tone ?? "neutral"])}><Icon className="size-4" /></span>
                        : <Avatar name={e.actor} className="size-9 text-caption" />}
                      <div className="min-w-0 flex-1 pt-1.5">
                        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-0.5">
                          <p className="text-small"><Line e={e} /></p>
                          <span className="text-caption tabular-nums text-muted">{e.time}</span>
                        </div>
                        {e.comment && <p className="mt-2 rounded-button border border-border bg-bg px-3.5 py-2.5 text-small text-pretty">{e.comment}</p>}
                      </div>
                    </li>
                  );
                })}
              </ol>
            </div>))}
        </div>
      </PanelCard>
    </Panel>
  );
}

/* ================================================================== progress list */

const GOALS = [
  { label: "Monthly revenue", detail: "$41,800 of $50,000", pct: 84, due: "8 days left" },
  { label: "New customers", detail: "312 of 400", pct: 78, due: "8 days left" },
  { label: "Five-star reviews", detail: "120 of 120", pct: 100, due: "Reached Sep 14" },
  { label: "Wholesale accounts", detail: "6 of 15", pct: 40, due: "12 days left" },
  { label: "Newsletter sign-ups", detail: "1,940 of 2,500", pct: 77, due: "20 days left" },
];
const goalStatus = (pct: number, i: number) => (pct >= 100 ? "Completed" : pct < 50 && i > 0 ? "At risk" : "On track");

function Ring({ pct, label }: { pct: number; label: string }) {
  const r = 22, C = 2 * Math.PI * r;
  const done = pct >= 100;
  return (
    <svg role="img" aria-label={label} viewBox="0 0 56 56" className="size-14 shrink-0 -rotate-90">
      <circle cx="28" cy="28" r={r} fill="none" stroke="var(--color-border)" strokeWidth="6" />
      <circle cx="28" cy="28" r={r} fill="none" stroke={done ? "var(--color-success)" : "var(--color-accent)"} strokeWidth="6"
        strokeLinecap="round" strokeDasharray={`${(Math.min(pct, 100) / 100) * C} ${C}`} />
    </svg>
  );
}

function ProgressList({ node, columns }: NodeProps) {
  const variant = variantOf(node);
  const title = prop(node, "title", "Goals this month");
  const labels = listProp(node, "items", GOALS.map((g) => g.label));
  const pcts = numbers(node, "values", GOALS.map((g) => g.pct));
  const details = listProp(node, "details", []);
  const goals = labels.map((label, i) => {
    const g = GOALS[i % GOALS.length];
    const pct = Math.max(0, Math.min(100, pcts[i] ?? g.pct));
    return { ...g, label, pct, detail: details[i] ?? (labels[i] === g.label ? g.detail : `${pct}% complete`), status: goalStatus(pct, i) };
  });

  if (variant === "cards") {
    return (
      <Panel label={title}>
        <h2 className="mb-3 text-body font-semibold tracking-tight">{title}</h2>
        <ul className="grid grid-cols-1 gap-3 @lg:grid-cols-2 @4xl:grid-cols-[repeat(var(--cols),minmax(0,1fr))] md:gap-4"
          style={{ ["--cols" as string]: columns ?? Math.min(goals.length, 4) }}>
          {goals.slice(0, 4).map((g) => (
            <li key={g.label} className="flex items-center gap-4 rounded-card border border-border bg-surface p-5 shadow-sm">
              <div className="relative">
                <Ring pct={g.pct} label={`${g.label}: ${g.pct}% complete`} />
                <span aria-hidden className="absolute inset-0 grid place-items-center text-caption font-semibold tabular-nums">{g.pct >= 100 ? <Check className="size-5 text-success" /> : `${g.pct}%`}</span>
              </div>
              <div className="min-w-0">
                <h3 className="truncate text-small font-semibold">{g.label}</h3>
                <p className="mt-0.5 truncate text-small tabular-nums text-muted">{g.detail}</p>
                <p className="mt-2"><StatusBadge>{g.status}</StatusBadge></p>
              </div>
            </li>))}
        </ul>
      </Panel>
    );
  }
  return (
    <Panel label={title}>
      <PanelCard title={title} subtitle={prop(node, "subtitle", "Progress resets on the first of every month.")}
        action={<Button variant="ghost" size="sm"><Plus aria-hidden className="size-4" />{prop(node, "cta", "New goal")}</Button>}>
        <ul className="space-y-5">
          {goals.map((g) => (
            <li key={g.label}>
              <div className="mb-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                <h3 className="flex items-center gap-2 text-small font-semibold">
                  {g.pct >= 100 && <CheckCircle2 aria-hidden className="size-4 text-success" />}{g.label}
                </h3>
                <p className="text-small tabular-nums"><span className="text-muted">{g.detail}</span><span className="ml-3 font-semibold">{g.pct}%</span></p>
              </div>
              <div role="progressbar" aria-label={g.label} aria-valuenow={g.pct} aria-valuemin={0} aria-valuemax={100}
                className="h-2 overflow-hidden rounded-pill bg-fg/[0.07]">
                <div className={cn("h-full rounded-pill transition-[width] duration-700 ease-brand",
                  g.pct >= 100 ? "bg-success" : g.status === "At risk" ? "bg-warning" : "bg-accent")} style={{ width: `${g.pct}%` }} />
              </div>
              <p className="mt-1.5 flex items-center gap-2 text-caption text-muted">
                <span className={cn("font-semibold", g.status === "Completed" ? "text-success" : g.status === "At risk" ? "text-warning" : "text-fg")}>{g.status}</span>
                <span aria-hidden>·</span>{g.due}
              </p>
            </li>))}
        </ul>
      </PanelCard>
    </Panel>
  );
}

/* ================================================================== notification list */

type Note = { id: number; actor: string; text: string; target: string; time: string; unread: boolean; kind: "mention" | "system" | "order";
  actions?: [string, string]; icon?: LucideIcon; tone?: StatusTone; day: string };
const NOTES: Note[] = [
  { id: 1, actor: "Priya Nair", text: "mentioned you in", target: "Autumn menu launch", time: "4m", unread: true, kind: "mention", day: "Today" },
  { id: 2, actor: "Leo Martin", text: "requested access to", target: "Wholesale price list", time: "26m", unread: true, kind: "system", actions: ["Approve", "Decline"], day: "Today" },
  { id: 3, actor: "Orders", text: "Order #4821 is ready for pickup at", target: "Main Street", time: "1h", unread: true, kind: "order", icon: ShoppingBag, day: "Today" },
  { id: 4, actor: "Payouts", text: "Your weekly payout of $2,840.00 has been", target: "sent", time: "3h", unread: false, kind: "system", icon: CheckCircle2, tone: "success", day: "Today" },
  { id: 5, actor: "Ava Rossi", text: "replied to your comment on", target: "Window display ideas", time: "Yesterday", unread: false, kind: "mention", day: "Earlier" },
  { id: 6, actor: "Inventory", text: "Garden Reserve dropped below", target: "15 units", time: "Yesterday", unread: false, kind: "system", icon: AlertTriangle, tone: "warning", day: "Earlier" },
];

function NotificationList({ node }: NodeProps) {
  const variant = variantOf(node);
  const compactView = variant === "compact";
  const title = prop(node, "title", "Notifications");
  const tabs = listProp(node, "tabs", ["All", "Unread", "Mentions"]);
  const [items, setItems] = useState(NOTES);
  const [tab, setTab] = useState(tabs[0]);
  const unread = items.filter((n) => n.unread).length;
  const shown = items.filter((n) => tab === tabs[1] ? n.unread : tab === tabs[2] ? n.kind === "mention" : true);
  const markRead = (id: number) => setItems((xs) => xs.map((x) => (x.id === id ? { ...x, unread: false } : x)));
  const archive = (id: number) => setItems((xs) => xs.filter((x) => x.id !== id));

  const list = (
    <ul className="divide-y divide-border">
      {shown.map((n) => {
        const Icon = n.icon;
        return (
          <li key={n.id} className={cn("group relative flex gap-3.5 px-5 py-4 transition-colors duration-200 md:px-6", n.unread ? "bg-accent/[0.045]" : "hover:bg-fg/[0.02]")}>
            <span aria-hidden className={cn("absolute left-2 top-9 size-2 -translate-y-1/2 rounded-pill bg-accent transition-opacity md:left-2.5", !n.unread && "opacity-0")} />
            {Icon
              ? <span aria-hidden className={cn("grid size-10 shrink-0 place-items-center rounded-pill border border-border bg-bg", EVENT_TONE[n.tone ?? "info"])}><Icon className="size-[18px]" /></span>
              : <Avatar name={n.actor} className="size-10 text-caption" />}
            <div className="min-w-0 flex-1">
              <p className="text-small text-pretty">
                {n.unread && <span className="sr-only">Unread: </span>}
                <span className="font-semibold">{n.actor}</span> <span className="text-muted">{n.text}</span> <span className="font-medium">{n.target}</span>
              </p>
              <p className="mt-0.5 text-caption text-muted">{n.time}{n.time.length < 5 ? " ago" : ""}</p>
              {n.actions && !compactView && (
                <div className="mt-3 flex gap-2">
                  <Button size="sm" onClick={() => markRead(n.id)}>{n.actions[0]}</Button>
                  <Button size="sm" variant="secondary" onClick={() => archive(n.id)}>{n.actions[1]}</Button>
                </div>)}
            </div>
            <div className="flex shrink-0 items-start gap-1 opacity-100 transition-opacity duration-200 md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100">
              {n.unread && (
                <button type="button" aria-label={`Mark notification from ${n.actor} as read`} onClick={() => markRead(n.id)}
                  className="grid size-9 place-items-center rounded-button text-muted transition-colors hover:bg-fg/[0.06] hover:text-fg"><Check className="size-4" /></button>)}
              <button type="button" aria-label={`Archive notification from ${n.actor}`} onClick={() => archive(n.id)}
                className="grid size-9 place-items-center rounded-button text-muted transition-colors hover:bg-fg/[0.06] hover:text-fg"><Archive className="size-4" /></button>
            </div>
          </li>
        );
      })}
      {shown.length === 0 && (
        <li className="flex flex-col items-center gap-2 px-6 py-12 text-center">
          <span aria-hidden className="grid size-11 place-items-center rounded-pill bg-fg/[0.05] text-muted"><Bell className="size-5" /></span>
          <p className="text-small font-semibold">You are all caught up</p>
          <p className="text-small text-muted">New notifications will appear here.</p>
        </li>)}
    </ul>
  );

  const header = (
    <div className="flex flex-wrap items-center justify-between gap-3 px-5 pt-5 md:px-6">
      <h2 className="flex items-center gap-2 text-body font-semibold tracking-tight">
        {title}
        {unread > 0 && <span className="rounded-pill bg-accent px-2 py-0.5 text-caption font-semibold tabular-nums text-accent-fg">{unread} new</span>}
      </h2>
      <Button variant="ghost" size="sm" disabled={unread === 0} onClick={() => setItems((xs) => xs.map((x) => ({ ...x, unread: false })))}>
        <Check aria-hidden className="size-4" />{prop(node, "cta", "Mark all as read")}
      </Button>
    </div>
  );

  if (compactView) {
    // Popover-sized panel: no tabs, one scroll list, a settings link in the footer.
    return (
      <Panel label={title}>
        <div className="mx-auto max-w-md overflow-hidden rounded-lg border border-border bg-surface shadow-lg @3xl:ml-auto @3xl:mr-0">
          {header}
          <div className="mt-3 border-t border-border">{list}</div>
          <div className="flex items-center justify-between border-t border-border px-5 py-2 md:px-6">
            <Button variant="ghost" size="sm">{prop(node, "secondary_cta", "Notification settings")}</Button>
            <Button variant="ghost" size="sm">{prop(node, "footer_cta", "View all")}<ChevronRight aria-hidden className="size-4" /></Button>
          </div>
        </div>
      </Panel>
    );
  }
  return (
    <Panel label={title}>
      <div className="overflow-hidden rounded-card border border-border bg-surface shadow-sm">
        {header}
        <div className="mt-3 border-b border-border px-5 pb-3 md:px-6">
          <Segmented label="Show" options={tabs} value={tab} onChange={setTab} />
        </div>
        {list}
      </div>
    </Panel>
  );
}

/* ================================================================== empty state */

/** Layered cards and a spark, drawn from the palette's roles so it belongs to every brand. */
function EmptyIllustration({ className }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 200 140" className={cn("h-auto w-44", className)}>
      <ellipse cx="100" cy="128" rx="70" ry="6" fill="var(--color-fg)" opacity="0.05" />
      <rect x="44" y="30" width="112" height="80" rx="10" fill="var(--color-surface-alt)" transform="rotate(-6 100 70)" />
      <rect x="40" y="24" width="120" height="86" rx="10" fill="var(--color-bg)" stroke="var(--color-border)" strokeWidth="1.5" />
      <rect x="54" y="40" width="44" height="6" rx="3" fill="var(--color-fg)" opacity="0.14" />
      <rect x="54" y="54" width="92" height="5" rx="2.5" fill="var(--color-fg)" opacity="0.07" />
      <rect x="54" y="66" width="76" height="5" rx="2.5" fill="var(--color-fg)" opacity="0.07" />
      <rect x="54" y="84" width="34" height="12" rx="6" fill="var(--color-accent)" opacity="0.18" />
      <circle cx="150" cy="30" r="16" fill="var(--color-accent)" />
      <path d="M150 22v16M142 30h16" stroke="var(--color-accent-fg)" strokeWidth="3" strokeLinecap="round" />
      <path d="M28 52l3 7 7 3-7 3-3 7-3-7-7-3 7-3z" fill="var(--color-accent)" opacity="0.5" />
      <circle cx="172" cy="96" r="3" fill="var(--color-fg)" opacity="0.18" />
    </svg>
  );
}

function EmptyState({ node }: NodeProps) {
  const variant = variantOf(node);
  const title = prop(node, "title", "No collections yet");
  const body = prop(node, "body", "Group your favourite pieces into a collection to feature them on your storefront and share them with guests.");
  const primary = prop(node, "primary_cta", "Create collection");
  const secondary = prop(node, "secondary_cta", "Learn how collections work");

  if (variant === "compact") {
    return (
      <Panel label={title}>
        <div className="flex flex-col gap-4 rounded-card border border-dashed border-border bg-surface p-5 @xl:flex-row @xl:items-center md:p-6">
          <span aria-hidden className="grid size-12 shrink-0 place-items-center rounded-card bg-accent/10 text-accent"><FolderOpen className="size-6" /></span>
          <div className="min-w-0 flex-1">
            <h2 className="text-body font-semibold">{title}</h2>
            <p className="mt-1 text-small text-muted text-pretty">{body}</p>
          </div>
          <Button size="sm" href={hrefOf(node, "primary_cta")} data-role="primary_cta" className="self-start @xl:self-auto"><Plus aria-hidden className="size-4" />{primary}</Button>
        </div>
      </Panel>
    );
  }
  return (
    <Panel label={title}>
      <div className="relative overflow-hidden rounded-card border border-border bg-surface px-6 py-14 text-center md:py-20">
        <div aria-hidden className="pointer-events-none absolute inset-0 opacity-70 [mask-image:radial-gradient(50%_60%_at_50%_40%,black,transparent)]"
          style={{ backgroundImage: "linear-gradient(var(--color-border) 1px, transparent 1px), linear-gradient(90deg, var(--color-border) 1px, transparent 1px)", backgroundSize: "28px 28px" }} />
        <div className="relative mx-auto flex max-w-lg flex-col items-center">
          <EmptyIllustration className="mb-8 w-52" />
          <h2 className="font-heading-set text-h4 text-balance">{title}</h2>
          <p className="mt-3 text-body text-muted text-pretty">{body}</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button href={hrefOf(node, "primary_cta")} data-role="primary_cta"><Plus aria-hidden className="size-4" />{primary}</Button>
            <Button variant="secondary">{secondary}</Button>
          </div>
        </div>
      </div>
    </Panel>
  );
}

/* ================================================================== alert banner */

type AlertTone = "info" | "success" | "warning" | "danger";
const ALERT: Record<AlertTone, { icon: LucideIcon; box: string; icon_: string; title: string; body: string; cta?: string; secondary?: string; items?: string[] }> = {
  info: { icon: Info, box: "border-border bg-surface", icon_: "text-fg", title: "Holiday hours are coming up",
    body: "Update your opening times before December 20 so guests see the right hours on your page.", cta: "Update hours" },
  success: { icon: CheckCircle2, box: "border-success/30 bg-success/[0.07]", icon_: "text-success", title: "Your changes have been published",
    body: "The new menu is live and visible to everyone." },
  warning: { icon: AlertTriangle, box: "border-warning/35 bg-warning/[0.08]", icon_: "text-warning", title: "Your card expires next month",
    body: "Add a new payment method to avoid any interruption to deliveries and payouts.", cta: "Update card", secondary: "Remind me later" },
  danger: { icon: XCircle, box: "border-danger/30 bg-danger/[0.06]", icon_: "text-danger", title: "We could not import 3 products",
    body: "Fix these rows in your file and upload it again:", items: ["Row 12: price is missing", "Row 27: image link is broken", "Row 41: duplicate product name"], cta: "Upload again" },
};
const toAlertTone = (s: string, fb: AlertTone): AlertTone => (["info", "success", "warning", "danger"].includes(s) ? s as AlertTone : fb);

function AlertBanner({ node }: NodeProps) {
  const variant = variantOf(node, "info");
  const banner = variant === "banner";
  const tone = toAlertTone(banner ? prop(node, "tone", "info") : variant, "info");
  const a = ALERT[tone];
  const [open, setOpen] = useState(true);
  const title = prop(node, "title", banner ? "New: gift cards are now available in your shop" : a.title);
  const body = prop(node, "body", a.body);
  const cta = prop(node, "cta", banner ? "Set them up" : a.cta ?? "");
  const secondary = prop(node, "secondary_cta", a.secondary ?? "");
  const Icon = a.icon;
  if (!open) return null;
  const dismiss = (
    <button type="button" aria-label="Dismiss" onClick={() => setOpen(false)}
      className="grid size-9 shrink-0 place-items-center rounded-button text-muted transition-colors hover:bg-fg/[0.06] hover:text-fg"><X className="size-4" /></button>
  );

  if (banner) {
    // Full-width announcement bar: one line, sits flush above page content.
    return (
      <section aria-label="Announcement" className="border-b border-border bg-surface-alt page-x">
        <div role="status" className="container-wide flex items-center gap-3 py-2">
          <span aria-hidden className={cn("hidden size-7 shrink-0 place-items-center rounded-pill bg-bg sm:grid", a.icon_)}><Icon className="size-4" /></span>
          <p className="min-w-0 flex-1 text-small"><span className="font-semibold">{title}</span>{" "}
            {cta && <a href="#" className="inline-flex min-h-6 items-center gap-1 font-semibold underline decoration-fg/30 underline-offset-4 hover:decoration-fg">{cta}<ChevronRight aria-hidden className="size-3.5" /></a>}
          </p>
          {dismiss}
        </div>
      </section>
    );
  }
  return (
    <section aria-label={title} className="page-x py-3 md:py-4">
      <div className="container-wide">
        <div role={tone === "danger" || tone === "warning" ? "alert" : "status"}
          className={cn("flex gap-3 rounded-card border p-4 text-fg md:gap-4 md:p-5", a.box, tone === "success" && "items-center")}>
          <Icon aria-hidden className={cn("mt-0.5 size-5 shrink-0", a.icon_, tone === "success" && "mt-0")} />
          <div className={cn("min-w-0 flex-1", tone === "success" && "flex flex-wrap items-baseline gap-x-2")}>
            <h2 className="text-small font-semibold">{title}</h2>
            <p className={cn("text-small text-muted text-pretty", tone !== "success" && "mt-1")}>{body}</p>
            {a.items && (
              <ul className="mt-2 space-y-1 text-small">
                {a.items.map((it) => <li key={it} className="flex gap-2"><span aria-hidden className="mt-2 size-1 shrink-0 rounded-pill bg-danger" />{it}</li>)}
              </ul>)}
            {(cta || secondary) && tone !== "success" && (
              <div className="mt-3 flex flex-wrap gap-2">
                {cta && <Button size="sm" variant={tone === "info" ? "secondary" : "primary"}>{cta}</Button>}
                {secondary && <Button size="sm" variant="ghost">{secondary}</Button>}
              </div>)}
          </div>
          {dismiss}
        </div>
      </div>
    </section>
  );
}

export const SECTIONS: SectionMap = {
  Stats, ChartPanel, KpiHero, DataTable, ActivityFeed, ProgressList, NotificationList, EmptyState, AlertBanner,
};
