/** Commerce sections. Keys are the catalog's implementation.root names. See sections/README.md. */
import { Children, useMemo, useState, type FormEvent, type ReactNode } from "react";
import * as RadioGroup from "@radix-ui/react-radio-group";
import * as ToggleGroup from "@radix-ui/react-toggle-group";
import {
  ArrowRight, ArrowUpRight, BadgeCheck, Check, ChevronDown, Clock, Gift, Heart, History, Leaf, Lock, Minus, Package,
  Plus, Repeat, RotateCcw, Search, ShieldCheck, SlidersHorizontal, Sparkles, Star, Tag, Trash2, Truck, X,
} from "lucide-react";
import {
  Avatar, Badge, Button, Card, Carousel, ChoiceChips, Disclosure, Eyebrow, Media, Price, QuantityStepper, Rating,
  Section, SectionHeader, Tabs, imageAt, listProp, prop, range, subjectOf, variantOf, type Subject,
} from "../ui";
import { cn } from "../lib/cn";
import type { RenderNode } from "../types";
import type { NodeProps, SectionMap } from "./types";

/** Stand-in catalogue for sections that received no product content. Domain-neutral on purpose. */
export const SAMPLE_PRODUCTS: { title: string; note: string; price: string; badge?: string; subject: Subject }[] = [
  { title: "Nº1 Signature", note: "Our house favourite", price: "$24", badge: "Bestseller", subject: "bag" },
  { title: "Morning Ritual", note: "Bright and balanced", price: "$19", badge: "New", subject: "cup" },
  { title: "Garden Reserve", note: "Limited seasonal harvest", price: "$32", badge: "Seasonal", subject: "leaf" },
  { title: "Cold Studio", note: "Made for warm afternoons", price: "$16", subject: "glass" },
  { title: "The Essential", note: "Everyday, done right", price: "$14", subject: "product" },
  { title: "Evening Blend", note: "Deep and smooth", price: "$22", badge: "Bestseller", subject: "bag" },
  { title: "Field Notes", note: "A taste of the source", price: "$27", subject: "leaf" },
  { title: "Slow Pour", note: "For patient mornings", price: "$21", subject: "cup" },
];

const sample = (i: number) => SAMPLE_PRODUCTS[i % SAMPLE_PRODUCTS.length];
/** Badges sit on imagery, so every tone is a solid fill; an outline badge would vanish on a photo. */
const badgeTone = (b?: string): "accent" | "neutral" | "primary" =>
  b === "New" ? "accent" : b === "Seasonal" ? "neutral" : "primary";

/* ------------------------------------------------------------------ local helpers */
/** An option list slot; the single value "hide" removes the whole group. */
const optionsOf = (n: RenderNode, key: string, fallback: string[]) => {
  const v = listProp(n, key, fallback);
  return v.length === 1 && v[0].toLowerCase() === "hide" ? [] : v;
};
const money = (s: string) => { const m = s.replace(",", ".").match(/-?\d+(?:\.\d+)?/); return m ? parseFloat(m[0]) : 0; };
const currencyOf = (s: string) => s.match(/^[^\d-]*/)?.[0].trim() || "$";
const fmt = (n: number, cur: string) => `${cur}${n.toFixed(2)}`;
const at = <T,>(list: T[], i: number, fallback: T): T => (list.length ? list[i % list.length] : fallback);

const chipCls =
  "inline-flex h-11 min-w-11 items-center justify-center gap-2 rounded-button border border-border px-4 text-small font-medium " +
  "transition-[background-color,color,border-color,transform] duration-200 ease-brand hover:border-fg/40 active:scale-[0.97]";
const chipOn = "border-primary bg-primary text-primary-fg hover:border-primary";
const inputCls =
  "h-12 w-full rounded-button border border-border bg-bg px-4 text-body text-fg placeholder:text-muted/70 " +
  "transition-[border-color,box-shadow] duration-200 focus:border-ring focus:outline-none focus:ring-4 focus:ring-ring/15";

function FavoriteButton({ title, className }: { title: string; className?: string }) {
  const [on, setOn] = useState(false);
  return (
    <button type="button" aria-pressed={on} aria-label={`${on ? "Remove" : "Save"} ${title} ${on ? "from" : "to"} favourites`}
      onClick={() => setOn((v) => !v)}
      className={cn("grid size-11 shrink-0 place-items-center rounded-pill bg-bg/90 text-fg shadow-sm backdrop-blur transition-transform duration-200 ease-brand hover:scale-110 active:scale-95", className)}>
      <Heart className={cn("size-[18px] transition-colors", on && "fill-accent text-accent")} />
    </button>
  );
}

function SelectField({ id, label, options, inline, className }: {
  id: string; label: string; options: string[]; inline?: boolean; className?: string;
}) {
  return (
    <div className={cn(inline ? "flex items-center gap-3" : "space-y-2", className)}>
      <label htmlFor={id} className={cn("shrink-0 text-small font-semibold", inline && "text-muted font-medium")}>{label}</label>
      <div className="relative min-w-0 flex-1">
        <select id={id} className={cn(inputCls, "cursor-pointer appearance-none pr-11 font-medium")}>
          {options.map((o) => <option key={o}>{o}</option>)}
        </select>
        <ChevronDown aria-hidden className="pointer-events-none absolute right-4 top-1/2 size-4 -translate-y-1/2 text-muted" />
      </div>
    </div>
  );
}

function SearchField({ id, label, placeholder, value, onChange, size = "md", className, action }: {
  id: string; label: string; placeholder: string; value: string; onChange: (v: string) => void;
  size?: "md" | "lg"; className?: string; action?: ReactNode;
}) {
  return (
    <div className={cn("relative", className)}>
      <label htmlFor={id} className="sr-only">{label}</label>
      <Search aria-hidden className={cn("pointer-events-none absolute top-1/2 -translate-y-1/2 text-muted", size === "lg" ? "left-5 size-5" : "left-4 size-4")} />
      <input id={id} type="search" value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} autoComplete="off"
        className={cn(inputCls, size === "lg" ? "h-16 rounded-pill pl-14 text-lead shadow-sm" : "pl-11", action && "pr-36")} />
      {action && <div className="absolute right-2 top-1/2 -translate-y-1/2">{action}</div>}
    </div>
  );
}

/** A controlled chip group (Radix toggle group) that can show a price delta under each option. */
function OptionGroup({ label, options, value, onChange, deltas, cur, multiple, step }: {
  label: string; options: string[]; value: string[]; onChange: (v: string[]) => void;
  deltas?: number[]; cur: string; multiple?: boolean; step?: number;
}) {
  const items = options.map((o, i) => (
    <ToggleGroup.Item key={o} value={o}
      className={cn(chipCls, "h-auto min-h-11 flex-col gap-0 py-2 data-[state=on]:border-primary data-[state=on]:bg-primary data-[state=on]:text-primary-fg")}>
      <span className="flex items-center gap-1.5">{multiple && <Plus aria-hidden className="size-3.5 transition-transform duration-200 [[data-state=on]_&]:rotate-45" />}{o}</span>
      {deltas && deltas[i] > 0 && <span className="text-caption font-normal opacity-80">+{fmt(deltas[i], cur)}</span>}
    </ToggleGroup.Item>));
  const summary = value.length ? value.join(", ") : "None";
  return (
    <fieldset className="space-y-3">
      <legend className="flex w-full items-center gap-3 text-small font-semibold">
        {step !== undefined && (
          <span aria-hidden className="grid size-7 place-items-center rounded-pill border border-border text-caption tabular-nums">{String(step).padStart(2, "0")}</span>)}
        <span>{label} <span className="font-normal text-muted">· {summary}</span></span>
      </legend>
      {multiple ? (
        <ToggleGroup.Root type="multiple" value={value} onValueChange={onChange} aria-label={label} className="flex flex-wrap gap-2">{items}</ToggleGroup.Root>
      ) : (
        <ToggleGroup.Root type="single" value={value[0]} onValueChange={(v) => v && onChange([v])} aria-label={label} className="flex flex-wrap gap-2">{items}</ToggleGroup.Root>
      )}
    </fieldset>
  );
}

/** Controlled quantity stepper, for places where the quantity feeds a live total. */
function Stepper({ value, onChange, label = "Quantity" }: { value: number; onChange: (n: number) => void; label?: string }) {
  return (
    <div className="inline-flex h-12 shrink-0 items-center rounded-button border border-border" role="group" aria-label={label}>
      <button type="button" aria-label="Decrease quantity" onClick={() => onChange(Math.max(1, value - 1))}
        className="grid size-11 place-items-center rounded-button text-fg transition-colors hover:bg-fg/[0.06]"><Minus className="size-4" /></button>
      <output aria-live="polite" className="w-8 text-center font-semibold tabular-nums">{value}</output>
      <button type="button" aria-label="Increase quantity" onClick={() => onChange(value + 1)}
        className="grid size-11 place-items-center rounded-button text-fg transition-colors hover:bg-fg/[0.06]"><Plus className="size-4" /></button>
    </div>
  );
}

/** Picks an icon from what a trust line says, so custom copy still gets a fitting glyph. */
const TRUST_ICONS: [RegExp, typeof Truck][] = [
  [/ship|deliver|dispatch/i, Truck], [/return|exchange|refund/i, RotateCcw], [/secure|pay|checkout|encrypt/i, Lock],
  [/fresh|made|craft|roast|hand/i, Sparkles], [/gift|wrap/i, Gift], [/sustain|eco|organic|plant|compost/i, Leaf],
  [/guarantee|warrant|quality/i, ShieldCheck], [/subscri|repeat|refill/i, Repeat], [/pack/i, Package],
];
const trustIcon = (text: string, i: number) =>
  TRUST_ICONS.find(([re]) => re.test(text))?.[1] ?? [Truck, Sparkles, RotateCcw, Lock][i % 4];

/* ------------------------------------------------------------------ product card & grid */
/** Trailing digits of a node id ("featured_products-item-3" -> 3) vary tone across sibling cards. */
const indexOf = (id: string) => Number(id.match(/(\d+)$/)?.[1] ?? 0);

function ProductCard({ node, index }: NodeProps & { index?: number }) {
  const i = index ?? indexOf(node.id);
  // A card with its own title is real content: nothing is borrowed from the sample catalogue.
  const s = prop(node, "title", "") ? null : sample(i);
  const title = s ? s.title : prop(node, "title", "");
  const price = s ? s.price : prop(node, "price", "");
  const note = s ? s.note : prop(node, "note", "");
  const badge = s ? s.badge ?? "" : prop(node, "badge", "");
  const subject = s ? s.subject : subjectOf(prop(node, "image", ""), "product");
  const src = imageAt(node, "image")?.url;
  const variant = variantOf(node);

  if (variant === "compact") {
    return (
      <article className="group flex items-center gap-4 rounded-card border border-border bg-surface p-3 transition-colors hover:border-fg/25">
        <Media ratio="1/1" subject={subject} src={src} tone={i} label={title} className="w-20 shrink-0 rounded-sm" />
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-semibold">{title}</h3>
          {note && <p className="truncate text-small text-muted">{note}</p>}
          <Price value={price} className="mt-1 text-small" />
        </div>
        <Button size="icon" variant="secondary" aria-label={`Add ${title} to cart`}><Plus className="size-4" /></Button>
      </article>
    );
  }
  const premium = variant === "premium";
  return (
    <article className="group relative flex flex-col">
      <div className="relative">
        <Media ratio={premium ? "4/5" : "1/1"} subject={subject} src={src} tone={i} label={title}
          className={cn("transition-shadow duration-500 ease-brand group-hover:shadow-lg", !premium && "rounded-card")} />
        {badge && <Badge tone={badgeTone(badge)} className="absolute left-3 top-3">{badge}</Badge>}
        <FavoriteButton title={title} className="absolute right-3 top-3" />
        {/* Quick add: always reachable on touch, revealed on hover where a pointer exists. */}
        <Button variant="primary" className="absolute inset-x-3 bottom-3 translate-y-0 opacity-100 transition-[opacity,transform] duration-300 ease-brand md:translate-y-3 md:opacity-0 md:group-hover:translate-y-0 md:group-hover:opacity-100 md:group-focus-within:translate-y-0 md:group-focus-within:opacity-100">
          <Plus className="size-4" aria-hidden /> Quick add
        </Button>
      </div>
      <div className={cn("mt-4 flex items-start justify-between gap-4", premium && "mt-5")}>
        <div className="min-w-0">
          <h3 className={cn("font-semibold", premium && "font-heading-set text-h4")}>{title}</h3>
          {note && <p className="mt-1 text-small text-muted">{note}</p>}
        </div>
        <Price value={price} className="shrink-0" />
      </div>
      {premium && <Rating value={4.8} count={120 + i * 17} className="mt-3" />}
    </article>
  );
}

const stubCard = (i: number, variant: string): RenderNode => ({
  id: `card-${i}`, semantic_type: "product_card", implementation: "ProductCard",
  props: { variant }, tokens: {}, layout: null, animation: null, children: [],
});
const sampleCards = (count: number, variant: string, offset = 0) =>
  range(count).map((i) => <ProductCard key={i} index={i + offset} node={stubCard(i + offset, variant)} children={null} hasChildren={false} />);

function ProductGrid({ node, children, hasChildren, columns }: NodeProps) {
  const variant = variantOf(node);
  const cardVariant = variant === "dense" ? "standard" : variant === "premium" ? "premium" : "standard";
  const count = variant === "dense" ? 8 : 6;
  const cols = columns ?? (variant === "dense" ? 4 : 3);
  return (
    <Section label={prop(node, "title", "Products")}>
      <SectionHeader eyebrow={prop(node, "eyebrow", "Shop")} title={prop(node, "title", "Best sellers")}
        body={prop(node, "subtitle", "The pieces our customers come back for, again and again.")}
        action={<Button variant="link" arrow>{prop(node, "cta", "View all")}</Button>} />
      {/* Columns come from the layout engine at desktop; phones and tablets always get 1 and 2. */}
      <div className={cn("grid grid-cols-1 gap-x-6 gap-y-12 sm:grid-cols-2 lg:grid-cols-[repeat(var(--cols),minmax(0,1fr))]", variant === "dense" && "gap-y-10")}
        style={{ ["--cols" as string]: cols }}>
        {hasChildren ? children : sampleCards(count, cardVariant)}
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ product detail */
const GALLERY: Subject[] = ["bag", "cup", "leaf", "glass", "product"];

/** The `media` slot lists up to four gallery shots; each position takes its photo or a silhouette. */
const shotSrc = (node: RenderNode, i: number) => imageAt(node, "media", i)?.url;

function Gallery({ node, title, main, layout }: { node: RenderNode; title: string; main: Subject; layout: "below" | "side" }) {
  const shots = [main, ...GALLERY.filter((s) => s !== main)].slice(0, 4) as Subject[];
  const [active, setActive] = useState(0);
  const thumbs = (
    <div role="group" aria-label="Product images"
      className={cn("grid grid-cols-4 gap-3", layout === "side" && "lg:order-first lg:flex lg:w-20 lg:flex-col")}>
      {shots.map((s, i) => (
        <button key={i} type="button" aria-label={`Show image ${i + 1} of ${shots.length}`} aria-pressed={active === i} onClick={() => setActive(i)}
          className={cn("rounded-sm ring-offset-2 ring-offset-bg transition-[opacity,box-shadow] duration-200 ease-brand",
            active === i ? "ring-2 ring-fg" : "opacity-70 hover:opacity-100")}>
          <Media ratio="1/1" subject={s} src={shotSrc(node, i)} tone={i} zoom={false} label={`${title}, view ${i + 1}`} className="rounded-sm" />
        </button>))}
    </div>
  );
  return (
    <div className={cn("flex flex-col gap-3", layout === "side" && "lg:flex-row lg:gap-4")}>
      <div className="relative min-w-0 flex-1">
        <Media ratio={layout === "side" ? "4/5" : "1/1"} subject={shots[active]} src={shotSrc(node, active)} tone={active} label={`${title}, image ${active + 1}`} className="shadow-sm" />
        <Badge tone="primary" className="absolute left-4 top-4">{active + 1} / {shots.length}</Badge>
      </div>
      {thumbs}
    </div>
  );
}

function DetailOptions({ node }: NodeProps) {
  const groups: [string, string, string[]][] = [
    ["sizes", prop(node, "size_label", "Size"), ["Small", "Medium", "Large"]],
    ["temperatures", prop(node, "temperature_label", "Temperature"), ["Hot", "Iced"]],
    ["milks", prop(node, "milk_label", "Milk"), ["Whole", "Oat", "Almond", "None"]],
    ["sweetness", prop(node, "sweetness_label", "Sweetness"), ["Unsweetened", "Light", "Classic"]],
  ];
  return (
    <div className="grid gap-6">
      {groups.map(([key, label, fallback]) => {
        const opts = optionsOf(node, key, fallback);
        return opts.length ? <ChoiceChips key={key} label={label} options={opts} initial={opts[Math.min(1, opts.length - 1)]} /> : null;
      })}
    </div>
  );
}

function BuyRow({ node, title, price }: { node: RenderNode; title: string; price: string }) {
  return (
    <div className="flex items-center gap-2 sm:gap-3">
      <QuantityStepper id={`${node.id}-qty`} />
      <Button size="lg" className="min-w-0 flex-1 px-5 sm:px-8">
        {prop(node, "primary_cta", "Add to cart")}
        <span className="hidden items-center gap-2 tabular-nums sm:inline-flex"><span aria-hidden className="opacity-60">·</span>{price}</span>
      </Button>
      <FavoriteButton title={title} className="size-14 rounded-button border border-border bg-transparent shadow-none backdrop-blur-none" />
    </div>
  );
}

function ShippingNote({ node }: { node: RenderNode }) {
  return (
    <ul className="grid gap-3 text-small sm:grid-cols-2">
      {[[Truck, prop(node, "shipping_note", "Free delivery over $50")], [RotateCcw, prop(node, "returns_note", "30-day easy returns")]].map(([Icon, text], i) => {
        const I = Icon as typeof Truck;
        return <li key={i} className="flex items-center gap-2.5 text-muted"><I aria-hidden className="size-4 shrink-0 text-fg" />{text as string}</li>;
      })}
    </ul>
  );
}

const SPECS = ["Origin: Responsibly sourced", "Made: In small batches", "Packaging: Recyclable, gift ready", "Dispatch: Within 2 working days"];

function detailTabs(node: RenderNode) {
  const specs = listProp(node, "specs", SPECS).map((s) => { const [k, ...v] = s.split(":"); return [k.trim(), v.join(":").trim()]; });
  const tabs = [
    { id: "details", label: prop(node, "details_label", "Details"), content: (
      <div className="space-y-6">
        <p className="text-muted text-pretty">{prop(node, "details", "Every batch is made to order and finished by hand, so it reaches you at its very best. Considered down to the packaging, which is fully recyclable.")}</p>
        <dl className="divide-y divide-border border-y border-border text-small">
          {specs.map(([k, v]) => <div key={k} className="flex justify-between gap-6 py-3"><dt className="text-muted">{k}</dt><dd className="text-right font-medium">{v}</dd></div>)}
        </dl>
      </div>) },
    { id: "notes", label: prop(node, "notes_label", "Notes"), content: (
      <ul className="flex flex-wrap gap-2">{listProp(node, "notes", ["Rich", "Rounded", "Quietly complex", "Long finish"]).map((n) => (
        <li key={n}><Badge tone="neutral" className="px-3.5 py-1.5 text-small font-medium">{n}</Badge></li>))}</ul>) },
    { id: "shipping", label: prop(node, "shipping_label", "Shipping & returns"), content: (
      <p className="text-muted text-pretty">{prop(node, "shipping", "Orders placed before 2pm ship the same day. Free delivery on orders over $50, and returns are free within 30 days.")}</p>) },
  ];
  return tabs;
}

function ProductDetail({ node }: NodeProps) {
  const variant = variantOf(node);
  const title = prop(node, "title", "Nº1 Signature");
  const price = prop(node, "price", "$24.00");
  const compare = prop(node, "compare_at", "");
  const main = subjectOf(prop(node, "media", ""), "bag");
  const rating = Number(prop(node, "rating", "4.8")) || 4.8;
  const count = Number(prop(node, "review_count", "218")) || 218;
  const eyebrow = prop(node, "eyebrow", "House collection");
  const badge = prop(node, "badge", "Bestseller");
  const description = prop(node, "description", "Our most-loved piece, refined over years. Balanced, generous and quietly memorable — the one customers return for.");
  const tabs = detailTabs(node);

  const header = (center?: boolean) => (
    <div className={cn("space-y-4", center && "flex flex-col items-center text-center")}>
      <div className={cn("flex flex-wrap items-center gap-3", center && "justify-center")}>
        <Eyebrow>{eyebrow}</Eyebrow>
        {badge && <Badge tone="accent">{badge}</Badge>}
      </div>
      <h1 className={cn("font-heading-set text-balance", center ? "text-display" : "text-h1")}>{title}</h1>
      <div className={cn("flex flex-wrap items-center gap-x-5 gap-y-2", center && "justify-center")}>
        <Price value={price} compareAt={compare || undefined} className="text-h3" />
        <a href="#reviews" className="inline-flex min-h-11 items-center underline-offset-4 hover:underline"><Rating value={rating} count={count} /></a>
      </div>
      <p className={cn("max-w-xl text-lead text-muted text-pretty", center && "mx-auto")}>{description}</p>
    </div>
  );

  if (variant === "premium_split") {
    return (
      <Section label={`Product: ${title}`} wide size="sm">
        <div className="grid gap-10 lg:grid-cols-2 lg:gap-12">
          <div className="lg:sticky lg:top-8 lg:self-start"><Gallery node={node} title={title} main={main} layout="side" /></div>
          <div className="rounded-lg bg-surface p-6 sm:p-10 lg:p-14">
            <div className="flex flex-col gap-8 lg:sticky lg:top-10">
              {header()}
              <ul className="grid grid-cols-3 divide-x divide-border rounded-card border border-border bg-bg text-center">
                {listProp(node, "highlights", ["Small batch", "Hand finished", "Gift ready"]).slice(0, 3).map((h, i) => {
                  const I = [Sparkles, Leaf, Gift][i];
                  return <li key={h} className="flex flex-col items-center gap-2 px-2 py-4 text-small font-medium"><I aria-hidden className="size-5 text-muted" />{h}</li>;
                })}
              </ul>
              <DetailOptions node={node} children={null} hasChildren={false} />
              <BuyRow node={node} title={title} price={price} />
              <ShippingNote node={node} />
              <Disclosure items={tabs.map((t, i) => ({ q: t.label, a: i === 0 ? prop(node, "details", "Every batch is made to order and finished by hand, so it reaches you at its very best.")
                : i === 1 ? listProp(node, "notes", ["Rich", "Rounded", "Quietly complex", "Long finish"]).join(" · ")
                : prop(node, "shipping", "Orders placed before 2pm ship the same day. Free delivery on orders over $50, and returns are free within 30 days.") }))} />
            </div>
          </div>
        </div>
      </Section>
    );
  }

  if (variant === "stacked") {
    const shots = [main, ...GALLERY.filter((s) => s !== main)].slice(0, 4) as Subject[];
    return (
      <Section label={`Product: ${title}`} size="sm">
        {header(true)}
        <Carousel label={`${title} images`} className="mt-12">
          {shots.map((s, i) => (
            <Media key={i} ratio="4/5" subject={s} src={shotSrc(node, i)} tone={i} label={`${title}, view ${i + 1}`}
              className="w-[80vw] sm:w-[46vw] lg:w-[386px]" />))}
        </Carousel>
        <div className="mt-12 grid gap-10 lg:grid-cols-12 lg:gap-14">
          <Card className="flex flex-col gap-7 p-6 sm:p-8 lg:col-span-5 lg:self-start">
            <DetailOptions node={node} children={null} hasChildren={false} />
            <BuyRow node={node} title={title} price={price} />
            <ShippingNote node={node} />
          </Card>
          <div className="lg:col-span-7"><Tabs label="Product information" tabs={tabs} /></div>
        </div>
      </Section>
    );
  }

  return (
    <Section label={`Product: ${title}`} size="sm">
      {/* Phones read gallery, buy box, details; desktop keeps details under the gallery. */}
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-x-16 lg:gap-y-14">
        <div className="lg:col-span-7"><Gallery node={node} title={title} main={main} layout="below" /></div>
        <div className="flex flex-col gap-8 lg:sticky lg:top-8 lg:col-span-5 lg:row-span-2 lg:self-start">
          {header()}
          <div className="border-t border-border pt-8"><DetailOptions node={node} children={null} hasChildren={false} /></div>
          <BuyRow node={node} title={title} price={price} />
          <ShippingNote node={node} />
        </div>
        <Tabs label="Product information" tabs={tabs} className="lg:col-span-7" />
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ trust signals */
function TrustSignals({ node, columns }: NodeProps) {
  const variant = variantOf(node);
  const titles = listProp(node, "items", ["Free delivery", "Made fresh to order", "Easy returns", "Secure checkout"]);
  const details = listProp(node, "details", ["On every order over $50", "Prepared the day it ships", "30 days, no questions asked", "Encrypted, trusted payments"]);
  const label = prop(node, "title", "Why shop with us");

  if (variant === "inline") {
    return (
      <Section label={label} size="none" className="py-6">
        <ul className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4 border-y border-border py-5">
          {titles.map((t, i) => {
            const I = trustIcon(t, i);
            return (
              <li key={t} className="flex items-center gap-2.5 text-small">
                <I aria-hidden className="size-[18px] shrink-0" />
                <span className="font-semibold">{t}</span>
                <span className="hidden text-muted md:inline">· {at(details, i, "")}</span>
              </li>);
          })}
        </ul>
      </Section>
    );
  }
  if (variant === "cards") {
    return (
      <Section label={label} size="sm">
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-[repeat(var(--cols),minmax(0,1fr))]" style={{ ["--cols" as string]: columns ?? Math.min(4, titles.length) }}>
          {titles.map((t, i) => {
            const I = trustIcon(t, i);
            return (
              <li key={t} className="flex flex-col gap-5 rounded-card border border-border bg-surface p-6 transition-[border-color,transform] duration-300 ease-brand hover:-translate-y-0.5 hover:border-fg/20">
                <span className="grid size-12 place-items-center rounded-pill bg-primary text-primary-fg"><I aria-hidden className="size-5" /></span>
                <div><h3 className="font-heading-set text-h4">{t}</h3><p className="mt-1.5 text-small text-muted">{at(details, i, "")}</p></div>
              </li>);
          })}
        </ul>
      </Section>
    );
  }
  return (
    <Section label={label} tone="surface" size="sm">
      <ul className="grid gap-x-8 gap-y-8 sm:grid-cols-2 lg:grid-cols-[repeat(var(--cols),minmax(0,1fr))] lg:divide-x lg:divide-border"
        style={{ ["--cols" as string]: columns ?? Math.min(4, titles.length) }}>
        {titles.map((t, i) => {
          const I = trustIcon(t, i);
          return (
            <li key={t} className="flex items-start gap-4 lg:px-6 lg:first:pl-0">
              <span className="grid size-12 shrink-0 place-items-center rounded-card border border-border bg-bg"><I aria-hidden className="size-5" /></span>
              <div className="pt-0.5"><h3 className="font-semibold">{t}</h3><p className="mt-1 text-small text-muted text-pretty">{at(details, i, "")}</p></div>
            </li>);
        })}
      </ul>
    </Section>
  );
}

/* ------------------------------------------------------------------ reviews */
const REVIEWS = [
  { name: "Amelia Hart", rating: 5, title: "Worth every penny", body: "Beautifully made and it arrived quicker than promised. The packaging alone felt like a gift — I have already ordered a second for a friend.", date: "2 weeks ago", meta: "Medium" },
  { name: "Daniel Okafor", rating: 5, title: "My new daily ritual", body: "Consistent, generous and clearly made with care. It has quietly become the best part of my morning.", date: "1 month ago", meta: "Large" },
  { name: "Sofia Marín", rating: 4, title: "Lovely, will reorder", body: "Exactly as described and the quality shows. Delivery took a day longer than expected, but support kept me updated throughout.", date: "1 month ago", meta: "Small" },
  { name: "Theo Lindqvist", rating: 5, title: "Thoughtful from start to finish", body: "From the note in the box to the finish of the product itself, every detail has been considered.", date: "2 months ago", meta: "Medium" },
];
const DIST = [78, 15, 4, 2, 1];

function ReviewCard({ r, compact }: { r: (typeof REVIEWS)[number]; compact?: boolean }) {
  return (
    <Card as="li" className={cn("flex flex-col gap-4", compact && "bg-bg")}>
      <div className="flex items-center justify-between gap-3">
        <Rating value={r.rating} />
        <span className="text-caption text-muted">{r.date}</span>
      </div>
      <div className="space-y-2">
        <h3 className="font-heading-set text-h4">{r.title}</h3>
        <p className="text-muted text-pretty">{r.body}</p>
      </div>
      <div className="mt-auto flex items-center gap-3 border-t border-border pt-4">
        <Avatar name={r.name} className="size-10" />
        <div className="min-w-0">
          <p className="truncate text-small font-semibold">{r.name}</p>
          <p className="flex items-center gap-1 text-caption text-muted"><BadgeCheck aria-hidden className="size-3.5 text-success" /> Verified buyer · {r.meta}</p>
        </div>
      </div>
    </Card>
  );
}

/** Stars only, for places where the numeric average is already shown large beside them. */
function Stars({ value }: { value: number }) {
  return (
    <span role="img" aria-label={`Rated ${value.toFixed(1)} out of 5`} className="flex">
      {range(5).map((i) => <Star key={i} aria-hidden className={cn("size-4", i < Math.round(value) ? "fill-current text-accent" : "text-border")} />)}
    </span>
  );
}

function Distribution({ className }: { className?: string }) {
  return (
    <ul className={cn("space-y-2.5", className)} aria-label="Rating distribution">
      {DIST.map((pct, i) => (
        <li key={i} className="flex items-center gap-3 text-small">
          <span className="w-12 shrink-0 tabular-nums text-muted">{5 - i} star</span>
          <span aria-hidden className="h-2 flex-1 overflow-hidden rounded-pill bg-fg/[0.08]">
            <span className="block h-full rounded-pill bg-accent" style={{ width: `${pct}%` }} />
          </span>
          <span className="w-9 shrink-0 text-right tabular-nums text-muted">{pct}%</span>
        </li>))}
    </ul>
  );
}

function Reviews({ node }: NodeProps) {
  const variant = variantOf(node);
  const rating = Number(prop(node, "rating", "4.8")) || 4.8;
  const count = prop(node, "count", "218");
  const title = prop(node, "title", "What customers are saying");
  const cta = prop(node, "cta", "Write a review");

  if (variant === "compact") {
    return (
      <Section label="Reviews" tone="surface">
        <div id="reviews" className="mb-10 grid items-center gap-8 rounded-lg border border-border bg-bg p-6 md:grid-cols-[auto_1fr_auto] md:gap-12 md:p-8">
          <div className="flex items-center gap-5">
            <p className="font-heading-set text-display tabular-nums">{rating.toFixed(1)}</p>
            <div className="space-y-1">
              <Stars value={rating} />
              <p className="text-small text-muted">From {count} verified reviews</p>
            </div>
          </div>
          <div>
            <h2 className="font-heading-set text-h3 text-balance">{title}</h2>
            <Distribution className="mt-4 hidden max-w-md lg:block" />
          </div>
          <Button variant="secondary">{cta}</Button>
        </div>
        <ul className="grid gap-5 md:grid-cols-3">{REVIEWS.slice(0, 3).map((r) => <ReviewCard key={r.name} r={r} compact />)}</ul>
      </Section>
    );
  }
  return (
    <Section label="Reviews">
      <div id="reviews" className="grid gap-12 lg:grid-cols-12 lg:gap-16">
        <aside className="lg:col-span-4">
          <div className="space-y-6 lg:sticky lg:top-10">
            <Eyebrow>{prop(node, "eyebrow", "Reviews")}</Eyebrow>
            <h2 className="font-heading-set text-h2 text-balance">{title}</h2>
            <div className="flex items-end gap-4">
              <p className="font-heading-set text-display leading-none tabular-nums">{rating.toFixed(1)}</p>
              <div className="space-y-1 pb-1"><Stars value={rating} /><p className="text-small text-muted">Based on {count} reviews</p></div>
            </div>
            <Distribution />
            <p className="flex items-center gap-2 text-small text-muted"><ShieldCheck aria-hidden className="size-4 text-fg" /> {prop(node, "recommend", "96% would recommend to a friend")}</p>
            <Button variant="secondary" className="w-full sm:w-auto">{cta}</Button>
          </div>
        </aside>
        <div className="lg:col-span-8">
          <ul className="grid gap-5 md:grid-cols-2">{REVIEWS.map((r) => <ReviewCard key={r.name} r={r} />)}</ul>
          <div className="mt-8 flex justify-center"><Button variant="ghost" arrow>{prop(node, "more_cta", "Read all reviews")}</Button></div>
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ related products */
function RelatedProducts({ node, children, hasChildren, columns }: NodeProps) {
  const variant = variantOf(node, "carousel");
  const title = prop(node, "title", "You may also like");
  const header = (
    <SectionHeader eyebrow={prop(node, "eyebrow", "Pairs well with")} title={title}
      body={prop(node, "subtitle", "")} className="md:mb-10"
      action={<Button variant="link" arrow>{prop(node, "cta", "Shop all")}</Button>} />
  );
  if (variant === "grid") {
    const cards = hasChildren ? Children.toArray(children) : sampleCards(4, "premium", 2);
    return (
      <Section label={title} tone="surface">
        <SectionHeader align="center" eyebrow={prop(node, "eyebrow", "Pairs well with")} title={title}
          body={prop(node, "subtitle", "Chosen to sit beside what you are looking at.")} />
        <div className="grid grid-cols-1 gap-x-6 gap-y-12 sm:grid-cols-2 lg:grid-cols-[repeat(var(--cols),minmax(0,1fr))]"
          style={{ ["--cols" as string]: columns ?? 4 }}>{cards.slice(0, (columns ?? 4) * (hasChildren ? 3 : 1))}</div>
        <div className="mt-12 flex justify-center"><Button variant="secondary" arrow>{prop(node, "cta", "Shop all")}</Button></div>
      </Section>
    );
  }
  const cards = hasChildren ? Children.toArray(children) : sampleCards(6, "standard", 2);
  return (
    <Section label={title} className="overflow-hidden">
      {header}
      <Carousel label={title}>
        {cards.map((c, i) => <div key={i} className="w-[78vw] sm:w-[44vw] lg:w-[285px]">{c}</div>)}
      </Carousel>
    </Section>
  );
}

/* ------------------------------------------------------------------ product filters */
function useFilters(node: RenderNode) {
  const categories = listProp(node, "categories", ["All", "New arrivals", "Best sellers", "Gift sets", "Limited edition"]);
  const filters = listProp(node, "filters", ["In stock", "Under $30", "New this month", "Gift ready"]);
  const sorts = listProp(node, "sort_options", ["Featured", "Newest", "Price: low to high", "Price: high to low", "Top rated"]);
  const [cat, setCat] = useState(0);
  const [active, setActive] = useState<string[]>([filters[0]]);
  const [q, setQ] = useState("");
  const total = Number(prop(node, "count", "48")) || 48;
  const shown = Math.max(1, Math.round(total * (cat === 0 ? 1 : 0.4) * Math.pow(0.7, active.length)) - (q ? 3 : 0));
  const toggle = (f: string) => setActive((a) => (a.includes(f) ? a.filter((x) => x !== f) : [...a, f]));
  return { categories, filters, sorts, cat, setCat, active, setActive, toggle, q, setQ, shown };
}

function FilterChips({ f, className, compact }: { f: ReturnType<typeof useFilters>; className?: string; compact?: boolean }) {
  return (
    <div className={cn("flex flex-wrap items-center gap-2", className)} role="group" aria-label="Filters">
      {f.filters.map((x) => {
        const on = f.active.includes(x);
        return (
          <button key={x} type="button" aria-pressed={on} onClick={() => f.toggle(x)} className={cn(chipCls, "rounded-pill", on && chipOn)}>
            {on && <Check aria-hidden className="size-3.5" />}{x}
          </button>);
      })}
      {f.active.length > 0 && (compact ? (
        <button type="button" aria-label="Clear all filters" onClick={() => f.setActive([])} className="grid size-11 place-items-center rounded-pill text-muted transition-colors hover:bg-fg/[0.06] hover:text-fg">
          <X aria-hidden className="size-4" />
        </button>
      ) : (
        <button type="button" onClick={() => f.setActive([])} className="inline-flex min-h-11 items-center gap-1.5 px-2 text-small font-semibold underline-offset-4 hover:underline">
          <X aria-hidden className="size-3.5" /> Clear all
        </button>))}
    </div>
  );
}

function ProductFilters({ node }: NodeProps) {
  const variant = variantOf(node, "bar");
  const f = useFilters(node);
  const title = prop(node, "title", "The full collection");
  const placeholder = prop(node, "search_placeholder", "Search products");
  const count = <p aria-live="polite" className="whitespace-nowrap text-small text-muted tabular-nums">{f.shown} {prop(node, "count_label", "products")}</p>;
  const search = (cls?: string, size?: "md" | "lg") => (
    <SearchField id={`${node.id}-search`} label={placeholder} placeholder={placeholder} value={f.q} onChange={f.setQ} className={cls} size={size} />);
  const sort = <SelectField id={`${node.id}-sort`} label={prop(node, "sort_label", "Sort by")} options={f.sorts} inline className="w-full sm:w-auto" />;

  if (variant === "chips") {
    return (
      <Section label="Browse and filter" size="sm">
        <div className="flex flex-col items-center text-center">
          <Eyebrow>{prop(node, "eyebrow", "Shop")}</Eyebrow>
          <h1 className="mt-4 font-heading-set text-h1 text-balance">{title}</h1>
          <p className="mt-4 max-w-xl text-lead text-muted text-pretty">{prop(node, "subtitle", "Considered pieces, made in small batches and delivered at their best.")}</p>
          {search("mt-8 w-full max-w-xl", "lg")}
          <nav aria-label="Categories" className="mt-8 flex max-w-full flex-wrap justify-center gap-2">
            {f.categories.map((c, i) => (
              <button key={c} type="button" aria-pressed={f.cat === i} onClick={() => f.setCat(i)}
                className={cn(chipCls, "h-12 rounded-pill px-5 text-body", f.cat === i ? chipOn : "bg-surface")}>
                {c}<span className={cn("text-caption tabular-nums", f.cat === i ? "opacity-80" : "text-muted")}>{[48, 12, 18, 9, 6][i % 5]}</span>
              </button>))}
          </nav>
        </div>
        <div className="mt-10 flex flex-col gap-4 border-t border-border pt-6 lg:flex-row lg:items-center lg:justify-between">
          <FilterChips f={f} />
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-6">{count}{sort}</div>
        </div>
      </Section>
    );
  }

  const nav = (
    <nav aria-label="Categories" className="-mb-px flex min-w-0 gap-1 self-stretch overflow-x-auto">
      {f.categories.map((c, i) => (
        <button key={c} type="button" aria-pressed={f.cat === i} onClick={() => f.setCat(i)}
          className={cn("min-h-14 shrink-0 border-b-2 px-3 text-small font-semibold transition-colors duration-200",
            f.cat === i ? "border-fg text-fg" : "border-transparent text-muted hover:text-fg")}>{c}</button>))}
    </nav>
  );

  if (variant === "toolbar") {
    return (
      <Section label="Refine products" size="none" className="py-6">
        <div className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-3 lg:flex-row lg:items-center">
          {search("lg:w-60 lg:shrink-0")}
          <FilterChips f={f} compact className="min-w-0 flex-1" />
          <div className="flex items-center justify-between gap-6 px-1">{count}{sort}</div>
        </div>
      </Section>
    );
  }

  return (
    <Section label="Browse and filter" size="sm">
      <div className="flex flex-col gap-6 pb-8 md:flex-row md:items-end md:justify-between">
        <div className="space-y-3">
          <Eyebrow>{prop(node, "eyebrow", "Shop")}</Eyebrow>
          <h1 className="font-heading-set text-h2 text-balance">{title}</h1>
          {count}
        </div>
        {search("w-full md:w-80")}
      </div>
      <div className="flex flex-col gap-3 border-b border-border lg:flex-row lg:items-center lg:justify-between">
        {nav}
        <div className="pb-3 lg:py-2">{sort}</div>
      </div>
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <span className="inline-flex items-center gap-2 pr-2 text-small font-semibold"><SlidersHorizontal aria-hidden className="size-4" /> {prop(node, "filter_label", "Filter")}</span>
        <FilterChips f={f} />
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ cart */
const CART = [
  { i: 0, meta: "Medium · Gift wrapped", qty: 1 },
  { i: 2, meta: "Large", qty: 2 },
  { i: 3, meta: "Set of 2", qty: 1 },
];
type CartLine = { i: number; title: string; meta: string; qty: number; unit: number; subject: Subject; src?: string };
/** Product-card children are the cart's real lines; without them the sample lines stand in. */
const cartLines = (node?: RenderNode): CartLine[] =>
  node && node.children.length
    ? node.children.map((c, i) => ({
        i, title: prop(c, "title", ""), meta: prop(c, "note", ""), qty: 1, unit: money(prop(c, "price", "0")),
        subject: subjectOf(prop(c, "image", ""), "product"), src: imageAt(c, "image")?.url,
      }))
    : CART.map((c) => ({ ...sample(c.i), ...c, unit: money(sample(c.i).price) }));

function CartItems({ node }: NodeProps) {
  const variant = variantOf(node);
  const lines = cartLines(node);
  const subtotal = lines.reduce((s, l) => s + l.unit * l.qty, 0);
  const threshold = money(prop(node, "free_shipping_threshold", "$120"));
  const left = Math.max(0, threshold - subtotal);

  if (variant === "compact") {
    return (
      <Section label="Cart items" size="sm">
        <div className="mx-auto max-w-xl rounded-lg border border-border bg-surface p-5 sm:p-6">
          <div className="flex items-baseline justify-between gap-4 border-b border-border pb-4">
            <h2 className="font-heading-set text-h4">{prop(node, "title", "Your bag")}</h2>
            <p className="text-small text-muted">{lines.length} items</p>
          </div>
          <ul className="divide-y divide-border">
            {lines.map((l) => (
              <li key={l.i} className="flex items-center gap-4 py-4">
                <Media ratio="1/1" subject={l.subject} src={l.src} tone={l.i} label={l.title} zoom={false} className="w-16 shrink-0 rounded-sm" />
                <div className="min-w-0 flex-1">
                  <h3 className="truncate font-semibold">{l.title}</h3>
                  <p className="truncate text-small text-muted">{l.meta ? `${l.meta} · ` : ""}Qty {l.qty}</p>
                  <Price value={`$${(l.unit * l.qty).toFixed(2)}`} className="mt-0.5 text-small sm:hidden" />
                </div>
                <Price value={`$${(l.unit * l.qty).toFixed(2)}`} className="hidden text-small sm:flex" />
                <Button variant="ghost" size="icon" aria-label={`Remove ${l.title}`}><X className="size-4" /></Button>
              </li>))}
          </ul>
        </div>
      </Section>
    );
  }
  return (
    <Section label="Cart items" size="sm">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h1 className="font-heading-set text-h1">{prop(node, "title", "Your cart")}</h1>
        <p className="text-muted">{lines.reduce((s, l) => s + l.qty, 0)} items</p>
      </div>
      <div className="mt-8 rounded-card border border-border bg-surface p-5">
        <p className="flex items-center gap-2 text-small font-medium">
          <Truck aria-hidden className="size-4 shrink-0" />
          {left > 0 ? <>You are <span className="font-semibold tabular-nums">${left.toFixed(2)}</span> away from free delivery</> : prop(node, "free_shipping_note", "Your order ships free")}
        </p>
        <span aria-hidden className="mt-3 block h-1.5 overflow-hidden rounded-pill bg-fg/[0.08]">
          <span className="block h-full rounded-pill bg-accent transition-[width] duration-700 ease-brand" style={{ width: `${Math.min(100, (subtotal / threshold) * 100)}%` }} />
        </span>
      </div>
      <div aria-hidden className="mt-10 hidden grid-cols-[7rem_minmax(0,1fr)_10rem_7rem] gap-x-6 border-b border-border pb-3 text-caption font-semibold uppercase tracking-[0.14em] text-muted md:grid">
        <span className="col-span-2">Product</span><span>Quantity</span><span className="text-right">Total</span>
      </div>
      <ul className="mt-4 divide-y divide-border border-b border-border md:mt-0">
        {lines.map((l) => (
          <li key={l.i} className="grid grid-cols-[5.5rem_minmax(0,1fr)] gap-x-4 py-6 md:grid-cols-[7rem_minmax(0,1fr)_10rem_7rem] md:items-center md:gap-x-6">
            <Media ratio="1/1" subject={l.subject} src={l.src} tone={l.i} label={l.title} className="rounded-card" />
            <div className="min-w-0 space-y-1">
              <h3 className="font-heading-set text-h4">{l.title}</h3>
              {l.meta && <p className="text-small text-muted">{l.meta}</p>}
              <p className="text-small tabular-nums text-muted">${l.unit.toFixed(2)} each</p>
              <div className="flex gap-4 pt-1">
                <button type="button" className="inline-flex min-h-11 items-center gap-1.5 text-small font-medium text-muted transition-colors hover:text-fg">
                  <Trash2 aria-hidden className="size-4" /> Remove</button>
                <button type="button" className="inline-flex min-h-11 items-center gap-1.5 text-small font-medium text-muted transition-colors hover:text-fg">
                  <Heart aria-hidden className="size-4" /> Save for later</button>
              </div>
            </div>
            <div className="col-start-2 mt-2 flex items-center justify-between gap-4 md:col-start-auto md:mt-0 md:contents">
              <QuantityStepper id={`${node.id}-qty-${l.i}`} initial={l.qty} label={`Quantity of ${l.title}`} />
              <Price value={`$${(l.unit * l.qty).toFixed(2)}`} className="justify-end text-lead" />
            </div>
          </li>))}
      </ul>
      <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
        <Button variant="link" className="gap-1.5"><ArrowRight aria-hidden className="size-4 rotate-180" /> {prop(node, "continue_cta", "Continue shopping")}</Button>
        <p className="text-small text-muted">{prop(node, "note", "Prices include taxes. Delivery is calculated at checkout.")}</p>
      </div>
    </Section>
  );
}

function OrderSummary({ node }: NodeProps) {
  const variant = variantOf(node);
  const lines = cartLines();
  const title = prop(node, "title", "Order summary");
  const rows: [string, string][] = [
    [prop(node, "subtotal_label", "Subtotal"), prop(node, "subtotal", "$104.00")],
    [prop(node, "shipping_label", "Delivery"), prop(node, "shipping", "Free")],
    [prop(node, "discount_label", "Discount · WELCOME10"), prop(node, "discount", "−$10.40")],
    [prop(node, "tax_label", "Estimated tax"), prop(node, "tax", "$7.49")],
  ];
  const total = prop(node, "total", "$101.09");
  const totals = (
    <>
      <dl className="space-y-3 text-small">
        {rows.map(([k, v]) => <div key={k} className="flex justify-between gap-4"><dt className="text-muted">{k}</dt><dd className="font-medium tabular-nums">{v}</dd></div>)}
      </dl>
      <div className="mt-5 flex items-baseline justify-between gap-4 border-t border-border pt-5">
        <span className="font-semibold">{prop(node, "total_label", "Total")}</span>
        <span className="flex items-baseline gap-2"><span className="text-caption text-muted">{prop(node, "currency", "USD")}</span><span className="font-heading-set text-h3 tabular-nums">{total}</span></span>
      </div>
    </>
  );

  if (variant === "compact") {
    // Sits beside the checkout form, which owns the only call to action: no button here.
    return (
      <Section label={title} size="sm">
        <aside className="mx-auto w-full max-w-md rounded-lg border border-border bg-surface p-6 sm:p-8">
          <h2 className="font-heading-set text-h4">{title}</h2>
          <ul className="mt-6 space-y-4 border-b border-border pb-6">
            {lines.map((l) => (
              <li key={l.i} className="flex items-center gap-4">
                <div className="relative w-16 shrink-0">
                  <Media ratio="1/1" subject={l.subject} tone={l.i} label={l.title} zoom={false} className="rounded-sm" />
                  <span className="absolute -right-2 -top-2 grid size-6 place-items-center rounded-pill bg-primary text-caption font-semibold text-primary-fg tabular-nums">{l.qty}</span>
                </div>
                <div className="min-w-0 flex-1"><p className="truncate font-semibold">{l.title}</p><p className="truncate text-small text-muted">{l.meta}</p></div>
                <Price value={`$${(l.unit * l.qty).toFixed(2)}`} className="text-small" />
              </li>))}
          </ul>
          <div className="mt-6">{totals}</div>
          <p className="mt-6 flex items-center gap-2 text-caption text-muted"><Lock aria-hidden className="size-3.5 shrink-0" /> {prop(node, "note", "Payments are encrypted and processed securely.")}</p>
        </aside>
      </Section>
    );
  }
  return (
    <Section label={title} size="sm">
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="space-y-6 lg:col-span-7">
          <div className="flex gap-4 rounded-card border border-border p-5">
            <Clock aria-hidden className="mt-0.5 size-5 shrink-0" />
            <div><p className="font-semibold">{prop(node, "delivery_title", "Arrives Thursday – Friday")}</p>
              <p className="mt-1 text-small text-muted">{prop(node, "delivery_note", "Order in the next 3 hours for dispatch today.")}</p></div>
          </div>
          <div className="flex gap-4 rounded-card border border-border p-5">
            <Gift aria-hidden className="mt-0.5 size-5 shrink-0" />
            <div className="flex-1 space-y-3">
              <div><p className="font-semibold">{prop(node, "gift_title", "Sending a gift?")}</p>
                <p className="mt-1 text-small text-muted">{prop(node, "gift_note", "Add a handwritten note and we will leave prices out of the box.")}</p></div>
              <label htmlFor={`${node.id}-gift`} className="sr-only">Gift message</label>
              <textarea id={`${node.id}-gift`} rows={3} placeholder="Your message" className={cn(inputCls, "h-auto resize-none py-3")} />
            </div>
          </div>
        </div>
        <aside className="rounded-lg border border-border bg-surface p-6 sm:p-8 lg:col-span-5 lg:self-start">
          <h2 className="mb-6 font-heading-set text-h4">{title}</h2>
          {totals}
          <form className="mt-6 flex gap-2" onSubmit={(e) => e.preventDefault()}>
            <label htmlFor={`${node.id}-code`} className="sr-only">Discount code</label>
            <div className="relative flex-1">
              <Tag aria-hidden className="pointer-events-none absolute left-4 top-1/2 size-4 -translate-y-1/2 text-muted" />
              <input id={`${node.id}-code`} placeholder="Discount code" className={cn(inputCls, "pl-11")} />
            </div>
            <Button variant="secondary" type="submit">Apply</Button>
          </form>
          <Button size="lg" arrow className="mt-6 w-full">{prop(node, "primary_cta", "Checkout")}</Button>
          <p className="mt-4 flex items-center justify-center gap-2 text-caption text-muted"><Lock aria-hidden className="size-3.5" /> {prop(node, "note", "Secure checkout · All major cards accepted")}</p>
        </aside>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ collections */
const COLLECTIONS = ["The Signature Edit", "Seasonal Rituals", "Cold & Bright", "Gifts & Sets", "Everyday Essentials"];
const COLLECTION_SUBJECTS: Subject[] = ["bag", "leaf", "glass", "product", "cup"];

function CollectionTile({ name, count, desc, subject, src, tone, ratio, className, mediaClass, cta, below }: {
  name: string; count: string; desc: string; subject: Subject; src?: string; tone: number; ratio: string; className?: string; mediaClass?: string; cta: string;
  below?: boolean;
}) {
  if (below) {
    return (
      <a href="#" className={cn("group block", className)}>
        <div className="relative">
          <Media ratio={ratio} subject={subject} src={src} tone={tone} label={name} className="transition-shadow duration-500 ease-brand group-hover:shadow-xl" />
          <span className="absolute left-4 top-4 rounded-pill bg-bg/95 px-3 py-1 text-caption font-semibold shadow-sm">{count}</span>
          <span className="absolute bottom-4 right-4 inline-flex h-11 items-center gap-2 rounded-pill bg-primary px-5 text-small font-semibold text-primary-fg shadow-md transition-[opacity,transform] duration-300 ease-brand md:translate-y-2 md:opacity-0 md:group-hover:translate-y-0 md:group-hover:opacity-100 md:group-focus-visible:translate-y-0 md:group-focus-visible:opacity-100">
            {cta}<ArrowRight aria-hidden className="size-4" />
          </span>
        </div>
        <h3 className="mt-5 font-heading-set text-h4 underline-offset-4 group-hover:underline">{name}</h3>
        <p className="mt-1 text-small text-muted text-pretty">{desc}</p>
      </a>
    );
  }
  return (
    <a href="#" className={cn("group relative block overflow-hidden rounded-media", className)}>
      <Media ratio={ratio} subject={subject} src={src} tone={tone} label={name} className={cn("transition-shadow duration-500 ease-brand group-hover:shadow-xl", mediaClass)} />
      <div className="absolute inset-x-3 bottom-3 rounded-card bg-bg/95 p-5 shadow-md backdrop-blur transition-transform duration-500 ease-brand md:group-hover:-translate-y-1">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0">
            <h3 className="font-heading-set text-h4 text-balance">{name}</h3>
            <p className="mt-0.5 text-small text-muted">{count}</p>
          </div>
          <span aria-hidden className="grid size-11 shrink-0 place-items-center rounded-pill border border-border transition-[background-color,color,border-color,transform] duration-300 ease-brand group-hover:rotate-45 group-hover:border-primary group-hover:bg-primary group-hover:text-primary-fg group-focus-visible:bg-primary group-focus-visible:text-primary-fg">
            <ArrowUpRight className="size-4" />
          </span>
        </div>
        {/* Reveal: open on touch, expands on hover or keyboard focus where a pointer exists. */}
        <div className="grid grid-rows-[1fr] transition-[grid-template-rows] duration-500 ease-brand md:grid-rows-[0fr] md:group-hover:grid-rows-[1fr] md:group-focus-visible:grid-rows-[1fr]">
          <div className="overflow-hidden">
            <p className="pt-3 text-small text-muted text-pretty">{desc}</p>
            <p className="hidden pt-3 text-small font-semibold underline underline-offset-4 md:block">{cta}</p>
          </div>
        </div>
      </div>
    </a>
  );
}

function CollectionGrid({ node, columns }: NodeProps) {
  const variant = variantOf(node, "three_up");
  const names = listProp(node, "collections", COLLECTIONS);
  const counts = listProp(node, "counts", ["24 products", "12 products", "9 products", "16 products", "31 products"]);
  const descs = listProp(node, "descriptions", ["The pieces we are known for.", "Here for the season, then gone.", "Light, crisp, made for warm days.", "Wrapped and ready to give.", "The staples, done properly."]);
  const media = listProp(node, "media", COLLECTION_SUBJECTS);
  const cta = prop(node, "tile_cta", "Shop the collection");
  const title = prop(node, "title", "Shop by collection");
  const tile = (i: number, ratio: string, className?: string, mediaClass?: string, below?: boolean) => (
    <CollectionTile key={i} below={below} name={names[i]} count={at(counts, i, "")} desc={at(descs, i, "")} cta={cta} tone={i}
      subject={subjectOf(at(media, i, "bag"), COLLECTION_SUBJECTS[i % 5])} src={imageAt(node, "media", i)?.url} ratio={ratio} className={className} mediaClass={mediaClass} />);
  const header = (
    <SectionHeader eyebrow={prop(node, "eyebrow", "Collections")} title={title}
      body={prop(node, "subtitle", "Find your way in — each collection is curated around a moment in the day.")}
      action={<Button variant="link" arrow>{prop(node, "cta", "All collections")}</Button>} />
  );

  if (variant === "asymmetric") {
    return (
      <Section label={title} wide>
        {header}
        <div className="grid gap-5 lg:grid-cols-12 lg:grid-rows-2">
          {names[0] && tile(0, "4/5", "lg:col-span-7 lg:row-span-2", "lg:h-full lg:aspect-auto!")}
          {names.slice(1, 3).map((_, k) => tile(k + 1, "4/3", "lg:col-span-5"))}
        </div>
      </Section>
    );
  }
  if (variant === "carousel") {
    return (
      <Section label={title} className="overflow-hidden">
        {header}
        <Carousel label={title}>{names.map((_, i) => <div key={i} className="w-[72vw] sm:w-[40vw] lg:w-[320px]">{tile(i, "3/4", undefined, undefined, true)}</div>)}</Carousel>
      </Section>
    );
  }
  const items = names.slice(0, Math.max(3, columns ?? 3));
  const odd = items.length % 2 === 1;
  return (
    <Section label={title}>
      {header}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-[repeat(var(--cols),minmax(0,1fr))]" style={{ ["--cols" as string]: columns ?? Math.min(3, items.length) }}>
        {items.map((_, i) => tile(i, "4/5", cn(odd && i === 0 && "sm:max-lg:col-span-2"), cn(odd && i === 0 && "sm:max-lg:aspect-[16/9]!")))}
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ promo banner */
function PromoBanner({ node }: NodeProps) {
  const variant = variantOf(node);
  const headline = prop(node, "headline", "The spring collection has arrived");
  const offer = prop(node, "offer", "20% off");
  const offerNote = prop(node, "offer_note", "everything in the new season edit");
  const code = prop(node, "code", "SPRING20");
  const countdown = prop(node, "countdown", "Ends Sunday at midnight");
  const cta = prop(node, "cta", "Shop the edit");
  const subject = subjectOf(prop(node, "media", ""), "leaf");
  const src = imageAt(node, "media")?.url;
  const codePill = code && (
    <span className="inline-flex items-center gap-2 rounded-pill border border-dashed border-current/40 px-4 py-2 text-small">
      Use code <span className="font-semibold tracking-[0.12em]">{code}</span>
    </span>
  );
  const timer = countdown && (
    <span className="inline-flex items-center gap-2 text-small font-medium"><Clock aria-hidden className="size-4" />{countdown}</span>
  );

  if (variant === "strip") {
    return (
      <Section label="Promotion" tone="accent" size="none" className="py-3">
        <div className="flex flex-col items-center justify-center gap-x-6 gap-y-2 text-center sm:flex-row">
          <p className="flex items-center gap-2 text-small font-semibold"><Sparkles aria-hidden className="size-4 shrink-0" />{offer} {offerNote}</p>
          <span aria-hidden className="hidden opacity-50 sm:inline">·</span>
          {timer}
          <a href="#" className="inline-flex min-h-11 items-center gap-1 text-small font-semibold underline underline-offset-4 hover:no-underline">{cta}<ArrowRight aria-hidden className="size-3.5" /></a>
        </div>
      </Section>
    );
  }
  const copy = (
    <div className="flex flex-col items-start gap-5">
      <Eyebrow>{prop(node, "eyebrow", "Limited time")}</Eyebrow>
      <h2 className="font-heading-set text-h1 text-balance">{headline}</h2>
      <p className="flex flex-wrap items-baseline gap-x-3"><span className="font-heading-set text-display leading-none">{offer}</span><span className="text-lead text-muted">{offerNote}</span></p>
      <p className="max-w-md text-muted text-pretty">{prop(node, "body", "Fresh arrivals, gift-ready sets and a few rare finds — only while the season lasts.")}</p>
      <div className="flex flex-wrap items-center gap-3">{codePill}{timer}</div>
      <Button size="lg" arrow className="mt-2">{cta}</Button>
    </div>
  );
  if (variant === "overlay") {
    return (
      <section aria-label="Promotion" className="relative isolate page-x py-10 md:py-24">
        <Media ratio="auto" subject={subject} src={src} label={prop(node, "media_label", "Seasonal campaign")} zoom={false} className="!absolute inset-0 -z-10 h-full rounded-none" />
        <div className="container-page flex md:justify-end">
          <div className="w-full max-w-xl rounded-lg bg-bg/95 p-8 shadow-xl backdrop-blur md:p-12">{copy}</div>
        </div>
      </section>
    );
  }
  return (
    <Section label="Promotion" size="sm">
      <div className="tone-inverse grid overflow-hidden rounded-lg lg:grid-cols-2">
        <div className="p-8 sm:p-12 lg:p-16">{copy}</div>
        <Media ratio="4/3" subject={subject} src={src} label={prop(node, "media_label", "Seasonal campaign")} className="rounded-none lg:h-full lg:aspect-auto!" />
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ product customizer */
function ProductCustomizer({ node }: NodeProps) {
  const variant = variantOf(node);
  const base = prop(node, "base_price", "$4.50");
  const cur = currencyOf(base);
  const nums = (key: string, fb: string[]) => listProp(node, key, fb).map(money);
  const sizes = optionsOf(node, "sizes", ["Small", "Medium", "Large"]);
  const sizeD = nums("size_prices", ["0", "0.60", "1.10"]);
  const temps = optionsOf(node, "temperatures", ["Hot", "Iced"]);
  const milks = optionsOf(node, "milks", ["Whole", "Oat", "Almond", "No milk"]);
  const milkD = nums("milk_prices", ["0", "0.70", "0.70", "0"]);
  const sweet = optionsOf(node, "sweetness", ["None", "Light", "Classic", "Extra"]);
  const extras = optionsOf(node, "extras", ["Extra shot", "Vanilla", "Cold foam", "Cinnamon"]);
  const extraD = nums("extra_prices", ["0.90", "0.60", "0.80", "0"]);
  const [size, setSize] = useState([sizes[1] ?? sizes[0]]);
  const [temp, setTemp] = useState([temps[0]]);
  const [milk, setMilk] = useState([milks[1] ?? milks[0]]);
  const [sw, setSw] = useState([sweet[1] ?? sweet[0]]);
  const [ex, setEx] = useState<string[]>([extras[0]].filter(Boolean));
  const [qty, setQty] = useState(1);
  const delta = (opts: string[], ds: number[], v: string[]) => v.reduce((s, x) => s + (ds[opts.indexOf(x)] ?? 0), 0);
  const unit = money(base) + delta(sizes, sizeD, size) + delta(milks, milkD, milk) + delta(extras, extraD, ex);
  const title = prop(node, "title", "Build your drink");
  const productName = prop(node, "product_name", "House Latte");
  const cta = `${prop(node, "primary_cta", "Add to order")} · ${fmt(unit * qty, cur)}`;
  const subject = subjectOf(prop(node, "media", ""), temp[0]?.toLowerCase().includes("ice") ? "glass" : "cup");
  const src = imageAt(node, "media")?.url;

  const groups = [
    sizes.length > 0 && { key: "size", label: prop(node, "size_label", "Size"), options: sizes, value: size, set: setSize, deltas: sizeD },
    temps.length > 0 && { key: "temp", label: prop(node, "temperature_label", "Temperature"), options: temps, value: temp, set: setTemp },
    milks.length > 0 && { key: "milk", label: prop(node, "milk_label", "Milk"), options: milks, value: milk, set: setMilk, deltas: milkD },
    sweet.length > 0 && { key: "sweet", label: prop(node, "sweetness_label", "Sweetness"), options: sweet, value: sw, set: setSw },
    extras.length > 0 && { key: "extras", label: prop(node, "extras_label", "Extras"), options: extras, value: ex, set: setEx, deltas: extraD, multiple: true },
  ].filter(Boolean) as { key: string; label: string; options: string[]; value: string[]; set: (v: string[]) => void; deltas?: number[]; multiple?: boolean }[];
  const renderGroup = (g: (typeof groups)[number], i: number, stepped?: boolean) => (
    <OptionGroup key={g.key} label={g.label} options={g.options} value={g.value} onChange={g.set} deltas={g.deltas} cur={cur} multiple={g.multiple} step={stepped ? i + 1 : undefined} />);
  const choices = [...size, ...temp, ...milk, ...sw].filter(Boolean).join(" · ");
  const summary = (withMedia?: boolean) => (
    <div className="space-y-5">
      <div className="flex items-center gap-4">
        {withMedia && <Media ratio="1/1" subject={subject} src={src} tone={1} label={productName} zoom={false} className="w-16 shrink-0 rounded-sm" />}
        <div className="min-w-0">
          <p className="text-caption font-semibold uppercase tracking-[0.14em] text-muted">{prop(node, "summary_label", "Your order")}</p>
          <p className="font-heading-set text-h4">{productName}</p>
        </div>
      </div>
      <p className="text-small text-muted text-pretty" aria-live="polite">{choices}{ex.length ? ` · ${ex.join(", ")}` : ""}</p>
      <div className="flex items-baseline justify-between gap-4 border-t border-border pt-4">
        <span className="text-small text-muted">{fmt(unit, cur)} each</span>
        <span className="font-heading-set text-h3 tabular-nums" aria-live="polite">{fmt(unit * qty, cur)}</span>
      </div>
      <div className="flex gap-3">
        <Stepper value={qty} onChange={setQty} />
        <Button size="lg" className="min-w-0 flex-1 px-4">{cta}</Button>
      </div>
    </div>
  );
  const head = (center?: boolean) => (
    <div className={cn("space-y-4", center && "mx-auto max-w-2xl text-center")}>
      <Eyebrow>{prop(node, "eyebrow", "Made your way")}</Eyebrow>
      <h2 className="font-heading-set text-h2 text-balance">{title}</h2>
      <p className="text-lead text-muted text-pretty">{prop(node, "description", "Choose every detail. We prepare it fresh the moment you order.")}</p>
    </div>
  );

  if (variant === "stepped") {
    return (
      <Section label={title} tone="surface">
        {head(true)}
        <div className="mt-12 grid gap-8 lg:grid-cols-12">
          <ol className="divide-y divide-border rounded-lg border border-border bg-bg lg:col-span-8">
            {groups.map((g, i) => <li key={g.key} className="p-6 sm:p-8">{renderGroup(g, i, true)}</li>)}
          </ol>
          <Card className="bg-bg p-6 shadow-lg sm:p-8 lg:sticky lg:top-8 lg:col-span-4 lg:self-start">{summary(true)}</Card>
        </div>
      </Section>
    );
  }
  if (variant === "compact") {
    return (
      <Section label={title} size="sm">
        <div className="mx-auto max-w-3xl overflow-hidden rounded-lg border border-border bg-surface">
          <div className="flex items-center gap-5 border-b border-border p-6">
            <Media ratio="1/1" subject={subject} src={src} tone={2} label={productName} className="w-20 shrink-0 rounded-card" />
            <div className="min-w-0 flex-1">
              <h2 className="font-heading-set text-h4">{productName}</h2>
              <p className="text-small text-muted">{prop(node, "description", "Choose every detail. We prepare it fresh the moment you order.")}</p>
            </div>
            <Price value={`from ${base}`} className="hidden text-small sm:flex" />
          </div>
          <div className="grid gap-7 p-6 md:grid-cols-2">
            {groups.map((g, i) => <div key={g.key} className={cn(g.multiple && "md:col-span-2")}>{renderGroup(g, i)}</div>)}
          </div>
          <div className="flex flex-col gap-3 border-t border-border bg-bg p-4 sm:flex-row sm:items-center sm:p-6">
            <p className="min-w-0 flex-1 truncate text-small text-muted" aria-live="polite">{choices}</p>
            <div className="flex gap-3"><Stepper value={qty} onChange={setQty} /><Button size="lg" className="flex-1 px-4 sm:flex-none">{cta}</Button></div>
          </div>
        </div>
      </Section>
    );
  }
  return (
    <Section label={title}>
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-5">
          <div className="relative lg:sticky lg:top-8">
            <Media ratio="4/5" subject={subject} src={src} tone={0} label={productName} className="shadow-lg" />
            <div className="absolute inset-x-4 bottom-4 flex items-center justify-between gap-4 rounded-card bg-bg/95 p-4 shadow-md backdrop-blur">
              <div className="min-w-0"><p className="truncate font-semibold">{productName}</p><p className="truncate text-small text-muted">{choices}</p></div>
              <span className="shrink-0 font-heading-set text-h4 tabular-nums">{fmt(unit, cur)}</span>
            </div>
          </div>
        </div>
        <div className="flex flex-col gap-8 lg:col-span-7">
          {head()}
          <div className="grid gap-7 border-t border-border pt-8">{groups.map((g, i) => renderGroup(g, i))}</div>
          <div className="rounded-lg border border-border bg-surface p-6">{summary()}</div>
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ search */
function SearchBar({ node }: NodeProps) {
  const variant = variantOf(node);
  const [q, setQ] = useState("");
  const suggestions = listProp(node, "suggestions", ["Signature blend", "Gift sets", "Seasonal edit", "Best sellers", "New arrivals", "Under $30"]);
  const [recent, setRecent] = useState(() => listProp(node, "recent", ["Morning Ritual", "Gift card", "Cold Studio"]));
  const placeholder = prop(node, "placeholder", "Search products, collections and gifts");
  const title = prop(node, "title", "What are you looking for?");
  const id = `${node.id}-q`;
  const matches = useMemo(() => (q ? suggestions.filter((s) => s.toLowerCase().includes(q.toLowerCase())) : suggestions), [q, suggestions]);
  const submit = (e: FormEvent) => e.preventDefault();

  if (variant === "inline") {
    return (
      <Section label="Search" size="none" className="py-6">
        <form role="search" onSubmit={submit} className="flex flex-col gap-4 rounded-lg border border-border bg-surface p-3 md:flex-row md:items-center">
          <SearchField id={id} label={title} placeholder={placeholder} value={q} onChange={setQ} className="md:w-[26rem]" />
          <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-1 gap-y-1 px-1">
            <span className="mr-2 inline-flex items-center gap-1.5 text-small font-semibold"><Sparkles aria-hidden className="size-4" />{prop(node, "suggestions_label", "Trending")}</span>
            {suggestions.slice(0, 4).map((s) => (
              <button key={s} type="button" onClick={() => setQ(s)} className="min-h-11 rounded-button px-3 text-small text-muted transition-colors hover:bg-fg/[0.05] hover:text-fg">{s}</button>))}
          </div>
          <Button type="submit" className="md:ml-auto">{prop(node, "cta", "Search")}</Button>
        </form>
      </Section>
    );
  }

  const bar = (
    <SearchField id={id} label={title} placeholder={placeholder} value={q} onChange={setQ} size="lg"
      action={<Button type="submit" className="h-12 rounded-pill">{prop(node, "cta", "Search")}</Button>} />
  );

  if (variant === "expanded") {
    return (
      <Section label="Search" size="sm">
        <form role="search" onSubmit={submit} className="mx-auto max-w-4xl">
          <h2 className="mb-6 font-heading-set text-h3">{title}</h2>
          {bar}
          <div className="mt-3 grid overflow-hidden rounded-lg border border-border bg-bg shadow-xl md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
            <div className="border-b border-border p-5 md:border-b-0 md:border-r">
              <p className="px-3 pb-2 text-caption font-semibold uppercase tracking-[0.14em] text-muted">{prop(node, "suggestions_label", "Suggestions")}</p>
              <ul>
                {(matches.length ? matches : suggestions).slice(0, 5).map((s) => (
                  <li key={s}><button type="button" onClick={() => setQ(s)} className="flex min-h-11 w-full items-center gap-3 rounded-button px-3 text-left transition-colors hover:bg-fg/[0.05]">
                    <Search aria-hidden className="size-4 shrink-0 text-muted" /><span className="truncate">{s}</span>
                    <ArrowUpRight aria-hidden className="ml-auto size-4 shrink-0 text-muted" /></button></li>))}
              </ul>
            </div>
            <div className="p-5">
              <p className="px-3 pb-2 text-caption font-semibold uppercase tracking-[0.14em] text-muted">{prop(node, "products_label", "Products")}</p>
              <ul>
                {range(3).map((i) => { const s = sample(i + 1); return (
                  <li key={i}><a href="#" className="flex items-center gap-4 rounded-button p-3 transition-colors hover:bg-fg/[0.05]">
                    <Media ratio="1/1" subject={s.subject} tone={i} label={s.title} zoom={false} className="w-14 shrink-0 rounded-sm" />
                    <span className="min-w-0 flex-1"><span className="block truncate font-semibold">{s.title}</span><span className="block truncate text-small text-muted">{s.note}</span></span>
                    <span className="font-semibold tabular-nums">{s.price}</span></a></li>); })}
              </ul>
              <a href="#" className="mt-2 flex min-h-11 items-center justify-center gap-2 rounded-button bg-surface text-small font-semibold transition-colors hover:bg-surface-alt">
                {prop(node, "all_results_cta", "See all results")}<ArrowRight aria-hidden className="size-4" /></a>
            </div>
          </div>
        </form>
      </Section>
    );
  }
  return (
    <Section label="Search" tone="surface">
      <form role="search" onSubmit={submit} className="mx-auto max-w-3xl text-center">
        <Eyebrow>{prop(node, "eyebrow", "Search")}</Eyebrow>
        <h2 className="mt-4 mb-8 font-heading-set text-h2 text-balance">{title}</h2>
        {bar}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
          <span className="mr-1 text-small font-semibold">{prop(node, "suggestions_label", "Popular")}</span>
          {matches.slice(0, 6).map((s) => (
            <button key={s} type="button" onClick={() => setQ(s)} className={cn(chipCls, "rounded-pill bg-bg")}>{s}</button>))}
        </div>
        {recent.length > 0 && (
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <span className="mr-1 inline-flex items-center gap-1.5 text-small text-muted"><History aria-hidden className="size-4" />{prop(node, "recent_label", "Recent")}</span>
            {recent.map((r) => (
              <span key={r} className="inline-flex items-center rounded-pill border border-border bg-bg text-small">
                <button type="button" onClick={() => setQ(r)} className="min-h-11 pl-4 pr-1 font-medium">{r}</button>
                <button type="button" aria-label={`Remove ${r} from recent searches`} onClick={() => setRecent((x) => x.filter((y) => y !== r))}
                  className="grid size-11 place-items-center rounded-pill text-muted transition-colors hover:text-fg"><X className="size-3.5" /></button>
              </span>))}
          </div>)}
      </form>
    </Section>
  );
}

/* ------------------------------------------------------------------ category hero */
function CategoryHero({ node }: NodeProps) {
  const variant = variantOf(node);
  const title = prop(node, "title", "The Signature Edit");
  const subs = listProp(node, "subcategories", ["All", "New", "Best sellers", "Limited", "Gift sets"]);
  const [active, setActive] = useState(0);
  const subject = subjectOf(prop(node, "media", ""), "bag");
  const src = imageAt(node, "media")?.url;
  const label = prop(node, "media_label", `${title} collection`);
  const crumbs = listProp(node, "breadcrumb", ["Home", "Shop"]);
  const breadcrumb = (
    <nav aria-label="Breadcrumb">
      <ol className="flex flex-wrap items-center gap-2 text-small text-muted">
        {crumbs.map((c) => <li key={c} className="flex items-center gap-2"><a href="#" className="inline-flex min-h-6 items-center hover:text-fg">{c}</a><span aria-hidden>/</span></li>)}
        <li aria-current="page" className="font-medium text-fg">{title}</li>
      </ol>
    </nav>
  );
  const desc = prop(node, "description", "Our most-loved pieces, gathered in one place. Each one refined over years and made in small batches.");
  const count = prop(node, "count", "48 products");
  const chips = (center?: boolean) => (
    <div role="group" aria-label="Sub-categories" className={cn("flex flex-wrap gap-2", center && "justify-center")}>
      {subs.map((s, i) => (
        <button key={s} type="button" aria-pressed={active === i} onClick={() => setActive(i)} className={cn(chipCls, "rounded-pill", active === i && chipOn)}>{s}</button>))}
    </div>
  );

  if (variant === "banner") {
    return (
      <Section label={title} wide size="sm">
        <div className="relative">
          <Media ratio="21/9" subject={subject} src={src} label={label} zoom={false} className="min-h-72 shadow-lg" />
          <div className="relative mx-3 -mt-16 rounded-lg bg-bg/95 p-6 shadow-xl backdrop-blur sm:mx-6 sm:p-8 md:absolute md:bottom-8 md:left-8 md:mx-0 md:mt-0 md:max-w-xl md:p-10">
            {breadcrumb}
            <h1 className="mt-4 font-heading-set text-h1 text-balance">{title}</h1>
            <p className="mt-3 text-muted text-pretty">{desc}</p>
            <p className="mt-4 text-small font-semibold">{count}</p>
          </div>
        </div>
        <div className="mt-8">{chips()}</div>
      </Section>
    );
  }
  if (variant === "minimal") {
    const thumbs: Subject[] = ["product", "bag", "leaf", "glass", "cup", "abstract"];
    return (
      <Section label={title} size="sm">
        <div className="flex flex-col items-center text-center">
          {breadcrumb}
          <h1 className="mt-6 font-heading-set text-display text-balance">{title}</h1>
          <p className="mt-5 max-w-2xl text-lead text-muted text-pretty">{desc}</p>
          <p className="mt-3 text-small text-muted">{count}</p>
        </div>
        <div role="group" aria-label="Sub-categories" className="mx-auto mt-12 flex max-w-4xl gap-5 overflow-x-auto pb-2 sm:justify-center sm:gap-8">
          {subs.map((s, i) => (
            <button key={s} type="button" aria-pressed={active === i} onClick={() => setActive(i)} className="group flex w-20 shrink-0 flex-col items-center gap-3 sm:w-24">
              <span className={cn("block w-full rounded-pill p-1 ring-2 transition-[box-shadow] duration-300", active === i ? "ring-fg" : "ring-transparent group-hover:ring-border")}>
                <Media ratio="1/1" subject={thumbs[i % thumbs.length]} tone={i} label={s} className="rounded-pill" />
              </span>
              <span className={cn("text-small", active === i ? "font-semibold" : "text-muted")}>{s}</span>
            </button>))}
        </div>
      </Section>
    );
  }
  return (
    <Section label={title} size="sm">
      <div className="grid items-center gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="flex flex-col gap-6 lg:col-span-6">
          {breadcrumb}
          <h1 className="font-heading-set text-display text-balance">{title}</h1>
          <p className="max-w-xl text-lead text-muted text-pretty">{desc}</p>
          {chips()}
        </div>
        <div className="relative lg:col-span-6">
          <Media ratio="5/4" subject={subject} src={src} label={label} className="shadow-xl" />
          <div className="absolute -bottom-5 left-5 flex items-center gap-3 rounded-card bg-bg px-5 py-3.5 shadow-lg">
            <Package aria-hidden className="size-5" />
            <div><p className="text-small font-semibold">{count}</p><p className="text-caption text-muted">{prop(node, "media_note", "New pieces added weekly")}</p></div>
          </div>
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ product spotlight */
function ProductSpotlight({ node }: NodeProps) {
  const variant = variantOf(node);
  const title = prop(node, "title", "Nº1 Signature");
  const subject = subjectOf(prop(node, "media", ""), "bag");
  const src = imageAt(node, "media")?.url;
  const label = prop(node, "media_label", title);
  const notes = listProp(node, "notes", ["Crafted", "Character", "Origin", "Pairs with"]);
  const details = listProp(node, "note_details", ["By hand, in small batches", "Rich, rounded and quietly complex", "Responsibly sourced, fully traceable", "Slow mornings and long conversations"]);
  const price = prop(node, "price", "$24");
  const story = prop(node, "story", "Ten years in the making and still our most-requested piece. We refine it every season, but never change what makes it ours.");
  const ctas = (withPrice = true) => (
    <div className="flex flex-wrap items-center gap-3">
      <Button size="lg" arrow>{prop(node, "primary_cta", "Shop now")}{withPrice && ` · ${price}`}</Button>
      <Button size="lg" variant="secondary">{prop(node, "secondary_cta", "Read the story")}</Button>
    </div>
  );
  const eyebrow = <Eyebrow>{prop(node, "eyebrow", "In the spotlight")}</Eyebrow>;

  if (variant === "centered") {
    const half = Math.ceil(notes.length / 2);
    const note = (n: string, i: number, align: "left" | "right") => (
      <li key={n} className={cn("space-y-2 border-t border-border pt-4", align === "right" && "lg:text-right")}>
        <p className="text-caption font-semibold tabular-nums text-muted">{String(i + 1).padStart(2, "0")} — {n}</p>
        <p className="font-heading-set text-h4 text-balance">{at(details, i, "")}</p>
      </li>);
    return (
      <Section label={title} size="lg">
        <div className="mx-auto max-w-2xl space-y-5 text-center">
          {eyebrow}
          <h2 className="font-heading-set text-display text-balance">{title}</h2>
          <p className="text-lead text-muted text-pretty">{story}</p>
        </div>
        <div className="mt-14 grid items-center gap-10 lg:grid-cols-[1fr_minmax(0,1.25fr)_1fr] lg:gap-14">
          <ul className="order-2 space-y-8 lg:order-1">{notes.slice(0, half).map((n, i) => note(n, i, "right"))}</ul>
          <div className="relative order-1 lg:order-2">
            <Media ratio="3/4" subject={subject} src={src} label={label} className="shadow-xl" />
            <Badge tone="primary" className="absolute left-1/2 top-5 -translate-x-1/2 shadow-md">{prop(node, "badge", "Bestseller")}</Badge>
          </div>
          <ul className="order-3 space-y-8">{notes.slice(half).map((n, i) => note(n, i + half, "left"))}</ul>
        </div>
        <div className="mt-14 flex justify-center">{ctas()}</div>
      </Section>
    );
  }
  const dl = (cols?: boolean) => (
    <dl className={cn(cols ? "grid gap-x-8 gap-y-6 sm:grid-cols-2" : "divide-y divide-border border-y border-border")}>
      {notes.map((n, i) => (
        <div key={n} className={cn(cols ? "space-y-2 border-t border-border pt-4" : "grid gap-1 py-4 sm:grid-cols-[9rem_1fr] sm:gap-6")}>
          <dt className="text-caption font-semibold uppercase tracking-[0.14em] text-muted sm:pt-0.5">{n}</dt>
          <dd className={cn(cols && "font-heading-set text-h4")}>{at(details, i, "")}</dd>
        </div>))}
    </dl>
  );
  if (variant === "inverse") {
    return (
      <Section label={title} tone="inverse" wide>
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-20">
          <div className="flex flex-col gap-7 lg:py-8">
            {eyebrow}
            <h2 className="font-heading-set text-display text-balance">{title}</h2>
            <p className="max-w-xl text-lead text-muted text-pretty">{story}</p>
            {dl(true)}
            {ctas()}
          </div>
          <div className="relative">
            <Media ratio="1/1" subject={subject} src={src} label={label} className="shadow-xl" />
            <div className="absolute bottom-5 right-5 rounded-card bg-bg px-5 py-4 text-right shadow-lg">
              <p className="text-caption text-muted">{prop(node, "price_label", "From")}</p>
              <p className="font-heading-set text-h3 tabular-nums">{price}</p>
            </div>
          </div>
        </div>
      </Section>
    );
  }
  return (
    <Section label={title}>
      <div className="grid items-center gap-14 lg:grid-cols-12 lg:gap-16">
        <div className="relative lg:col-span-7">
          <Media ratio="4/5" subject={subject} src={src} label={label} className="shadow-xl" />
          <Media ratio="1/1" subject="leaf" tone={2} label={`${title}, detail`}
            className="absolute -bottom-8 -right-4 hidden w-44 border-4 border-bg shadow-lg sm:block lg:-right-10 lg:w-56" />
          <Badge tone="primary" className="absolute left-5 top-5 shadow-md">{prop(node, "badge", "Bestseller")}</Badge>
        </div>
        <div className="flex flex-col gap-7 lg:col-span-5">
          {eyebrow}
          <h2 className="font-heading-set text-h1 text-balance">{title}</h2>
          <p className="text-lead text-muted text-pretty">{story}</p>
          {dl()}
          <div className="flex items-center gap-4"><Price value={price} className="text-h3" /><Rating value={4.9} count={312} /></div>
          {ctas(false)}
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ subscription */
function SubscriptionOffer({ node }: NodeProps) {
  const variant = variantOf(node);
  const [plan, setPlan] = useState("subscribe");
  const title = prop(node, "title", "Subscribe and never run out");
  const discount = prop(node, "discount", "Save 15%");
  const once = prop(node, "one_time_price", "$24.00");
  const sub = prop(node, "subscribe_price", "$20.40");
  const freqs = listProp(node, "frequencies", ["Every 2 weeks", "Every month", "Every 2 months"]);
  const perks = listProp(node, "perks", ["Free delivery on every order", "Skip, pause or cancel anytime", "First access to limited releases"]);
  const plans = [
    { id: "subscribe", name: prop(node, "subscribe_label", "Subscribe & save"), price: sub, note: prop(node, "subscribe_note", "Delivered on your schedule"), badge: discount },
    { id: "once", name: prop(node, "one_time_label", "One-time purchase"), price: once, note: prop(node, "one_time_note", "No commitment"), badge: "" },
  ];
  const radios = (stacked?: boolean) => (
    <RadioGroup.Root value={plan} onValueChange={setPlan} aria-label="Purchase option" className={cn("grid gap-3", !stacked && "md:grid-cols-2 md:gap-5")}>
      {plans.map((p) => (
        <RadioGroup.Item key={p.id} value={p.id}
          className={cn("group relative flex w-full items-start gap-4 rounded-card border bg-bg p-5 text-left transition-[border-color,box-shadow,transform] duration-300 ease-brand hover:border-fg/40 active:scale-[0.99] data-[state=checked]:border-primary data-[state=checked]:shadow-md sm:p-6",
            !stacked && "md:flex-col md:p-8", "border-border")}>
          <span aria-hidden className="mt-0.5 grid size-5 shrink-0 place-items-center rounded-pill border-2 border-border transition-colors group-data-[state=checked]:border-primary">
            <RadioGroup.Indicator className="size-2.5 rounded-pill bg-primary" />
          </span>
          <span className={cn("min-w-0 flex-1", !stacked && "md:flex-none")}>
            <span className="flex flex-wrap items-center gap-2"><span className="font-semibold">{p.name}</span>{p.badge && <Badge tone="accent">{p.badge}</Badge>}</span>
            <span className="mt-1 block text-small text-muted">{p.note}</span>
          </span>
          <span className={cn("shrink-0 text-right", !stacked && "md:text-left")}>
            <span className={cn("block font-heading-set tabular-nums", stacked ? "text-h4" : "text-h3")}>{p.price}</span>
            {p.id === "subscribe" && <span className="block text-small text-muted line-through tabular-nums">{once}</span>}
          </span>
        </RadioGroup.Item>))}
    </RadioGroup.Root>
  );
  const freq = (
    <div className={cn("transition-opacity duration-300", plan !== "subscribe" && "pointer-events-none opacity-40")} aria-disabled={plan !== "subscribe"}>
      <ChoiceChips label={prop(node, "frequency_label", "Deliver")} options={freqs} initial={freqs[1] ?? freqs[0]} />
    </div>
  );
  const perkList = (
    <ul className="grid gap-3">
      {perks.map((p) => <li key={p} className="flex items-center gap-3"><span className="grid size-6 shrink-0 place-items-center rounded-pill bg-primary text-primary-fg"><Check aria-hidden className="size-3.5" /></span>{p}</li>)}
    </ul>
  );
  const cta = <Button size="lg" arrow className="w-full sm:w-auto">{plan === "subscribe" ? prop(node, "primary_cta", "Start my subscription") : prop(node, "secondary_cta", "Add to cart")}</Button>;

  if (variant === "split") {
    return (
      <Section label={title} tone="surface">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          <div className="relative">
            <Media ratio="4/5" subject={subjectOf(prop(node, "media", ""), "bag")} src={imageAt(node, "media")?.url} label={prop(node, "media_label", "Subscription box")} className="shadow-xl" />
            <div className="absolute left-5 top-5 flex items-center gap-2 rounded-pill bg-bg px-4 py-2 text-small font-semibold shadow-md"><Repeat aria-hidden className="size-4" />{discount} on every delivery</div>
          </div>
          <div className="flex flex-col gap-8">
            <div className="space-y-4">
              <Eyebrow>{prop(node, "eyebrow", "Subscription")}</Eyebrow>
              <h2 className="font-heading-set text-h2 text-balance">{title}</h2>
              <p className="text-lead text-muted text-pretty">{prop(node, "body", "Your favourites, delivered on your schedule — at their freshest and for less.")}</p>
            </div>
            {radios(true)}
            {freq}
            {perkList}
            <div className="flex flex-wrap items-center gap-4">{cta}<p className="text-small text-muted">{prop(node, "fine_print", "Cancel anytime in two clicks.")}</p></div>
          </div>
        </div>
      </Section>
    );
  }
  return (
    <Section label={title}>
      <SectionHeader align="center" eyebrow={prop(node, "eyebrow", "Subscription")} title={title}
        body={prop(node, "body", "Your favourites, delivered on your schedule — at their freshest and for less.")} />
      <div className="mx-auto max-w-4xl">
        {radios()}
        <div className="mt-8 grid gap-8 rounded-lg bg-surface p-6 sm:p-8 md:grid-cols-2 md:gap-12">
          {freq}
          {perkList}
        </div>
        <div className="mt-8 flex flex-col items-center gap-3 text-center">{cta}<p className="text-small text-muted">{prop(node, "fine_print", "Cancel anytime in two clicks.")}</p></div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ lookbook */
const SPOTS: [number, number][][] = [[[32, 30], [64, 50], [42, 68]], [[58, 42]]];

function Hotspot({ id, x, y, product, open, onToggle }: {
  id: string; x: number; y: number; product: (typeof SAMPLE_PRODUCTS)[number]; open: boolean; onToggle: () => void;
}) {
  return (
    <>
      <button type="button" aria-expanded={open} aria-controls={id} aria-label={`${open ? "Hide" : "Show"} ${product.title}`} onClick={onToggle}
        className="absolute z-10 grid size-11 -translate-x-1/2 -translate-y-1/2 place-items-center rounded-pill bg-bg/95 text-fg shadow-lg transition-transform duration-300 ease-brand hover:scale-110 active:scale-95"
        style={{ left: `${x}%`, top: `${y}%` }}>
        {!open && <span aria-hidden className="absolute inset-0 rounded-pill bg-bg/60 motion-safe:animate-ping" />}
        <Plus className={cn("relative size-4 transition-transform duration-300 ease-brand", open && "rotate-45")} />
      </button>
      {open && (
        <div id={id} className="absolute inset-x-3 bottom-3 z-20 flex items-center gap-3 rounded-card bg-bg p-3 shadow-xl sm:inset-x-auto sm:left-4 sm:w-80">
          <Media ratio="1/1" subject={product.subject} tone={3} label={product.title} zoom={false} className="w-14 shrink-0 rounded-sm" />
          <div className="min-w-0 flex-1"><p className="truncate font-semibold">{product.title}</p><p className="text-small tabular-nums text-muted">{product.price}</p></div>
          <Button size="icon" variant="primary" aria-label={`Add ${product.title} to cart`}><Plus className="size-4" /></Button>
        </div>)}
    </>
  );
}

function Lookbook({ node }: NodeProps) {
  const variant = variantOf(node, "hotspots");
  const title = prop(node, "title", "The season, styled");
  const looks = listProp(node, "looks", ["Slow Sunday", "Studio hours", "Golden afternoon", "The long table"]);
  const captions = listProp(node, "captions", ["Everything you need for an unhurried morning.", "Quiet tools for focused days.", "Light, bright and made to share.", "Set for friends, and for lingering."]);
  const productNames = listProp(node, "products", SAMPLE_PRODUCTS.map((p) => p.title as string));
  const prices = listProp(node, "prices", []);
  const product = (i: number) => ({ ...sample(i), title: at(productNames, i, sample(i).title), price: at(prices, i, sample(i).price) });
  const [open, setOpen] = useState<string | null>("0-0");
  const header = (
    <SectionHeader eyebrow={prop(node, "eyebrow", "Lookbook")} title={title}
      body={prop(node, "subtitle", "Pieces from the collection, shown the way we live with them.")}
      action={<Button variant="link" arrow>{prop(node, "cta", "Shop the lookbook")}</Button>} />
  );

  if (variant === "captions") {
    const subjects: Subject[] = ["space", "cup", "leaf", "glass"];
    return (
      <Section label={title} wide>
        {header}
        <div className="grid gap-x-6 gap-y-12 sm:grid-cols-2 lg:grid-cols-4">
          {looks.slice(0, 4).map((l, i) => (
            <figure key={l} className={cn("group", i % 2 === 1 && "lg:mt-20")}>
              <Media ratio={i % 2 ? "3/4" : "4/5"} subject={subjects[i % 4]} tone={i} label={l} className="transition-shadow duration-500 ease-brand group-hover:shadow-xl" />
              <figcaption className="mt-5 space-y-2">
                <p className="text-caption font-semibold tabular-nums text-muted">Look {String(i + 1).padStart(2, "0")}</p>
                <h3 className="font-heading-set text-h4">{l}</h3>
                <p className="text-small text-muted text-pretty">{at(captions, i, "")}</p>
                <a href="#" className="inline-flex min-h-11 items-center gap-1.5 text-small font-semibold underline-offset-4 hover:underline">
                  {product(i).title} · {product(i).price}<ArrowRight aria-hidden className="size-3.5 transition-transform duration-200 group-hover:translate-x-0.5" /></a>
              </figcaption>
            </figure>))}
        </div>
      </Section>
    );
  }
  const toggle = (k: string) => setOpen((o) => (o === k ? null : k));
  return (
    <Section label={title} wide>
      {header}
      <div className="grid gap-5 lg:grid-cols-12">
        <div className="lg:col-span-7">
          <Media ratio="4/5" subject="space" tone={0} zoom={false} label={`${at(looks, 0, "Look")}, styled scene`} className="h-full lg:aspect-auto!">
            {SPOTS[0].map(([x, y], k) => (
              <Hotspot key={k} id={`${node.id}-spot-0-${k}`} x={x} y={y} product={product(k)} open={open === `0-${k}`} onToggle={() => toggle(`0-${k}`)} />))}
          </Media>
        </div>
        <div className="flex flex-col gap-5 lg:col-span-5">
          <Media ratio="1/1" subject="cup" tone={2} zoom={false} label={`${at(looks, 1, "Look")}, styled scene`}>
            {SPOTS[1].map(([x, y], k) => (
              <Hotspot key={k} id={`${node.id}-spot-1-${k}`} x={x} y={y} product={product(k + 3)} open={open === `1-${k}`} onToggle={() => toggle(`1-${k}`)} />))}
          </Media>
          <div className="flex flex-1 flex-col justify-between gap-6 rounded-media bg-surface p-6 sm:p-8">
            <div className="space-y-3">
              <p className="text-caption font-semibold uppercase tracking-[0.14em] text-muted">Look 01</p>
              <h3 className="font-heading-set text-h3">{at(looks, 0, "Slow Sunday")}</h3>
              <p className="text-muted text-pretty">{at(captions, 0, "")}</p>
            </div>
            <ul className="divide-y divide-border border-t border-border">
              {range(3).map((k) => (
                <li key={k} className="flex items-center justify-between gap-4 py-3 text-small">
                  <span className="font-medium">{product(k).title}</span><span className="tabular-nums text-muted">{product(k).price}</span>
                </li>))}
            </ul>
            <Button variant="primary" arrow className="self-start">{prop(node, "look_cta", "Shop this look")}</Button>
          </div>
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ menu */
type MenuItem = { name: string; desc: string; price: string; tags: string[]; badge?: string };
const MENU: MenuItem[][] = [
  [
    { name: "Espresso", desc: "Double shot of the house blend, chocolate and stone fruit.", price: "$3.50", tags: ["VG"] },
    { name: "Flat white", desc: "Silky microfoam over a ristretto double.", price: "$4.50", tags: ["V"] },
    { name: "Cortado", desc: "Equal parts espresso and warm milk.", price: "$4.20", tags: ["V"] },
    { name: "Honey lavender latte", desc: "Wildflower honey, dried lavender, oat milk.", price: "$5.60", tags: ["VG", "DF"], badge: "Seasonal" },
  ],
  [
    { name: "Ceremonial matcha", desc: "Stone-ground Uji matcha, whisked to order.", price: "$5.20", tags: ["VG", "GF"] },
    { name: "Jasmine pearls", desc: "Hand-rolled green tea, floral and sweet.", price: "$4.80", tags: ["VG", "GF"] },
    { name: "Masala chai", desc: "House spice blend simmered with black tea.", price: "$4.90", tags: ["V", "GF"] },
    { name: "Aged oolong", desc: "Roasted, honeyed and long on the finish.", price: "$5.40", tags: ["VG", "GF"], badge: "New" },
  ],
  [
    { name: "Cold brew", desc: "Steeped for 18 hours, served over clear ice.", price: "$4.80", tags: ["VG", "GF"] },
    { name: "Yuzu tonic espresso", desc: "Espresso over yuzu and tonic, bright and bitter.", price: "$5.80", tags: ["VG", "GF"], badge: "Signature" },
    { name: "Iced hojicha latte", desc: "Roasted green tea, milk of your choice.", price: "$5.20", tags: ["V"] },
    { name: "Sparkling hibiscus", desc: "Hibiscus, citrus peel and soda.", price: "$4.50", tags: ["VG", "GF"] },
  ],
  [
    { name: "Butter croissant", desc: "Laminated over three days, baked each morning.", price: "$4.00", tags: ["V"] },
    { name: "Cardamom bun", desc: "Swedish-style knot, pearl sugar.", price: "$4.50", tags: ["V"] },
    { name: "Olive oil cake", desc: "Citrus, almond, a little salt.", price: "$5.00", tags: ["GF", "DF"] },
    { name: "Seasonal fruit tart", desc: "Pastry cream and whatever is best this week.", price: "$6.00", tags: ["V"] },
  ],
];
const TAGS: Record<string, string> = { V: "Vegetarian", VG: "Vegan", GF: "Gluten free", DF: "Dairy free" };

function DietTags({ tags }: { tags: string[] }) {
  return (
    <span className="inline-flex gap-1">
      {tags.map((t) => (
        <abbr key={t} title={TAGS[t] ?? t} className="inline-grid h-5 min-w-5 place-items-center rounded-sm border border-border px-1 text-caption font-semibold text-muted no-underline">{t}</abbr>))}
    </span>
  );
}

function MenuList({ node }: NodeProps) {
  const variant = variantOf(node);
  const groups = listProp(node, "groups", ["Espresso bar", "Tea house", "Cold drinks", "From the oven"]);
  const title = prop(node, "title", "The menu");
  const note = prop(node, "note", "Oat, almond and whole milk at no extra charge. Ask us about allergens.");
  const items = (i: number) => MENU[i % MENU.length];
  const legend = (
    <div className="mt-14 flex flex-col gap-4 border-t border-border pt-6 text-small text-muted md:flex-row md:items-center md:justify-between">
      <dl className="flex flex-wrap gap-x-5 gap-y-2">
        {Object.entries(TAGS).map(([k, v]) => <div key={k} className="flex items-center gap-2"><dt><DietTags tags={[k]} /></dt><dd>{v}</dd></div>)}
      </dl>
      <p>{note}</p>
    </div>
  );

  if (variant === "tabs") {
    const subjects: Subject[] = ["cup", "leaf", "glass", "product"];
    return (
      <Section label={title} tone="surface">
        <SectionHeader eyebrow={prop(node, "eyebrow", "Menu")} title={title} body={prop(node, "subtitle", "Made to order, all day.")} />
        <Tabs label="Menu sections" tabs={groups.map((g, gi) => ({ id: `g${gi}`, label: g, content: (
          <ul className="grid gap-4 md:grid-cols-2">
            {items(gi).map((it, k) => (
              <li key={it.name} className="group flex gap-4 rounded-card border border-border bg-bg p-4 transition-[border-color,box-shadow] duration-300 ease-brand hover:border-fg/20 hover:shadow-md">
                <Media ratio="1/1" subject={subjects[gi % 4]} tone={k} label={it.name} className="w-20 shrink-0 rounded-sm sm:w-24" />
                <div className="min-w-0 flex-1 space-y-1.5">
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="font-semibold">{it.name}</h3>
                    <span className="shrink-0 font-semibold tabular-nums">{it.price}</span>
                  </div>
                  <p className="text-small text-muted text-pretty">{it.desc}</p>
                  <div className="flex flex-wrap items-center gap-2 pt-1"><DietTags tags={it.tags} />{it.badge && <Badge tone="accent">{it.badge}</Badge>}</div>
                </div>
              </li>))}
          </ul>) }))} />
        {legend}
      </Section>
    );
  }
  if (variant === "board") {
    return (
      <Section label={title} tone="inverse" wide>
        <div className="mb-12 text-center md:mb-16">
          <Eyebrow>{prop(node, "eyebrow", "Menu")}</Eyebrow>
          <h2 className="mt-4 font-heading-set text-display">{title}</h2>
        </div>
        <div className="grid gap-12 sm:grid-cols-2 lg:grid-cols-4 lg:gap-10">
          {groups.slice(0, 4).map((g, gi) => (
            <div key={g}>
              <h3 className="border-b border-border pb-3 text-caption font-semibold uppercase tracking-[0.18em]">{g}</h3>
              <ul className="mt-2">
                {items(gi).map((it) => (
                  <li key={it.name} className="flex items-baseline justify-between gap-4 border-b border-border/60 py-3">
                    <span className="min-w-0"><span className="block font-medium">{it.name}</span>{it.badge && <span className="text-caption text-muted">{it.badge}</span>}</span>
                    <span className="shrink-0 tabular-nums">{it.price}</span>
                  </li>))}
              </ul>
            </div>))}
        </div>
        <p className="mt-12 text-center text-small text-muted">{note}</p>
      </Section>
    );
  }
  return (
    <Section label={title}>
      <SectionHeader eyebrow={prop(node, "eyebrow", "Menu")} title={title} body={prop(node, "subtitle", "Made to order, all day. Everything on the bar is available hot or iced.")} />
      <div className="grid gap-x-16 gap-y-14 md:grid-cols-2">
        {groups.map((g, gi) => (
          <div key={g}>
            <div className="flex items-baseline justify-between gap-4 border-b border-fg pb-3">
              <h3 className="font-heading-set text-h3">{g}</h3>
              <span className="text-caption tabular-nums text-muted">{String(gi + 1).padStart(2, "0")}</span>
            </div>
            <ul className="mt-2">
              {items(gi).map((it) => (
                <li key={it.name} className="py-4">
                  <div className="flex items-baseline gap-3">
                    <span className="font-semibold">{it.name}</span>
                    {it.badge && <Badge tone="accent" className="self-center">{it.badge}</Badge>}
                    <span aria-hidden className="min-w-6 flex-1 translate-y-[-0.25em] border-b border-dotted border-fg/30" />
                    <span className="font-semibold tabular-nums">{it.price}</span>
                  </div>
                  <div className="mt-1 flex items-start justify-between gap-4">
                    <p className="text-small text-muted text-pretty">{it.desc}</p>
                    <DietTags tags={it.tags} />
                  </div>
                </li>))}
            </ul>
          </div>))}
      </div>
      {legend}
    </Section>
  );
}

export const SECTIONS: SectionMap = {
  ProductCard, ProductGrid, ProductDetail, TrustSignals, Reviews, RelatedProducts, ProductFilters, CartItems, OrderSummary,
  CollectionGrid, PromoBanner, ProductCustomizer, SearchBar, CategoryHero, ProductSpotlight, SubscriptionOffer, Lookbook, MenuList,
};
