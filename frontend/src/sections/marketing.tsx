/** Marketing sections. Keys are the catalog's implementation.root names. See sections/README.md. */
import { Children, useState, type ReactNode } from "react";
import * as ToggleGroup from "@radix-ui/react-toggle-group";
import {
  Apple, ArrowUpRight, Award, BadgeCheck, CalendarCheck, Check, Clock, CreditCard, Gift, Globe, Heart, Layers,
  Leaf, Lock, MapPin, Package, Palette, Play, Quote, ShieldCheck, Sparkles, Star, Truck, Users, Zap,
  type LucideIcon,
} from "lucide-react";
import { Avatar, Badge, Button, Carousel, Eyebrow, Marquee, Media, Rating, Section, SectionHeader, imageAt, listProp, prop, range, subjectOf, variantOf, type Subject } from "../ui";
import { cn } from "../lib/cn";
import type { RenderNode } from "../types";
import type { NodeProps, SectionMap } from "./types";

/**
 * A list slot whose entries carry several parts: "Title|Body,Title|Body". An entry without a part
 * leaves it empty rather than borrowing mismatched fallback copy.
 */
const entries = (n: RenderNode, key: string, fallback: string[][]): string[][] => {
  const v = n.props[key];
  if (typeof v !== "string" || !v.trim()) return fallback;
  return listProp(n, key, []).map((e) => e.split("|").map((s) => s.trim()));
};

/** Stable small hash, so a card without an index still picks a varied icon and image tone. */
const hash = (s: string) => [...s].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7);

const ICONS: Record<string, LucideIcon> = {
  sparkles: Sparkles, leaf: Leaf, clock: Clock, gift: Gift, truck: Truck, package: Package, heart: Heart,
  shield: ShieldCheck, star: Star, palette: Palette, layers: Layers, zap: Zap, globe: Globe, users: Users,
  map: MapPin, calendar: CalendarCheck, card: CreditCard, award: Award,
};
const ICON_ORDER = Object.values(ICONS);
const iconOf = (name: string, seed: string): LucideIcon => ICONS[name.toLowerCase()] ?? ICON_ORDER[hash(seed) % ICON_ORDER.length];

/** Grids that follow the layout engine's desktop column count; phones and tablets collapse. */
const colsGrid = "grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-[repeat(var(--cols),minmax(0,1fr))]";
const colsVar = (columns: number | undefined, fallback: number) => ({ ["--cols" as string]: columns ?? fallback });

/* ================================================================== hero */
function HeroCopy({ node, align = "start", size = "h1" }: NodeProps & { align?: "start" | "center"; size?: "h1" | "display" }) {
  return (
    <div className={cn("flex flex-col gap-6", align === "center" ? "items-center text-center" : "items-start")}>
      <Eyebrow>{prop(node, "eyebrow", "New season")}</Eyebrow>
      <h1 className={cn("font-heading-set text-balance", size === "display" ? "text-display" : "text-h1")}>
        {prop(node, "headline", "Crafted slowly. Made to be savoured.")}
      </h1>
      <p className={cn("max-w-xl text-lead text-muted text-pretty", align === "center" && "mx-auto")}>
        {prop(node, "subhead", "Small-batch goods chosen with care, delivered while they are at their best.")}
      </p>
      <div className="mt-2 flex flex-wrap gap-3">
        <Button size="lg" arrow>{prop(node, "primary_cta", "Shop the collection")}</Button>
        <Button size="lg" variant="secondary">{prop(node, "secondary_cta", "Our story")}</Button>
      </div>
    </div>
  );
}

function Hero(props: NodeProps) {
  const { node } = props;
  const variant = variantOf(node);
  const subject = subjectOf(prop(node, "media", ""), "product");
  const src = imageAt(node, "media")?.url;
  const label = prop(node, "media_label", "Featured product");

  if (variant === "editorial") {
    // Asymmetric: display type over eight columns, a tall image offset to the right and a second
    // image overlapping its lower edge, so the composition reads as a magazine spread.
    return (
      <Section label="Hero" size="lg" wide>
        <div className="grid items-end gap-10 lg:grid-cols-12">
          <div className="lg:col-span-7 lg:pb-16"><HeroCopy {...props} size="display" /></div>
          <div className="relative lg:col-span-5">
            <Media ratio="4/5" subject={subject} src={src} label={label} className="shadow-xl" />
            <Media ratio="1/1" subject="leaf" tone={2} label="Detail"
              className="absolute -bottom-10 -left-10 hidden w-44 border-4 border-bg shadow-lg md:block lg:-left-24 lg:w-56" />
          </div>
        </div>
      </Section>
    );
  }
  if (variant === "fullbleed") {
    return (
      <section aria-label="Hero" className="relative isolate page-x pb-10 pt-32 md:pb-16 md:pt-72">
        <Media ratio="auto" subject={subject} src={src} label={label} zoom={false}
          className="!absolute inset-0 -z-10 h-full rounded-none" />
        <div className="container-wide">
          <div className="max-w-2xl rounded-lg bg-bg/95 p-8 shadow-xl backdrop-blur md:p-12"><HeroCopy {...props} /></div>
        </div>
      </section>
    );
  }
  if (variant === "product_stack") {
    return (
      <Section label="Hero" size="lg" className="overflow-hidden">
        <HeroCopy {...props} align="center" size="display" />
        <div className="relative mx-auto mt-16 grid max-w-4xl grid-cols-3 items-end gap-4 md:gap-8">
          {(["cup", subject, "glass"] as Subject[]).map((s, i) => (
            <Media key={i} subject={s} src={i === 1 ? src : undefined} tone={i} ratio={i === 1 ? "3/4" : "4/5"} label={`${label} ${i + 1}`}
              className={cn("shadow-xl transition-transform duration-700 ease-brand",
                i === 0 && "md:-rotate-6 md:translate-y-6", i === 2 && "md:rotate-6 md:translate-y-6", i === 1 && "z-10")} />))}
        </div>
      </Section>
    );
  }
  const stacked = variant === "centered" || variant === "aurora";
  return (
    <Section label="Hero" size="lg" className={cn(variant === "aurora" && "relative isolate overflow-hidden")}>
      {variant === "aurora" && (
        <div aria-hidden className="absolute inset-0 -z-10 opacity-70"
          style={{ background: "radial-gradient(60% 50% at 50% 0%, color-mix(in srgb, var(--color-accent) 35%, transparent), transparent), radial-gradient(40% 40% at 85% 30%, color-mix(in srgb, var(--color-media-a) 50%, transparent), transparent)" }} />)}
      {stacked ? (
        <div className="flex flex-col items-center gap-14">
          <HeroCopy {...props} align="center" size="display" />
          <Media ratio="21/9" subject={subject} src={src} label={label} className="shadow-xl" />
        </div>
      ) : (
        <div className="grid items-center gap-12 lg:grid-cols-2">
          <HeroCopy {...props} />
          <div className="relative">
            <Media ratio={variant === "video" ? "16/10" : "5/4"} subject={variant === "video" ? "device" : subject} src={src} label={label} className="shadow-xl" />
            {variant === "video" && (
              <Button variant="inverse" size="lg" className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 shadow-xl hover:-translate-y-1/2" aria-label="Play video">
                <Play aria-hidden className="size-4 fill-current" /> Play film
              </Button>)}
            <Badge tone="primary" className="absolute -bottom-3 left-6 shadow-md">{prop(node, "badge", "Freshly made this week")}</Badge>
          </div>
        </div>
      )}
    </Section>
  );
}

/* ================================================================== social proof */
const LOGOS = ["Kettle & Co", "Nordvik", "Maison Vale", "Common Ground", "Fieldwork", "atelier.one"];

/** Wordmarks set in different type treatments, so a strip of names reads as a strip of logos. */
function Wordmark({ name, i }: { name: string; i: number }) {
  const style = [
    "font-heading-set text-lead italic",
    "text-small font-bold uppercase tracking-[0.32em]",
    "font-mono text-body font-medium tracking-tight",
    "text-body font-extrabold tracking-[-0.03em]",
    "font-heading-set text-lead",
    "text-lead font-light lowercase tracking-tight",
  ][i % 6];
  const glyph = [
    null,
    <span className="size-3.5 rotate-45 border-2 border-current" />,
    null,
    <span className="size-4 rounded-pill bg-current" />,
    <span className="flex gap-0.5"><span className="h-4 w-1.5 bg-current" /><span className="h-4 w-1.5 bg-current opacity-60" /></span>,
    <span className="size-4 rounded-pill border-2 border-current" />,
  ][i % 6];
  return (
    <span className={cn("inline-flex items-center gap-2 whitespace-nowrap text-muted transition-colors duration-300 hover:text-fg", style)}>
      {glyph && <span aria-hidden className="inline-flex">{glyph}</span>}{name}
    </span>
  );
}

function SocialProof({ node }: NodeProps) {
  const variant = variantOf(node, "logos");
  const logos = listProp(node, "logos", LOGOS);
  const eyebrow = prop(node, "eyebrow", "Chosen by people who notice the details");

  if (variant === "badges") {
    const badges = entries(node, "badges", [
      ["Editor's pick", "Kinfolk Journal · 2025"], ["Best newcomer", "City Design Awards"],
      ["Certified B Corp", "Independently audited"],
    ]);
    const BadgeIcons = [Award, Star, BadgeCheck];
    return (
      <Section label="Recognition" size="sm">
        <div className="grid items-center gap-8 rounded-lg border border-border bg-surface p-6 md:p-8 lg:grid-cols-[auto_1fr] lg:gap-12">
          <div className="flex items-center gap-5 lg:border-r lg:border-border lg:pr-12">
            <p className="font-heading-set text-h1 tabular-nums">{prop(node, "rating", "4.9")}</p>
            <div className="space-y-1.5">
              <Stars />
              <p className="text-small text-muted">{prop(node, "rating_label", "From 2,400+ verified reviews")}</p>
            </div>
          </div>
          <ul className="grid gap-4 sm:grid-cols-3">
            {badges.map(([title, detail], i) => {
              const Icon = BadgeIcons[i % 3];
              return (
                <li key={i} className="flex items-center gap-3">
                  <span className="grid size-11 shrink-0 place-items-center rounded-pill border border-border bg-bg text-fg"><Icon aria-hidden className="size-5" /></span>
                  <span className="min-w-0">
                    <span className="block text-small font-semibold">{title}</span>
                    {detail && <span className="block text-caption text-muted">{detail}</span>}
                  </span>
                </li>);
            })}
          </ul>
        </div>
      </Section>
    );
  }
  if (variant === "marquee") {
    return (
      <Section label="Trusted by" size="sm" tone="surface" wide>
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:gap-12">
          <p className="max-w-[15rem] shrink-0 text-small font-semibold text-muted">{eyebrow}</p>
          <Marquee className="min-w-0 flex-1 py-2" speed={45}>
            {logos.map((l, i) => <Wordmark key={i} name={l} i={i} />)}
          </Marquee>
        </div>
      </Section>
    );
  }
  return (
    <Section label="Trusted by" size="sm">
      <Eyebrow className="text-center">{eyebrow}</Eyebrow>
      <ul className="mt-8 grid grid-cols-2 border-l border-t border-border sm:grid-cols-3 lg:grid-cols-6">
        {logos.map((l, i) => (
          <li key={i} className="grid min-h-24 place-items-center border-b border-r border-border px-4 py-6 text-center">
            <Wordmark name={l} i={i} />
          </li>))}
      </ul>
    </Section>
  );
}

/* ================================================================== features */
const FEATURES: { title: string; body: string; icon: string; subject: Subject }[] = [
  { title: "Made in small batches", body: "Prepared by hand in quantities small enough to check every single one before it leaves.", icon: "sparkles", subject: "product" },
  { title: "Sourced with intent", body: "A short list of makers and growers we know by name, visit every year and pay fairly.", icon: "leaf", subject: "leaf" },
  { title: "Ready when you are", body: "Order ahead and collect in minutes, or have it with you the same day.", icon: "clock", subject: "cup" },
  { title: "Wrapped to give", body: "Every order leaves beautifully packed, with a handwritten note on request.", icon: "gift", subject: "bag" },
  { title: "Delivered with care", body: "Tracked delivery in plastic-free packaging that arrives exactly as it left us.", icon: "truck", subject: "glass" },
  { title: "Here when you need us", body: "Real people answer every message, usually within the hour.", icon: "heart", subject: "person" },
];

/** Five filled stars, for places where the number is already shown large beside them. */
function Stars({ className }: { className?: string }) {
  return <span aria-hidden className={cn("flex text-accent", className)}>{range(5).map((i) => <Star key={i} className="size-4 fill-current" />)}</span>;
}

function IconTile({ Icon, className }: { Icon: LucideIcon; className?: string }) {
  return (
    <span className={cn("grid size-11 shrink-0 place-items-center rounded-button bg-accent text-accent-fg shadow-sm transition-transform duration-300 ease-brand group-hover:-rotate-6 group-hover:scale-105", className)}>
      <Icon aria-hidden className="size-5" />
    </span>
  );
}

function FeatureCard({ node, index }: NodeProps & { index?: number }) {
  const variant = variantOf(node);
  const seed = prop(node, "title", "") || String(index ?? 0);
  const f = FEATURES[(index ?? hash(seed)) % FEATURES.length];
  const title = prop(node, "title", f.title);
  const body = prop(node, "body", f.body);
  const Icon = iconOf(prop(node, "icon", f.icon), title);
  const tone = hash(title) % 4;

  if (variant === "icon_top") {
    return (
      <article className="group flex h-full flex-col items-center gap-5 rounded-card px-4 py-8 text-center transition-colors duration-300 hover:bg-fg/[0.03]">
        <span className="grid size-16 place-items-center rounded-pill border border-border bg-surface text-fg transition-[transform,background-color,color] duration-300 ease-brand group-hover:-translate-y-1 group-hover:bg-accent group-hover:text-accent-fg">
          <Icon aria-hidden className="size-6" />
        </span>
        <h3 className="font-heading-set text-h4 text-balance">{title}</h3>
        <p className="max-w-xs text-muted text-pretty">{body}</p>
      </article>
    );
  }
  if (variant === "wide") {
    return (
      <article className="group grid h-full overflow-hidden rounded-card border border-border bg-surface transition-[border-color,box-shadow] duration-300 ease-brand hover:border-fg/20 hover:shadow-lg sm:grid-cols-[1.1fr_1fr]">
        <div className="flex flex-col gap-4 p-6 md:p-8">
          <IconTile Icon={Icon} />
          <h3 className="mt-auto pt-6 font-heading-set text-h3 text-balance">{title}</h3>
          <p className="text-muted text-pretty">{body}</p>
        </div>
        <Media ratio="4/3" subject={f.subject} tone={tone} label={title} className="h-full rounded-none sm:!aspect-auto" />
      </article>
    );
  }
  // Standard. Inside a bento, the large tile (data-size=lg) also shows imagery.
  return (
    <FeatureSurface>
      <IconTile Icon={Icon} />
      <div className="space-y-2">
        <h3 className="font-heading-set text-h4 text-balance group-data-[size=lg]/tile:text-h3">{title}</h3>
        <p className="text-muted text-pretty">{body}</p>
      </div>
      <Media ratio="16/10" subject={f.subject} tone={tone} label={title}
        className="mt-auto hidden group-data-[size=lg]/tile:block" />
    </FeatureSurface>
  );
}

/** The standard feature surface: fills its tile, lifts on hover. */
function FeatureSurface({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <article className={cn("group flex h-full flex-col gap-6 rounded-card border border-border bg-surface p-6 text-fg transition-[transform,box-shadow,border-color] duration-300 ease-brand hover:-translate-y-1 hover:border-fg/20 hover:shadow-lg md:p-7", className)}>
      {children}
    </article>
  );
}

/**
 * Bento placement for the nth of `count` tiles on a 4-column desktop grid (2 on tablet): a 2x2
 * opener, a wide tile beside it, two small tiles under that, then rows alternating 1+3 and 3+1.
 * A tile left alone at the end takes the whole row, so the grid never ends with a hole.
 */
function bentoSpan(i: number, count: number): { cls: string; size: "lg" | "wide" | "sm" } {
  if (i === 0) return { cls: "md:col-span-2 lg:row-span-2", size: "lg" };
  if (i === 1) return { cls: "md:col-span-2", size: "wide" };
  const pos = i - 2, rest = count - 2;
  if (pos < 2) return rest === 1 ? { cls: "md:col-span-2", size: "wide" } : { cls: "", size: "sm" };
  const q = pos - 2;
  if ((rest - 2) % 2 === 1 && q === rest - 3) return { cls: "md:col-span-2 lg:col-span-4", size: "wide" };
  const wideFirst = Math.floor(q / 2) % 2 === 1;
  return (q % 2 === 0) === wideFirst ? { cls: "lg:col-span-3", size: "wide" } : { cls: "", size: "sm" };
}

function FeatureBento({ node, children, hasChildren }: NodeProps) {
  const variant = variantOf(node);
  const eyebrow = prop(node, "eyebrow", "Why people stay");
  const title = prop(node, "title", "Small details, done properly.");
  const subtitle = prop(node, "subtitle", "Everything that happens between choosing and enjoying, considered so you never have to think about it.");
  const subject = subjectOf(prop(node, "media", ""), "product");
  const src = imageAt(node, "media")?.url;
  const items = entries(node, "items", FEATURES.map((f) => [f.title, f.body]));
  const item = (i: number) => ({ title: items[i]?.[0] || FEATURES[i].title, body: items[i]?.[1] ?? FEATURES[i].body });

  if (hasChildren) {
    const kids = Children.toArray(children);
    return (
      <Section label={title}>
        <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4 lg:auto-rows-[minmax(14rem,auto)]">
          {kids.map((k, i) => {
            const s = bentoSpan(i, kids.length);
            return <div key={i} data-size={s.size} className={cn("group/tile [&>*]:h-full", s.cls)}>{k}</div>;
          })}
        </div>
      </Section>
    );
  }

  if (variant === "compact") {
    // Split: a sticky heading column beside a tight 2x2 of icon tiles, one of which runs wide.
    return (
      <Section label={title}>
        <div className="grid gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16">
          <div className="lg:sticky lg:top-24 lg:self-start">
            <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} className="mb-0 md:mb-0" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {range(5).map((i) => {
              const Icon = iconOf(FEATURES[i].icon, item(i).title);
              return (
                <article key={i} className={cn("group flex gap-4 rounded-card border border-border bg-surface p-5 transition-[border-color,box-shadow] duration-300 ease-brand hover:border-fg/20 hover:shadow-md",
                  i === 0 ? "flex-col sm:col-span-2 sm:flex-row sm:items-center" : "flex-col")}>
                  <IconTile Icon={Icon} />
                  <div className="space-y-1.5">
                    <h3 className="font-semibold">{item(i).title}</h3>
                    <p className="text-small text-muted text-pretty">{item(i).body}</p>
                  </div>
                </article>);
            })}
          </div>
        </div>
      </Section>
    );
  }

  const premium = variant === "premium";
  const tileBase = "group relative flex flex-col overflow-hidden rounded-lg border border-border transition-[transform,box-shadow,border-color] duration-500 ease-brand hover:-translate-y-1 hover:border-fg/20 hover:shadow-lg";
  const tile = cn(tileBase, premium ? "bg-bg" : "bg-surface");
  const Icon = (i: number) => iconOf(FEATURES[i].icon, item(i).title);
  const T = ({ i, className }: { i: number; className?: string }) => (
    <div className={cn("space-y-2", className)}>
      <h3 className="font-heading-set text-h4 text-balance">{item(i).title}</h3>
      <p className="text-muted text-pretty">{item(i).body}</p>
    </div>
  );
  return (
    <Section label={title} tone={premium ? "surface" : "default"} wide={premium}>
      <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} align={premium ? "center" : "start"}
        action={premium ? undefined : <Button variant="link" arrow>{prop(node, "cta", "See how we work")}</Button>} />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4 lg:auto-rows-[minmax(15rem,auto)]">
        {/* A: the large media tile */}
        {premium ? (
          <article className={cn(tile, "min-h-[26rem] md:col-span-2 lg:row-span-2")}>
            <Media ratio="auto" subject={subject} src={src} label={item(0).title} className="!absolute inset-0 h-full rounded-none" />
            <div className="relative mx-4 mb-4 mt-auto rounded-card bg-bg/95 p-6 shadow-lg backdrop-blur md:mx-6 md:mb-6 md:p-7">
              <Badge tone="accent" className="mb-4">{prop(node, "badge", "Signature")}</Badge>
              <h3 className="font-heading-set text-h3 text-balance">{item(0).title}</h3>
              <p className="mt-2 text-muted text-pretty">{item(0).body}</p>
            </div>
          </article>
        ) : (
          <article className={cn(tile, "md:col-span-2 lg:row-span-2")}>
            <div className="flex items-start justify-between gap-4 p-6 md:p-8">
              <div className="space-y-2">
                <h3 className="font-heading-set text-h3 text-balance">{item(0).title}</h3>
                <p className="max-w-md text-muted text-pretty">{item(0).body}</p>
              </div>
              <IconTile Icon={Icon(0)} />
            </div>
            <Media ratio="16/10" subject={subject} src={src} label={item(0).title} className="mt-auto rounded-none md:!aspect-auto md:min-h-72 md:flex-1" />
          </article>
        )}
        {/* B: wide tile with a strip of thumbnails */}
        <article className={cn(tile, "gap-6 p-6 md:col-span-2 md:p-7")}>
          <T i={1} />
          <div className="mt-auto grid grid-cols-3 gap-3">
            {(["leaf", "bag", "cup"] as Subject[]).map((s, k) => <Media key={k} ratio="4/3" subject={s} tone={k + 1} label={`${item(1).title} ${k + 1}`} className="rounded-card" />)}
          </div>
        </article>
        {/* C: proof tile */}
        <article className={cn(premium ? cn(tileBase, "tone-inverse border-transparent") : tile, "justify-between gap-6 p-6 md:p-7")}>
          <Quote aria-hidden className="size-7 text-muted" />
          <div>
            <p className="font-heading-set text-h1 tabular-nums">{prop(node, "stat", "4.9")}</p>
            <Stars className={cn("mt-2", premium && "text-fg")} />
            <p className="mt-2 text-small text-muted">{prop(node, "stat_label", "Average from 2,400+ reviews")}</p>
          </div>
        </article>
        {/* D: icon tile */}
        <article className={cn(tile, "gap-6 p-6 md:p-7")}>
          <IconTile Icon={Icon(2)} />
          <T i={2} className="mt-auto" />
        </article>
        {/* E: icon tile */}
        <article className={cn(tile, "gap-6 p-6 md:p-7")}>
          <IconTile Icon={Icon(3)} />
          <T i={3} className="mt-auto" />
        </article>
        {/* F: wide tile, copy beside media */}
        <article className={cn(tile, "grid sm:grid-cols-[1fr_1fr] lg:col-span-3")}>
          <div className="flex flex-col gap-6 p-6 md:p-7">
            <IconTile Icon={Icon(4)} />
            <T i={4} className="mt-auto" />
          </div>
          <Media ratio="16/10" subject={FEATURES[4].subject} tone={2} label={item(4).title} className="h-full rounded-none sm:!aspect-auto" />
        </article>
      </div>
    </Section>
  );
}

/* ================================================================== product showcase */
function BrowserFrame({ url, children, className }: { url: string; children: ReactNode; className?: string }) {
  return (
    <div className={cn("overflow-hidden rounded-lg border border-border bg-bg shadow-xl ring-1 ring-fg/5", className)}>
      <div className="flex items-center gap-4 border-b border-border bg-surface-alt px-4 py-3">
        <div aria-hidden className="flex gap-1.5">
          <span className="size-3 rounded-pill bg-danger/70" /><span className="size-3 rounded-pill bg-warning/70" /><span className="size-3 rounded-pill bg-success/70" />
        </div>
        <div className="mx-auto flex h-8 w-full max-w-sm min-w-0 items-center justify-center gap-2 rounded-pill bg-bg px-4 text-caption text-muted">
          <Lock aria-hidden className="size-3 shrink-0" /><span className="truncate">{url}</span>
        </div>
        <div aria-hidden className="hidden w-[3.25rem] sm:block" />
      </div>
      {children}
    </div>
  );
}

/** A miniature website: skeleton nav, hero with media, a row of cards. Reads as a real screen. */
function SiteMock({ subject, src, label }: { subject: Subject; src?: string; label: string }) {
  const line = "rounded-pill bg-fg/10";
  return (
    <div className="space-y-6 p-4 sm:p-6 md:p-8">
      <div aria-hidden className="flex items-center gap-4">
        <span className="size-5 rounded-pill bg-fg" /><span className={cn(line, "h-2 w-16")} />
        <span className="ml-auto hidden gap-4 sm:flex">{range(3).map((i) => <span key={i} className={cn(line, "h-2 w-10")} />)}</span>
        <span className="h-6 w-16 rounded-button bg-primary" />
      </div>
      <div className="grid items-center gap-6 sm:grid-cols-2">
        <div aria-hidden className="space-y-3">
          <span className={cn(line, "block h-2 w-20 bg-accent/60")} />
          <span className="block h-4 w-11/12 rounded-sm bg-fg/80" /><span className="block h-4 w-3/4 rounded-sm bg-fg/80" />
          <span className={cn(line, "block h-2 w-full")} /><span className={cn(line, "block h-2 w-5/6")} />
          <span className="mt-2 flex gap-2"><span className="h-7 w-20 rounded-button bg-primary" /><span className="h-7 w-16 rounded-button border border-border" /></span>
        </div>
        <Media ratio="4/3" subject={subject} src={src} label={label} className="rounded-card" />
      </div>
      <div className="hidden grid-cols-3 gap-4 sm:grid">
        {(["cup", "leaf", "bag"] as Subject[]).map((s, i) => (
          <div key={i} className="space-y-2">
            <Media ratio="1/1" subject={s} tone={i + 1} label={`${label} detail ${i + 1}`} className="rounded-card" />
            <span aria-hidden className={cn(line, "block h-2 w-2/3")} />
          </div>))}
      </div>
    </div>
  );
}

/** A phone: bezel, dynamic island, side keys, and a miniature app screen. */
function Phone({ subject, src, label, tone = 0, className }: { subject: Subject; src?: string; label: string; tone?: number; className?: string }) {
  const line = "rounded-pill bg-fg/10";
  return (
    // Devices are drawn as physical objects, so their corner radius is fixed rather than themed.
    <div className={cn("relative w-full rounded-[2.6rem] bg-fg p-2 shadow-xl ring-1 ring-fg/20", className)}>
      <span aria-hidden className="absolute -left-[3px] top-24 h-10 w-[3px] rounded-l-sm bg-fg" />
      <span aria-hidden className="absolute -right-[3px] top-32 h-16 w-[3px] rounded-r-sm bg-fg" />
      <div className="relative flex aspect-[9/19] flex-col overflow-hidden rounded-[2.1rem] bg-bg">
        <span aria-hidden className="absolute left-1/2 top-2 z-10 h-5 w-20 -translate-x-1/2 rounded-pill bg-fg" />
        <div aria-hidden className="flex items-center justify-between px-6 pb-2 pt-3">
          <span className={cn(line, "h-1.5 w-6 bg-fg/40")} /><span className={cn(line, "h-1.5 w-8 bg-fg/40")} />
        </div>
        <div className="flex flex-1 flex-col gap-3 px-3 pb-3 pt-4">
          <div aria-hidden className="flex items-center justify-between px-1">
            <span className="block h-3 w-20 rounded-sm bg-fg/80" /><span className="size-6 rounded-pill bg-surface-alt" />
          </div>
          <Media ratio="4/5" subject={subject} src={src} tone={tone} label={label} className="rounded-card" />
          {range(2).map((i) => (
            <div key={i} aria-hidden className="flex items-center gap-2.5 rounded-card bg-surface p-2">
              <span className="size-8 shrink-0 rounded-sm bg-media-a/60" />
              <span className="flex-1 space-y-1.5"><span className={cn(line, "block h-1.5 w-3/4")} /><span className={cn(line, "block h-1.5 w-1/2")} /></span>
            </div>))}
          <span aria-hidden className="mt-auto block h-8 rounded-button bg-primary" />
        </div>
      </div>
    </div>
  );
}

function ShowcasePoint({ Icon, title, body, align = "start" }: { Icon: LucideIcon; title: string; body: string; align?: "start" | "end" }) {
  return (
    <li className={cn("flex gap-4", align === "end" && "lg:flex-row-reverse lg:text-right")}>
      <span className="grid size-10 shrink-0 place-items-center rounded-pill border border-border bg-surface text-fg"><Icon aria-hidden className="size-4" /></span>
      <div className="space-y-1">
        <h3 className="font-semibold">{title}</h3>
        <p className="text-small text-muted text-pretty">{body}</p>
      </div>
    </li>
  );
}

function ProductShowcase({ node }: NodeProps) {
  const variant = variantOf(node);
  const subject = subjectOf(prop(node, "media", ""), variant === "standard" ? "product" : "cup");
  const src = imageAt(node, "media")?.url;
  const label = prop(node, "media_label", "A closer look");
  const eyebrow = prop(node, "eyebrow", "A closer look");
  const title = prop(node, "title", "Everything you love, in one place.");
  const subtitle = prop(node, "subtitle", "Browse the full range, save your favourites and reorder in two taps. Built to feel as considered as what we make.");
  const points = entries(node, "points", [
    ["Order ahead", "Choose a time and skip the wait."], ["Saved favourites", "Your usuals, one tap away."],
    ["Live updates", "Know exactly when it is ready."], ["Rewards built in", "Every order counts toward the next."],
    ["Gift anything", "Send a treat with a personal note."], ["Secure checkout", "Card and wallet payments, encrypted."],
  ]);
  const icons = [Clock, Heart, Zap, Award, Gift, ShieldCheck];
  const pt = (i: number) => ({ title: points[i]?.[0] ?? "", body: points[i]?.[1] ?? "" });

  if (variant === "browser_frame") {
    return (
      <Section label={title} tone="surface" wide className="overflow-hidden">
        <div className="grid items-center gap-12 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16">
          <div>
            <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} className="mb-8 md:mb-10" />
            <ul className="space-y-6">{range(Math.min(3, points.length)).map((i) => <ShowcasePoint key={i} Icon={icons[i]} {...pt(i)} />)}</ul>
            <Button className="mt-10" arrow>{prop(node, "cta", "Take a look")}</Button>
          </div>
          <div className="relative">
            <div aria-hidden className="absolute -inset-8 rounded-lg bg-accent/10 blur-2xl" />
            <BrowserFrame url={prop(node, "url", "yourstudio.com")} className="relative">
              <SiteMock subject={subject} src={src} label={label} />
            </BrowserFrame>
          </div>
        </div>
      </Section>
    );
  }
  if (variant === "device_frame") {
    const side = (from: number, align: "start" | "end") => (
      <ul className="space-y-10">{range(3).map((k) => from + k < points.length && (
        <ShowcasePoint key={k} Icon={icons[(from + k) % 6]} align={align} {...pt(from + k)} />))}</ul>
    );
    return (
      <Section label={title} className="relative isolate overflow-hidden">
        <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} align="center" />
        <div className="grid items-center gap-12 lg:grid-cols-[1fr_auto_1fr] lg:gap-16">
          <div className="order-2 lg:order-1">{side(0, "end")}</div>
          <div className="relative order-1 mx-auto w-64 sm:w-72 lg:order-2">
            <div aria-hidden className="absolute left-1/2 top-1/2 -z-10 size-[130%] -translate-x-1/2 -translate-y-1/2 rounded-pill"
              style={{ background: "radial-gradient(closest-side, color-mix(in srgb, var(--color-accent) 22%, transparent), transparent)" }} />
            <Phone subject={subject} src={src} label={label} />
          </div>
          <div className="order-3">{side(3, "start")}</div>
        </div>
      </Section>
    );
  }
  // Standard: a large image on a tinted stage, with solid callout panels pinned to its corners.
  return (
    <Section label={title} wide>
      <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} align="center" />
      <div className="relative rounded-lg bg-surface-alt p-3 sm:p-6 md:p-10">
        <Media ratio="16/9" subject={subject} src={src} label={label} className="shadow-xl" />
        <div className="absolute left-6 top-6 hidden max-w-sm rounded-card bg-bg/95 p-5 shadow-lg backdrop-blur md:block lg:left-16 lg:top-16">
          <p className="text-caption font-semibold uppercase tracking-[0.18em] text-muted">{prop(node, "callout_label", "This week")}</p>
          <p className="mt-1 font-heading-set text-h4 text-balance">{prop(node, "callout", "New arrivals, freshly in")}</p>
        </div>
        <div className="absolute bottom-6 right-6 hidden items-center gap-3 rounded-pill bg-bg/95 py-2 pl-2 pr-5 shadow-lg backdrop-blur md:flex lg:bottom-16 lg:right-16">
          <span className="grid size-9 place-items-center rounded-pill bg-success text-bg"><Check aria-hidden className="size-4" /></span>
          <span className="text-small font-semibold">{prop(node, "badge", "Ready in 8 minutes")}</span>
        </div>
      </div>
      <ul className="mt-12 grid gap-8 sm:grid-cols-3">{range(Math.min(3, points.length)).map((i) => <ShowcasePoint key={i} Icon={icons[i]} {...pt(i)} />)}</ul>
    </Section>
  );
}

/* ================================================================== metrics */
const METRICS = [
  ["12", "Years doing one thing well"], ["4.9", "Average rating from 2.4k reviews"],
  ["38k", "Orders delivered last year"], ["96%", "Of customers come back within 90 days"],
];

function Metrics({ node, columns }: NodeProps) {
  const variant = variantOf(node);
  const items = entries(node, "items", METRICS);
  const eyebrow = prop(node, "eyebrow", "In numbers");
  const title = prop(node, "title", "Quietly, consistently good.");
  const subtitle = prop(node, "subtitle", "We measure ourselves by the people who come back. Here is how that looks so far.");

  if (variant === "inline") {
    return (
      <Section label={title} size="sm" tone="surface">
        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] lg:items-center lg:gap-12">
          <p className="font-heading-set text-h4 text-balance">{title}</p>
          <dl className="grid grid-cols-2 gap-y-6 md:grid-cols-4 md:divide-x md:divide-border">
            {items.map(([v, l], i) => (
              <div key={i} className="flex flex-col gap-1 md:px-6 md:first:pl-0">
                <dt className="order-2 text-small text-muted">{l}</dt>
                <dd className="font-heading-set text-h2 tabular-nums">{v}</dd>
              </div>))}
          </dl>
        </div>
      </Section>
    );
  }
  if (variant === "cards") {
    const icons = [Clock, Star, Package, Heart];
    return (
      <Section label={title}>
        <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} align="center" />
        <dl className={cn(colsGrid, "gap-4")} style={colsVar(columns, Math.min(4, items.length))}>
          {items.map(([v, l], i) => {
            const Icon = icons[i % 4];
            return (
              <div key={i} className={cn("group flex min-h-56 flex-col rounded-card border p-6 transition-[transform,box-shadow] duration-300 ease-brand hover:-translate-y-1 hover:shadow-lg md:p-7",
                i === 0 ? "tone-accent border-transparent" : "border-border bg-surface")}>
                <Icon aria-hidden className={cn("size-5", i === 0 ? "text-fg" : "text-muted")} />
                <dt className={cn("order-last mt-2 text-small", i === 0 ? "text-fg" : "text-muted")}>{l}</dt>
                <dd className="mt-auto pt-8 font-heading-set text-h1 tabular-nums">{v}</dd>
              </div>);
          })}
        </dl>
      </Section>
    );
  }
  return (
    <Section label={title}>
      <div className="grid gap-12 lg:grid-cols-[minmax(0,4fr)_minmax(0,8fr)] lg:gap-16">
        <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} className="mb-0 md:mb-0" />
        <dl className="grid grid-cols-1 gap-x-10 gap-y-10 sm:grid-cols-2">
          {items.map(([v, l], i) => (
            <div key={i} className="flex flex-col border-t border-fg pt-6">
              <dt className="order-last mt-3 max-w-[16rem] text-muted">{l}</dt>
              <dd className="font-heading-set text-display tabular-nums">{v}</dd>
            </div>))}
        </dl>
      </div>
    </Section>
  );
}

/* ================================================================== testimonials */
const QUOTES = [
  ["We came for one thing and left with a new favourite. The attention to detail is on another level.", "Maya Okafor", "Regular since 2021"],
  ["Everything arrived beautifully packed and exactly when they said it would.", "Daniel Reyes", "Verified customer"],
  ["The kind of place you recommend to friends before you have even left.", "Priya Nair", "Local guide"],
  ["Thoughtful from the first hello to the final follow-up. It shows in every detail.", "Tom Becker", "Studio client"],
  ["Consistently excellent. It has quietly become part of our weekly routine.", "Ana Lima", "Member"],
  ["Honest prices and genuinely warm people. Rare and completely worth it.", "Sam Whitfield", "Returning customer"],
];

function QuoteCard({ q, featured, className }: { q: string[]; featured?: boolean; className?: string }) {
  const [text, name, role] = q;
  return (
    <figure className={cn("flex h-full flex-col gap-6 rounded-card border p-6 transition-[border-color,box-shadow] duration-300 ease-brand hover:shadow-lg md:p-8",
      featured ? "tone-inverse border-transparent" : "border-border bg-surface hover:border-fg/20", className)}>
      {featured ? <Stars className="text-fg" /> : <Rating value={5} />}
      <blockquote className={cn("text-pretty", featured ? "font-heading-set text-h3" : "text-lead")}>&ldquo;{text}&rdquo;</blockquote>
      {name && (
        <figcaption className="mt-auto flex items-center gap-3 pt-2">
          <Avatar name={name} className={cn(featured && "bg-surface-alt")} />
          <span className="min-w-0">
            <span className="block font-semibold">{name}</span>
            {role && <span className="block text-small text-muted">{role}</span>}
          </span>
        </figcaption>)}
    </figure>
  );
}

function Testimonials({ node, columns }: NodeProps) {
  const variant = variantOf(node, "grid");
  const quotes = entries(node, "quotes", QUOTES);
  const eyebrow = prop(node, "eyebrow", "Kind words");
  const title = prop(node, "title", "Loved by the people who matter most.");
  const subtitle = prop(node, "subtitle", "Unedited notes from customers, regulars and the occasional first-timer.");

  if (variant === "carousel") {
    return (
      <Section label={title} tone="surface" className="overflow-hidden">
        <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} />
        <Carousel label={title}>
          {quotes.map((q, i) => (
            <div key={i} className="h-full w-[82vw] max-w-[26rem] sm:w-[24rem]">
              <figure className="flex h-full flex-col gap-8 rounded-card border border-border bg-bg p-6 md:p-8">
                <Quote aria-hidden className="size-8 text-accent" />
                <blockquote className="font-heading-set text-h4 text-pretty">{q[0]}</blockquote>
                <figcaption className="mt-auto flex items-center gap-3 border-t border-border pt-6">
                  <Avatar name={q[1] || "Guest"} />
                  <span className="min-w-0 flex-1">
                    <span className="block font-semibold">{q[1]}</span>
                    <span className="block text-small text-muted">{q[2]}</span>
                  </span>
                </figcaption>
              </figure>
            </div>))}
        </Carousel>
      </Section>
    );
  }
  if (variant === "marquee") {
    const half = Math.ceil(quotes.length / 2);
    const row = (list: string[][]) => list.map((q, i) => (
      <QuoteCard key={i} q={q} className="w-[20rem] shrink-0 whitespace-normal md:w-[24rem]" />));
    return (
      <Section label={title} wide className="overflow-hidden">
        <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} align="center" />
        <div className="-mx-4 space-y-6 sm:-mx-10">
          <Marquee speed={60} className="[&>div]:items-stretch [&>div]:gap-6 [&>div]:pr-6">{row(quotes.slice(0, half))}</Marquee>
          <Marquee speed={70} className="[&>div]:items-stretch [&>div]:gap-6 [&>div]:pr-6 [&>div]:[animation-direction:reverse]">{row(quotes.slice(half))}</Marquee>
        </div>
      </Section>
    );
  }
  // Grid: a featured quote across two columns, then the rest.
  const cols = columns ?? 3;
  return (
    <Section label={title}>
      <SectionHeader eyebrow={eyebrow} title={title} body={subtitle}
        action={<div className="flex items-center gap-3"><Rating value={4.9} /><span className="text-small text-muted">{prop(node, "rating_label", "2,400+ reviews")}</span></div>} />
      <div className={colsGrid} style={colsVar(cols, 3)}>
        {quotes.slice(0, 5).map((q, i) => (
          <QuoteCard key={i} q={q} featured={i === 0} className={cn(i === 0 && cols > 1 && "sm:col-span-2")} />))}
      </div>
    </Section>
  );
}

/* ================================================================== pricing */
const PLANS = [
  ["Essential", "$12", "The everyday favourite, at its simplest.",
    "The core offer every month;Member pricing on extras;Pause or cancel anytime"],
  ["Signature", "$29", "Our most loved plan, with a little more.",
    "Everything in Essential;Early access to new releases;Free delivery on every order;A dedicated point of contact"],
  ["Complete", "$59", "For those who want it all, done for them.",
    "Everything in Signature;Bespoke requests each quarter;Invitations to private events;Priority booking"],
];

/** "$29" -> "$23" at the yearly discount; non-numeric prices stay as written. */
const discounted = (price: string, pct: number) => {
  const m = price.match(/^(\D*)(\d+(?:\.\d+)?)(.*)$/);
  return m ? `${m[1]}${Math.round(Number(m[2]) * (1 - pct / 100))}${m[3]}` : price;
};

function PricingTable({ node, columns }: NodeProps) {
  const variant = variantOf(node);
  const [yearly, setYearly] = useState(false);
  const names = listProp(node, "plans", PLANS.map((p) => p[0]));
  const prices = listProp(node, "prices", PLANS.map((p) => p[1]));
  const period = prop(node, "period", "/month");
  const pct = Number.parseInt(prop(node, "yearly_discount", "20"), 10) || 20;
  const eyebrow = prop(node, "eyebrow", "Membership");
  const title = prop(node, "title", "Choose the way you want to join us.");
  const subtitle = prop(node, "subtitle", "Simple plans with no fine print. Switch or pause whenever life changes.");
  const featured = Math.min(1, names.length - 1);
  const highlight = variant !== "standard";
  const toggle = variant === "toggle";

  const plans = names.map((name, i) => {
    const d = PLANS[i % PLANS.length];
    const base = prices[i] ?? d[1];
    return { name, base, price: toggle && yearly ? discounted(base, pct) : base, blurb: d[2], features: d[3].split(";") };
  });

  const card = (p: (typeof plans)[number], i: number) => {
    const hot = highlight && i === featured;
    return (
      <article key={i} className={cn("relative flex flex-col rounded-card border p-6 [&>*]:shrink-0 transition-[transform,box-shadow,border-color] duration-300 ease-brand md:p-8",
        !hot && "border-border hover:-translate-y-1 hover:border-fg/20 hover:shadow-lg",
        !hot && (toggle ? "bg-bg" : "bg-surface"),
        hot && !toggle && "tone-inverse border-transparent shadow-xl lg:-my-6 lg:py-12",
        hot && toggle && "border-primary bg-bg shadow-xl ring-1 ring-primary")}>
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-heading-set text-h4">{p.name}</h3>
          {hot && <Badge tone="accent"><Sparkles aria-hidden className="size-3" />{prop(node, "badge", "Most popular")}</Badge>}
        </div>
        <p className="mt-2 text-small text-muted">{p.blurb}</p>
        <p className="mt-8 flex items-baseline gap-1.5">
          <span className="font-heading-set text-h1 tabular-nums">{p.price}</span>
          <span className="text-muted">{period}</span>
        </p>
        <p className="mt-1 min-h-6 text-small text-muted">
          {toggle ? (yearly ? `Billed yearly · save ${pct}%` : "Billed monthly") : prop(node, "billing_note", "Billed monthly · no commitment")}
        </p>
        <Button className="mt-8 w-full" variant={hot ? "primary" : "secondary"} arrow={hot}>
          {prop(node, "cta", "Choose")} {p.name}
        </Button>
        <ul className="mt-8 space-y-3 border-t border-border pt-8">
          {p.features.map((f) => (
            <li key={f} className="flex items-start gap-3 text-small">
              <span className={cn("mt-0.5 grid size-5 shrink-0 place-items-center rounded-pill", hot ? "bg-primary text-primary-fg" : "bg-surface-alt text-fg")}>
                <Check aria-hidden className="size-3" strokeWidth={3} />
              </span>{f}
            </li>))}
        </ul>
      </article>
    );
  };

  return (
    <Section label={title} tone={toggle ? "surface" : "default"}>
      <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} align={variant === "standard" ? "start" : "center"}
        action={variant === "standard" ? <p className="flex items-center gap-2 text-small text-muted"><ShieldCheck aria-hidden className="size-4" />{prop(node, "guarantee", "30-day happiness guarantee")}</p> : undefined} />
      {toggle && (
        <div className="-mt-4 mb-12 flex justify-center">
          <ToggleGroup.Root type="single" value={yearly ? "yearly" : "monthly"} onValueChange={(v) => v && setYearly(v === "yearly")}
            aria-label="Billing period" className="inline-flex items-center gap-1 rounded-pill border border-border bg-bg p-1 shadow-sm">
            {["monthly", "yearly"].map((v) => (
              <ToggleGroup.Item key={v} value={v}
                className="inline-flex h-11 items-center gap-2 rounded-pill px-5 text-small font-semibold text-muted transition-[background-color,color,transform] duration-300 ease-brand hover:text-fg active:scale-[0.97] data-[state=on]:bg-primary data-[state=on]:text-primary-fg">
                {v === "monthly" ? prop(node, "monthly_label", "Monthly") : prop(node, "yearly_label", "Yearly")}
                {v === "yearly" && <span className="rounded-pill bg-accent px-2 py-0.5 text-caption text-accent-fg">−{pct}%</span>}
              </ToggleGroup.Item>))}
          </ToggleGroup.Root>
        </div>)}
      <div className={cn(colsGrid, "items-stretch sm:grid-cols-1 md:grid-cols-[repeat(var(--cols),minmax(0,1fr))]", highlight && "lg:gap-4")}
        style={colsVar(columns, Math.min(3, plans.length))}>
        {plans.map(card)}
      </div>
      <p className="mt-12 text-center text-small text-muted">{prop(node, "note", "Prices include tax. Change or pause your plan at any time.")}</p>
    </Section>
  );
}

/* ================================================================== CTA */
function CTAButtons({ node, center }: NodeProps & { center?: boolean }) {
  return (
    <div className={cn("flex flex-wrap gap-3", center && "justify-center")}>
      <Button size="lg" arrow>{prop(node, "primary_cta", "Start your order")}</Button>
      <Button size="lg" variant="secondary">{prop(node, "secondary_cta", "Talk to us")}</Button>
    </div>
  );
}

function CTA(props: NodeProps) {
  const { node } = props;
  const variant = variantOf(node);
  const headline = prop(node, "headline", "Your next favourite is waiting.");
  const body = prop(node, "body", "Visit us, order ahead or have it delivered. However you choose, it is made with the same care.");
  const eyebrow = prop(node, "eyebrow", "Ready when you are");
  const points = listProp(node, "points", ["Free delivery over $50", "Reply within a day", "Cancel anytime"]);

  if (variant === "banner") {
    return (
      <Section label={headline} tone="inverse" size="sm">
        <div className="flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="max-w-2xl space-y-2">
            <h2 className="font-heading-set text-h3 text-balance">{headline}</h2>
            <p className="text-muted text-pretty">{body}</p>
          </div>
          <div className="shrink-0"><CTAButtons {...props} /></div>
        </div>
      </Section>
    );
  }
  if (variant === "card") {
    const subject = subjectOf(prop(node, "media", ""), "bag");
    return (
      <Section label={headline}>
        <div className="tone-accent grid overflow-hidden rounded-lg shadow-xl lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
          <div className="flex flex-col gap-6 p-8 md:p-12 lg:p-16">
            {/* Muted copy on an accent fill can fall under AA (espresso: 4.3:1), so it stays full strength. */}
            <Eyebrow className="text-fg">{eyebrow}</Eyebrow>
            <h2 className="font-heading-set text-h2 text-balance">{headline}</h2>
            <p className="max-w-xl text-lead text-pretty">{body}</p>
            <div className="mt-2"><CTAButtons {...props} /></div>
          </div>
          <Media ratio="16/10" subject={subject} src={imageAt(node, "media")?.url} tone={1} label={prop(node, "media_label", "A glimpse of what is waiting")}
            className="h-full rounded-none lg:!aspect-auto lg:min-h-96" />
        </div>
      </Section>
    );
  }
  if (variant === "gradient") {
    return (
      <Section label={headline} tone="inverse" size="lg" className="relative isolate overflow-hidden">
        <div aria-hidden className="absolute inset-0 -z-10"
          style={{ background: "radial-gradient(50% 70% at 12% 0%, color-mix(in srgb, var(--color-accent) 45%, transparent), transparent 70%), radial-gradient(45% 60% at 92% 100%, color-mix(in srgb, var(--color-media-a) 35%, transparent), transparent 70%)" }} />
        <div aria-hidden className="absolute inset-0 -z-10 opacity-[0.07] [background-image:linear-gradient(currentColor_1px,transparent_1px),linear-gradient(90deg,currentColor_1px,transparent_1px)] [background-size:64px_64px] [mask-image:radial-gradient(60%_60%_at_50%_50%,black,transparent)]" />
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 text-center">
          <Badge tone="outline" className="px-3"><Sparkles aria-hidden className="size-3" />{eyebrow}</Badge>
          <h2 className="font-heading-set text-display text-balance">{headline}</h2>
          <p className="max-w-xl text-lead text-muted text-pretty">{body}</p>
          <div className="mt-4"><CTAButtons {...props} center /></div>
        </div>
      </Section>
    );
  }
  return (
    <Section label={headline} tone="surface" size="lg">
      <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 text-center">
        <Eyebrow>{eyebrow}</Eyebrow>
        <h2 className="font-heading-set text-h1 text-balance">{headline}</h2>
        <p className="max-w-xl text-lead text-muted text-pretty">{body}</p>
        <div className="mt-4"><CTAButtons {...props} center /></div>
        <ul className="mt-4 flex flex-wrap justify-center gap-x-6 gap-y-2 text-small text-muted">
          {points.map((p) => <li key={p} className="flex items-center gap-2"><Check aria-hidden className="size-4 text-success" />{p}</li>)}
        </ul>
      </div>
    </Section>
  );
}

/* ================================================================== CTA split */
function CTASplit(props: NodeProps) {
  const { node } = props;
  const variant = variantOf(node, "media");
  const headline = prop(node, "headline", "Come and see it for yourself.");
  const body = prop(node, "body", "Drop by, book a time that suits you, or start online. We will take it from there, at your pace.");

  if (variant === "offers") {
    const offers = entries(node, "offers", [
      ["In person", "Visit us", "Stop by any day of the week to see everything up close and talk it through with the team.", "Plan a visit"],
      ["Online", "Order ahead", "The full range is available to order, with tracked delivery in two to three days.", "Start an order"],
    ]);
    return (
      <Section label={headline}>
        <SectionHeader title={headline} body={body} align="center" />
        <div className="grid gap-4 md:grid-cols-2">
          {offers.slice(0, 2).map(([tag, title, text, cta], i) => (
            <article key={i} className={cn("group flex min-h-80 flex-col gap-5 rounded-lg border p-8 transition-[transform,box-shadow] duration-300 ease-brand hover:-translate-y-1 hover:shadow-xl md:p-10",
              i === 1 ? "tone-inverse border-transparent" : "border-border bg-surface")}>
              <div className="flex items-center justify-between">
                <Eyebrow>{tag}</Eyebrow>
                <span className="grid size-11 place-items-center rounded-pill border border-border transition-transform duration-300 ease-brand group-hover:rotate-45">
                  <ArrowUpRight aria-hidden className="size-5" />
                </span>
              </div>
              <h3 className="mt-auto font-heading-set text-h2 text-balance">{title}</h3>
              {text && <p className="max-w-md text-muted text-pretty">{text}</p>}
              {cta && <Button variant={i === 1 ? "primary" : "secondary"} className="self-start" arrow>{cta}</Button>}
            </article>))}
        </div>
      </Section>
    );
  }
  const subject = subjectOf(prop(node, "media", ""), "space");
  return (
    <Section label={headline}>
      <div className="grid overflow-hidden rounded-lg border border-border bg-surface lg:grid-cols-2">
        <div className="flex flex-col justify-center gap-6 p-8 md:p-12 lg:p-16">
          <Eyebrow>{prop(node, "eyebrow", "Visit or order")}</Eyebrow>
          <h2 className="font-heading-set text-h2 text-balance">{headline}</h2>
          <p className="text-lead text-muted text-pretty">{body}</p>
          <div className="mt-2"><CTAButtons {...props} /></div>
          <p className="flex items-center gap-2 text-small text-muted"><MapPin aria-hidden className="size-4" />{prop(node, "note", "Open every day · Delivery across the city")}</p>
        </div>
        <div className="relative p-3 lg:p-4 lg:pl-0">
          <Media ratio="4/3" subject={subject} src={imageAt(node, "media")?.url} tone={2} label={prop(node, "media_label", "Inside the space")} className="h-full lg:!aspect-auto lg:min-h-[28rem]" />
          <div className="absolute bottom-8 left-8 flex items-center gap-3 rounded-card bg-bg/95 p-3 pr-5 shadow-lg backdrop-blur">
            <span className="grid size-10 place-items-center rounded-pill bg-accent text-accent-fg"><CalendarCheck aria-hidden className="size-5" /></span>
            <span>
              <span className="block text-caption text-muted">{prop(node, "badge_label", "Next opening")}</span>
              <span className="block text-small font-semibold">{prop(node, "badge", "Today, from 2pm")}</span>
            </span>
          </div>
        </div>
      </div>
    </Section>
  );
}

/* ================================================================== integrations */
/** Invented names: fallback copy must never imply a real partnership on a generated site. */
const INTEGRATIONS = [
  ["Paywell", "Payments", "Cards and wallets"], ["Tillbox", "Payments", "In-person checkout"], ["Laterpay", "Payments", "Pay later options"],
  ["Shopline", "Sales", "Storefront sync"], ["Mapleaf", "Sales", "Maps and reviews"], ["Stallhouse", "Sales", "Marketplace listings"],
  ["Postmark & Co", "Marketing", "Newsletters"], ["Loop Mail", "Marketing", "Lifecycle email"], ["Bookwise", "Bookings", "Appointments"],
  ["Daybook", "Bookings", "Two-way availability"], ["Ledgerly", "Operations", "Accounting"], ["Huddle", "Operations", "Team alerts"],
];

function AppMark({ name, i, className }: { name: string; i: number; className?: string }) {
  const tone = ["bg-primary text-primary-fg", "bg-accent text-accent-fg", "bg-surface-alt text-fg", "bg-fg text-bg"][i % 4];
  return (
    <span aria-hidden className={cn("grid size-12 shrink-0 place-items-center rounded-button font-heading-set text-h4 shadow-sm", tone, className)}>
      {name.charAt(0)}
    </span>
  );
}

function IntegrationsGrid({ node, columns }: NodeProps) {
  const variant = variantOf(node, "grid");
  const items = entries(node, "items", INTEGRATIONS);
  const eyebrow = prop(node, "eyebrow", "Integrations");
  const title = prop(node, "title", "Works with the tools you already use.");
  const subtitle = prop(node, "subtitle", "Connect payments, bookings and bookkeeping in a few clicks. No developers, no spreadsheets.");
  const categories = [...new Set(items.map((it) => it[1]).filter(Boolean))];
  const [filter, setFilter] = useState("all");

  if (variant === "grouped") {
    return (
      <Section label={title} tone="surface">
        <SectionHeader eyebrow={eyebrow} title={title} body={subtitle}
          action={<Button variant="secondary" arrow>{prop(node, "cta", "Browse all integrations")}</Button>} />
        <div className="grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-[repeat(var(--cols),minmax(0,1fr))]" style={colsVar(columns, Math.min(3, categories.length))}>
          {categories.map((c) => (
            <div key={c}>
              <h3 className="flex items-center justify-between border-b border-fg pb-3 font-semibold">
                {c}<span className="text-small font-normal text-muted tabular-nums">{items.filter((it) => it[1] === c).length}</span>
              </h3>
              <ul className="divide-y divide-border">
                {items.map((it, i) => it[1] === c && (
                  <li key={i} className="group flex items-center gap-4 py-4">
                    <AppMark name={it[0]} i={i} className="size-10 text-body" />
                    <span className="min-w-0 flex-1">
                      <span className="block font-semibold">{it[0]}</span>
                      {it[2] && <span className="block text-small text-muted">{it[2]}</span>}
                    </span>
                    <ArrowUpRight aria-hidden className="size-4 text-muted transition-transform duration-300 ease-brand group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-fg" />
                  </li>))}
              </ul>
            </div>))}
        </div>
      </Section>
    );
  }
  const shown = items.map((it, i) => ({ it, i })).filter(({ it }) => filter === "all" || it[1] === filter);
  return (
    <Section label={title}>
      <SectionHeader eyebrow={eyebrow} title={title} body={subtitle} align="center" />
      <ToggleGroup.Root type="single" value={filter} onValueChange={(v) => v && setFilter(v)} aria-label="Filter integrations by category"
        className="mb-10 flex flex-wrap justify-center gap-2">
        {["all", ...categories].map((c) => (
          <ToggleGroup.Item key={c} value={c}
            className="h-11 rounded-pill border border-border px-5 text-small font-semibold text-fg transition-[background-color,color,border-color,transform] duration-200 ease-brand hover:border-fg/40 active:scale-[0.97] data-[state=on]:border-primary data-[state=on]:bg-primary data-[state=on]:text-primary-fg">
            {c === "all" ? prop(node, "all_label", "All") : c}
          </ToggleGroup.Item>))}
      </ToggleGroup.Root>
      <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-[repeat(var(--cols),minmax(0,1fr))]" style={colsVar(columns, 4)} aria-live="polite">
        {shown.map(({ it, i }) => (
          <li key={it[0]} className="group relative flex flex-col gap-5 rounded-card border border-border bg-surface p-5 transition-[transform,box-shadow,border-color] duration-300 ease-brand hover:-translate-y-1 hover:border-fg/20 hover:shadow-lg">
            <div className="flex items-start justify-between">
              <AppMark name={it[0]} i={i} />
              {it[1] && <span className="rounded-pill border border-border px-2.5 py-1 text-caption font-medium text-muted">{it[1]}</span>}
            </div>
            <div>
              <h3 className="font-semibold">{it[0]}</h3>
              {it[2] && <p className="mt-1 text-small text-muted">{it[2]}</p>}
            </div>
          </li>))}
      </ul>
      <div className="mt-10 flex justify-center"><Button variant="link" arrow>{prop(node, "cta", "Browse all integrations")}</Button></div>
    </Section>
  );
}

/* ================================================================== app download */
function StoreButton({ store, className }: { store: "apple" | "google"; className?: string }) {
  const apple = store === "apple";
  return (
    <button type="button" aria-label={apple ? "Download on the App Store" : "Get it on Google Play"}
      className={cn("group/store inline-flex h-14 items-center gap-3 rounded-button bg-primary px-5 text-left text-primary-fg shadow-sm transition-[transform,box-shadow] duration-200 ease-brand hover:-translate-y-0.5 hover:shadow-md active:scale-[0.97]", className)}>
      {apple ? <Apple aria-hidden className="size-6" /> : <Play aria-hidden className="size-6 fill-current" />}
      <span className="leading-tight">
        <span className="block text-caption">{apple ? "Download on the" : "Get it on"}</span>
        <span className="block text-body font-semibold">{apple ? "App Store" : "Google Play"}</span>
      </span>
    </button>
  );
}

/** A deterministic QR-like pattern: decorative, it signals "scan me" without pretending to encode. */
function QRMark() {
  const cells = range(121).map((k) => {
    const x = k % 11, y = Math.floor(k / 11);
    const finder = (x < 3 && y < 3) || (x > 7 && y < 3) || (x < 3 && y > 7);
    return finder ? !(x % 10 === 1 && y % 10 === 1) && !(x === 9 && y === 1) : (x * 7 + y * 13 + x * y) % 3 === 0;
  });
  return (
    <span aria-hidden className="grid size-20 shrink-0 grid-cols-11 gap-px rounded-sm bg-bg p-1.5">
      {cells.map((on, k) => <span key={k} className={on ? "bg-fg" : ""} />)}
    </span>
  );
}

function AppDownload({ node }: NodeProps) {
  const variant = variantOf(node);
  const subject = subjectOf(prop(node, "media", ""), "cup");
  const src = imageAt(node, "media")?.url;
  const label = prop(node, "media_label", "The app on a phone");
  const headline = prop(node, "headline", "Everything we do, now in your pocket.");
  const body = prop(node, "body", "Order ahead, track deliveries and collect rewards with every visit. Available on iPhone and Android.");
  const points = listProp(node, "points", ["Order ahead in seconds", "Members-only releases", "Rewards on every order"]);

  if (variant === "banner") {
    return (
      <Section label={headline} tone="inverse" size="none" className="overflow-hidden">
        <div className="grid items-center gap-10 pt-12 md:grid-cols-[minmax(0,1fr)_16rem] md:gap-16 md:pt-0 lg:grid-cols-[minmax(0,1fr)_20rem]">
          <div className="space-y-6 md:py-16">
            <h2 className="font-heading-set text-h2 text-balance">{headline}</h2>
            <p className="max-w-xl text-muted text-pretty">{body}</p>
            <div className="flex flex-wrap gap-3"><StoreButton store="apple" /><StoreButton store="google" /></div>
          </div>
          {/* The phone rises out of the band's lower edge. */}
          <div className="relative mx-auto -mb-40 w-56 md:mb-0 md:w-full md:translate-y-24 md:self-end">
            <Phone subject={subject} src={src} label={label} />
          </div>
        </div>
      </Section>
    );
  }
  return (
    <Section label={headline} tone="surface" className="overflow-hidden">
      <div className="grid items-center gap-16 lg:grid-cols-2">
        <div className="flex flex-col gap-6">
          <Eyebrow>{prop(node, "eyebrow", "The app")}</Eyebrow>
          <h2 className="font-heading-set text-h1 text-balance">{headline}</h2>
          <p className="max-w-xl text-lead text-muted text-pretty">{body}</p>
          <ul className="space-y-3">
            {points.map((p) => (
              <li key={p} className="flex items-center gap-3">
                <span className="grid size-6 place-items-center rounded-pill bg-accent text-accent-fg"><Check aria-hidden className="size-3.5" strokeWidth={3} /></span>{p}
              </li>))}
          </ul>
          <div className="mt-2 flex flex-wrap items-center gap-3"><StoreButton store="apple" /><StoreButton store="google" /></div>
          <div className="mt-4 flex items-center gap-6 border-t border-border pt-6">
            <div className="hidden items-center gap-3 sm:flex">
              <span className="rounded-card border border-border bg-bg p-1"><QRMark /></span>
              <span className="text-small text-muted">{prop(node, "qr_label", "Scan to download")}</span>
            </div>
            <div className="sm:border-l sm:border-border sm:pl-6">
              <Rating value={Number.parseFloat(prop(node, "rating", "4.8")) || 4.8} />
              <p className="mt-1 text-small text-muted">{prop(node, "rating_label", "Rated 4.8 by 12k+ people")}</p>
            </div>
          </div>
        </div>
        <div className="relative mx-auto flex w-full max-w-md items-end justify-center">
          <div aria-hidden className="absolute inset-x-0 bottom-0 mx-auto aspect-square w-[90%] rounded-pill"
            style={{ background: "radial-gradient(closest-side, color-mix(in srgb, var(--color-accent) 25%, transparent), transparent)" }} />
          <Phone subject="leaf" tone={2} label={`${label}, second screen`} className="relative -mr-12 hidden w-52 translate-y-8 -rotate-6 sm:block" />
          <Phone subject={subject} src={src} label={label} className="relative z-10 w-60 sm:w-64" />
        </div>
      </div>
    </Section>
  );
}

export const SECTIONS: SectionMap = {
  Hero, SocialProof, FeatureBento, FeatureCard, ProductShowcase, Metrics, Testimonials, PricingTable, CTA,
  CTASplit, IntegrationsGrid, AppDownload,
};
