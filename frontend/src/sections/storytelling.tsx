/** storytelling sections. Keys are the catalog's implementation.root names. See sections/README.md. */
import { useState } from "react";
import {
  ArrowRight, AtSign, Check, Clock, Compass, Globe, Mail, PackageCheck, Pause, Play, Quote, RefreshCw, Sparkles, X,
  type LucideIcon,
} from "lucide-react";
import { Badge, Button, Eyebrow, Marquee, Media, Rating, Section, SectionHeader, Tabs, imageAt, listProp, prop, subjectOf, variantOf, type Subject } from "../ui";
import { cn } from "../lib/cn";
import type { NodeProps, SectionMap } from "./types";

/** Item i of a list slot, cycling so parallel lists of different lengths never render empty. */
const at = (list: string[], i: number) => list[i % list.length];
const pad2 = (i: number) => String(i + 1).padStart(2, "0");

/* ------------------------------------------------------------------ testimonial_spotlight */
function Attribution({ name, role, company, align = "start" }: { name: string; role: string; company: string; align?: "start" | "center" }) {
  return (
    <figcaption className={cn("flex flex-wrap items-center gap-x-5 gap-y-3", align === "center" && "justify-center text-center")}>
      <div>
        <p className="font-semibold">{name}</p>
        <p className="text-small text-muted">{role}</p>
      </div>
      {company && (
        <>
          <span aria-hidden className="hidden h-8 w-px bg-border sm:block" />
          <p className="font-heading-set text-h4 italic tracking-tight">{company}</p>
        </>
      )}
    </figcaption>
  );
}

function TestimonialSpotlight({ node }: NodeProps) {
  const variant = variantOf(node, "split");
  const quote = prop(node, "quote", "They treat every detail as if it were the only one. Three years on, it is still the first thing our guests ask about.");
  const name = prop(node, "name", "Amara Okafor");
  const role = prop(node, "role", "Founder and owner");
  const company = prop(node, "company", "Maison Okafor");
  const rating = Number.parseFloat(prop(node, "rating", "5")) || 5;
  const subject = subjectOf(prop(node, "media", ""), "person");
  const src = imageAt(node, "media")?.url;
  const label = prop(node, "media_label", `Portrait of ${name}`);
  const eyebrow = prop(node, "eyebrow", "In their words");

  if (variant === "centered") {
    return (
      <Section label="Testimonial" tone="surface" size="lg">
        <figure className="mx-auto flex max-w-4xl flex-col items-center text-center">
          <Rating value={rating} />
          <blockquote className="mt-8 font-heading-set text-h3 text-balance md:text-h2">“{quote}”</blockquote>
          <Media ratio="1/1" subject={subject} src={src} tone={1} label={label} zoom={false}
            className="mt-10 w-20 rounded-pill border-4 border-bg shadow-md" />
          <div className="mt-5"><Attribution name={name} role={role} company="" align="center" /></div>
          {company && <p className="mt-6 text-caption font-semibold uppercase tracking-[0.24em] text-muted">{company}</p>}
        </figure>
      </Section>
    );
  }
  if (variant === "editorial") {
    // Inverse band: an oversized accent quote mark hangs in the margin, the quote runs across eight
    // columns and a small portrait anchors the attribution at the lower right.
    return (
      <Section label="Testimonial" tone="inverse" size="lg">
        <figure className="grid gap-10 lg:grid-cols-12 lg:gap-12">
          <div className="lg:col-span-1">
            <Quote aria-hidden className="size-12 -scale-x-100 fill-current text-accent md:size-16" strokeWidth={0} />
          </div>
          <div className="lg:col-span-8">
            <Eyebrow>{eyebrow}</Eyebrow>
            <blockquote className="mt-6 font-heading-set text-h2 text-balance md:text-h1">{quote}</blockquote>
            <div className="mt-10 border-t border-border pt-8"><Attribution name={name} role={role} company={company} /></div>
          </div>
          <div className="flex items-end lg:col-span-3">
            <Media ratio="3/4" subject={subject} src={src} tone={2} label={label} className="max-w-40 shadow-xl sm:max-w-56 lg:max-w-none" />
          </div>
        </figure>
      </Section>
    );
  }
  return (
    <Section label="Testimonial" size="lg">
      <figure className="grid items-center gap-10 md:grid-cols-12 lg:gap-16">
        <div className="relative md:col-span-5">
          <Media ratio="4/5" subject={subject} src={src} tone={0} label={label} className="shadow-xl" />
          <div className="absolute -bottom-5 right-5 rounded-card bg-bg px-5 py-4 shadow-lg">
            <Rating value={rating} />
            <p className="mt-1 text-caption text-muted">{prop(node, "rating_note", "Verified customer since 2021")}</p>
          </div>
        </div>
        <div className="md:col-span-7 md:pl-4">
          <Eyebrow>{eyebrow}</Eyebrow>
          <Quote aria-hidden className="mt-8 size-10 -scale-x-100 fill-current text-accent" strokeWidth={0} />
          <blockquote className="mt-4 font-heading-set text-h3 text-balance lg:text-h2">{quote}</blockquote>
          <div className="mt-10"><Attribution name={name} role={role} company={company} /></div>
        </div>
      </figure>
    </Section>
  );
}

/* ------------------------------------------------------------------ press_quotes */
/** Wordmark stand-ins: each publication gets its own typographic treatment, like real mastheads. */
const MASTHEADS = [
  "font-heading-set text-h4 italic",
  "text-small font-bold uppercase tracking-[0.3em]",
  "font-heading-set text-h4 font-semibold tracking-tight",
  "text-body font-semibold uppercase tracking-[0.12em]",
  "font-heading-set text-h4",
];

function PressQuotes({ node }: NodeProps) {
  const variant = variantOf(node, "grid");
  const quotes = listProp(node, "quotes", [
    "Quietly the most considered name in town",
    "Obsessive about detail in the best possible way",
    "The rare place that gets better every visit",
    "Set a new standard for the whole category",
  ]);
  const pubs = listProp(node, "publications", ["The Weekend Review", "KINFOLK HOUSE", "Monocle Notes", "Design Daily", "The Standard"]);
  const eyebrow = prop(node, "eyebrow", "As seen in");

  if (variant === "marquee") {
    return (
      <Section label="Press" tone="surface" size="sm" wide>
        <Eyebrow className="mb-8 text-center">{eyebrow}</Eyebrow>
        <Marquee speed={55}>
          {quotes.map((q, i) => (
            <figure key={i} className="flex shrink-0 items-center gap-5">
              <blockquote className="font-heading-set text-h4 whitespace-nowrap">“{q}”</blockquote>
              <figcaption className={cn("whitespace-nowrap text-muted", MASTHEADS[(i + 1) % MASTHEADS.length])}>{at(pubs, i)}</figcaption>
              <span aria-hidden className="ml-7 size-1.5 rounded-pill bg-accent" />
            </figure>))}
        </Marquee>
      </Section>
    );
  }
  const shown = quotes.slice(0, 3);
  return (
    <Section label="Press">
      <div className="mb-12 flex flex-wrap items-baseline justify-between gap-4 border-b border-border pb-6">
        <Eyebrow>{eyebrow}</Eyebrow>
        <p className="font-heading-set text-h4 text-muted">{prop(node, "title", "What the critics are saying")}</p>
      </div>
      <ul className="grid gap-12 md:grid-cols-3 md:gap-0 md:divide-x md:divide-border">
        {shown.map((q, i) => (
          <li key={i} className="md:px-10 md:first:pl-0 md:last:pr-0">
            <figure className="flex h-full flex-col gap-6">
              <figcaption className={cn("flex min-h-9 items-center text-fg", MASTHEADS[i % MASTHEADS.length])}>{at(pubs, i)}</figcaption>
              <blockquote className="font-heading-set text-h3 text-balance">“{q}”</blockquote>
              <p className="mt-auto text-caption uppercase tracking-[0.18em] text-muted">{at(listProp(node, "dates", ["Spring issue", "Autumn guide", "Best of the year"]), i)}</p>
            </figure>
          </li>))}
      </ul>
    </Section>
  );
}

/* ------------------------------------------------------------------ team_grid */
const SOCIALS: { icon: LucideIcon; label: string }[] = [
  { icon: Mail, label: "Email" }, { icon: AtSign, label: "Social profile" }, { icon: Globe, label: "Portfolio" },
];

function SocialLinks({ name }: { name: string }) {
  return (
    <ul className="-ml-3 flex gap-1">
      {SOCIALS.map(({ icon: Icon, label }) => (
        <li key={label}>
          <a href="#" aria-label={`${label} for ${name}`}
            className="grid size-11 place-items-center rounded-pill text-muted transition-[color,background-color,transform] duration-200 ease-brand hover:bg-fg/[0.06] hover:text-fg active:scale-95">
            <Icon aria-hidden className="size-[18px]" />
          </a>
        </li>))}
    </ul>
  );
}

function TeamGrid({ node, columns }: NodeProps) {
  const variant = variantOf(node, "grid");
  const names = listProp(node, "names", ["Élise Moreau", "Tomás Reyes", "Hana Sato", "Marcus Bell", "Ines Duarte", "Kofi Mensah"]);
  const roles = listProp(node, "roles", ["Founder & creative director", "Head of craft", "Operations lead", "Client experience", "Sourcing", "Studio manager"]);
  const bios = listProp(node, "bios", [
    "Started it all at a kitchen table in 2014 and still signs off every new piece.",
    "Twelve years at the bench. Believes the last five percent is the whole job.",
    "Keeps every order on time and every partner on first-name terms.",
    "The voice on the phone who remembers your usual.",
    "Travels to meet every producer before anything reaches our shelves.",
    "Makes sure the space feels as good as what happens in it.",
  ]);
  const header = (
    <SectionHeader eyebrow={prop(node, "eyebrow", "The people")} title={prop(node, "title", "Small team, serious about the craft")}
      body={prop(node, "subtitle", "Everyone here has a hand in what you receive. These are the people behind it.")}
      action={<Button variant="link" arrow>{prop(node, "cta", "Join the team")}</Button>} />
  );

  if (variant === "compact") {
    return (
      <Section label="Team" tone="surface">
        {header}
        <ul className="grid gap-x-10 gap-y-2 md:grid-cols-2">
          {names.map((n, i) => (
            <li key={i} className="flex items-start gap-5 border-t border-border py-6">
              <Media ratio="1/1" subject="person" tone={i} label={`Portrait of ${n}`} zoom={false} className="w-16 shrink-0 rounded-pill md:w-20" />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-baseline justify-between gap-x-4">
                  <h3 className="font-heading-set text-h4">{n}</h3>
                  <p className="text-small text-muted">{at(roles, i)}</p>
                </div>
                <p className="mt-2 text-small text-muted text-pretty">{at(bios, i)}</p>
                <div className="mt-2"><SocialLinks name={n} /></div>
              </div>
            </li>))}
        </ul>
      </Section>
    );
  }
  const cols = columns ?? 4;
  return (
    <Section label="Team">
      {header}
      <ul className="grid grid-cols-1 gap-x-6 gap-y-12 sm:grid-cols-2 lg:grid-cols-[repeat(var(--cols),minmax(0,1fr))]"
        style={{ ["--cols" as string]: cols }}>
        {names.slice(0, cols === 3 ? 3 : 4).map((n, i) => (
          <li key={i} className="group flex flex-col">
            <Media ratio="4/5" subject="person" tone={i} label={`Portrait of ${n}`} className="transition-shadow duration-500 ease-brand group-hover:shadow-lg" />
            <p className="mt-5 text-caption font-semibold uppercase tracking-[0.16em] text-muted">{at(roles, i)}</p>
            <h3 className="mt-1 font-heading-set text-h4">{n}</h3>
            <p className="mt-2 text-small text-muted text-pretty">{at(bios, i)}</p>
            <div className="mt-3"><SocialLinks name={n} /></div>
          </li>))}
      </ul>
    </Section>
  );
}

/* ------------------------------------------------------------------ timeline */
function Timeline({ node }: NodeProps) {
  const variant = variantOf(node, "alternating");
  const years = listProp(node, "years", ["2014", "2017", "2020", "2024"]);
  const titles = listProp(node, "milestones", ["A single room and a big idea", "Our first real home", "Taking it further afield", "Still small by design"]);
  const details = listProp(node, "details", [
    "Opened with four products, two people and a waiting list of friends.",
    "Moved into the old print works and built the workshop we had sketched for years.",
    "Began shipping nationwide without giving up a single hand-finished step.",
    "Forty people, one standard. We say no to growth that would cost the detail.",
  ]);
  const header = (
    <SectionHeader eyebrow={prop(node, "eyebrow", "Our story")} title={prop(node, "title", "Ten years, one standard")}
      body={prop(node, "subtitle", "The moments that shaped how we work today.")}
      align={variant === "alternating" ? "center" : "start"} />
  );

  if (variant === "horizontal") {
    return (
      <Section label="Timeline" tone="surface">
        {header}
        {/* Phones: a vertical rule on the left. Desktop: one horizontal rule the markers sit on. */}
        <ol className="relative grid gap-10 border-l border-border pl-8 lg:grid-cols-4 lg:gap-8 lg:border-l-0 lg:border-t lg:pl-0 lg:pt-10">
          {years.map((y, i) => (
            <li key={i} className="relative">
              <span aria-hidden className={cn("absolute -left-[39px] top-1.5 size-3.5 rounded-pill border-2 border-surface bg-fg ring-1 ring-border lg:-top-[48px] lg:left-0",
                i === years.length - 1 && "bg-accent")} />
              <p className="font-heading-set text-h2 tabular-nums">{y}</p>
              <h3 className="mt-3 font-semibold">{at(titles, i)}</h3>
              <p className="mt-2 text-small text-muted text-pretty">{at(details, i)}</p>
            </li>))}
        </ol>
      </Section>
    );
  }
  return (
    <Section label="Timeline">
      {header}
      <ol className="relative mx-auto max-w-5xl">
        <span aria-hidden className="absolute bottom-2 left-[7px] top-2 w-px bg-border md:left-1/2" />
        {years.map((y, i) => {
          const right = i % 2 === 1;
          return (
            <li key={i} className="relative grid pb-14 pl-10 last:pb-0 md:grid-cols-2 md:gap-16 md:pl-0">
              <span aria-hidden className={cn("absolute left-0 top-2 size-[15px] rounded-pill border-[3px] border-bg bg-fg ring-1 ring-border md:left-1/2 md:-translate-x-1/2",
                i === years.length - 1 && "bg-accent")} />
              <p className={cn("font-heading-set text-h3 tabular-nums text-muted md:text-h1 md:text-fg/25", right ? "md:order-2 md:text-left" : "md:text-right")}>{y}</p>
              <div className={cn("mt-2 md:mt-1", right ? "md:order-1 md:text-right" : "")}>
                <h3 className="font-heading-set text-h4">{at(titles, i)}</h3>
                <p className={cn("mt-2 max-w-md text-muted text-pretty", right && "md:ml-auto")}>{at(details, i)}</p>
              </div>
            </li>
          );
        })}
      </ol>
    </Section>
  );
}

/* ------------------------------------------------------------------ steps */
const STEP_ICONS: LucideIcon[] = [Compass, Sparkles, PackageCheck, RefreshCw];

function Steps({ node }: NodeProps) {
  const variant = variantOf(node, "numbered");
  const titles = listProp(node, "steps", ["Tell us what you love", "We make it to order", "Delivered at its best", "Refill on your terms"]);
  const details = listProp(node, "details", [
    "A two-minute guide narrows it down to the few things worth trying first.",
    "Prepared in small batches the week it ships, never pulled from a warehouse shelf.",
    "Packed by hand and on its way within two days, tracked door to door.",
    "Pause, swap or skip any time. No calls, no forms, no small print.",
  ]);
  const shown = titles.slice(0, 4);
  const n = shown.length;
  const header = (
    <SectionHeader eyebrow={prop(node, "eyebrow", "How it works")} title={prop(node, "title", "From first choice to your door")}
      body={prop(node, "subtitle", "Four simple steps, with a person behind every one of them.")} align="center" />
  );
  const cta = <Button size="lg" arrow>{prop(node, "cta", "Get started")}</Button>;

  if (variant === "cards") {
    return (
      <Section label="How it works" tone="surface">
        {header}
        <ol className="grid gap-5 sm:grid-cols-2 lg:grid-cols-[repeat(var(--cols),minmax(0,1fr))]" style={{ ["--cols" as string]: n }}>
          {shown.map((t, i) => {
            const Icon = STEP_ICONS[i % STEP_ICONS.length];
            return (
              <li key={i} className="relative flex flex-col rounded-card border border-border bg-bg p-7 transition-[transform,box-shadow,border-color] duration-300 ease-brand hover:-translate-y-1 hover:border-fg/20 hover:shadow-lg">
                <div className="flex items-start justify-between">
                  <span className="grid size-12 place-items-center rounded-button bg-primary text-primary-fg"><Icon aria-hidden className="size-5" /></span>
                  <span aria-hidden className="font-heading-set text-h2 tabular-nums text-fg/15">{pad2(i)}</span>
                </div>
                <h3 className="mt-10 font-heading-set text-h4"><span className="sr-only">Step {i + 1}: </span>{t}</h3>
                <p className="mt-3 text-small text-muted text-pretty">{at(details, i)}</p>
                {i < n - 1 && (
                  <span aria-hidden className="absolute -right-[18px] top-1/2 z-10 hidden size-8 -translate-y-1/2 place-items-center rounded-pill border border-border bg-bg text-muted lg:grid">
                    <ArrowRight className="size-3.5" />
                  </span>)}
              </li>
            );
          })}
        </ol>
        <div className="mt-12 flex justify-center">{cta}</div>
      </Section>
    );
  }
  return (
    <Section label="How it works">
      {header}
      <ol className="relative grid gap-10 md:grid-cols-[repeat(var(--cols),minmax(0,1fr))] md:gap-8" style={{ ["--cols" as string]: n }}>
        {/* The connecting rule runs through the centres of the first and last markers. */}
        <span aria-hidden className="absolute bottom-6 left-6 top-6 w-px bg-border md:bottom-auto md:left-[calc(50%/var(--cols))] md:right-[calc(50%/var(--cols))] md:top-7 md:h-px md:w-auto" />
        {shown.map((t, i) => {
          const Icon = STEP_ICONS[i % STEP_ICONS.length];
          return (
            <li key={i} className="relative flex gap-6 md:flex-col md:items-center md:text-center">
              <span className="relative grid size-12 shrink-0 place-items-center rounded-pill border border-border bg-bg font-heading-set text-body font-semibold tabular-nums shadow-sm md:size-14 md:text-h4">
                {i + 1}
              </span>
              <div className="md:mt-2">
                <Icon aria-hidden className="mb-3 hidden size-5 text-accent md:mx-auto md:block" />
                <h3 className="font-heading-set text-h4"><span className="sr-only">Step {i + 1}: </span>{t}</h3>
                <p className="mt-2 max-w-xs text-muted text-pretty md:mx-auto">{at(details, i)}</p>
              </div>
            </li>
          );
        })}
      </ol>
      <div className="mt-14 flex justify-center">{cta}</div>
    </Section>
  );
}

/* ------------------------------------------------------------------ video_showcase */
function VideoShowcase({ node }: NodeProps) {
  const variant = variantOf(node, "standard");
  const title = prop(node, "title", "Inside the workshop");
  const chapters = listProp(node, "chapters", ["Where it begins", "The long slow middle", "Finishing by hand", "Out into the world"]);
  const times = listProp(node, "timestamps", ["0:00", "1:24", "3:10", "4:42"]);
  const duration = prop(node, "duration", "6 min film");
  const playLabel = prop(node, "play_label", "Watch the film");
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(false);
  const cinematic = variant === "cinematic";

  const poster = (
    <Media ratio={cinematic ? "2/1" : "16/10"} subject={subjectOf(prop(node, "media", ""), "space")} src={imageAt(node, "media")?.url} tone={cinematic ? 3 : 1}
      label={prop(node, "media_label", `Poster frame from ${title}`)} className="shadow-xl">
      <div className="absolute inset-0 grid place-items-center">
        <button type="button" aria-label={`${playing ? "Pause" : "Play"}: ${title}`} aria-pressed={playing} onClick={() => setPlaying((p) => !p)}
          className="group/play flex items-center gap-3 rounded-pill bg-bg/95 py-2 pl-2 pr-6 text-fg shadow-xl backdrop-blur transition-transform duration-300 ease-brand hover:scale-105 active:scale-95">
          <span className="grid size-12 place-items-center rounded-pill bg-primary text-primary-fg md:size-14">
            {playing ? <Pause aria-hidden className="size-5 fill-current" /> : <Play aria-hidden className="ml-0.5 size-5 fill-current" />}
          </span>
          <span className="text-left">
            <span className="block text-small font-semibold">{playing ? "Pause" : playLabel}</span>
            <span className="block text-caption text-muted">{duration}</span>
          </span>
        </button>
      </div>
    </Media>
  );
  const chapterList = (
    <ol aria-label="Chapters" className={cn(cinematic ? "grid gap-2 sm:grid-cols-2 lg:grid-cols-4" : "flex flex-col gap-1")}>
      {chapters.map((c, i) => (
        <li key={i}>
          <button type="button" aria-pressed={active === i} onClick={() => setActive(i)}
            className={cn("flex min-h-11 w-full items-center gap-4 rounded-button px-4 py-3 text-left transition-colors duration-200 ease-brand hover:bg-fg/[0.05]",
              active === i && "bg-surface-alt hover:bg-surface-alt")}>
            <span className={cn("font-heading-set text-small tabular-nums", active === i ? "text-fg" : "text-muted")}>{pad2(i)}</span>
            <span className="min-w-0 flex-1 font-semibold">{c}</span>
            <span className="flex items-center gap-1 text-caption tabular-nums text-muted"><Clock aria-hidden className="size-3" />{at(times, i)}</span>
          </button>
        </li>))}
    </ol>
  );

  if (cinematic) {
    return (
      <Section label="Film" tone="inverse" wide>
        <div className="mb-10 grid gap-6 lg:grid-cols-2 lg:items-end">
          <div className="space-y-4">
            <Eyebrow>{prop(node, "eyebrow", "The film")}</Eyebrow>
            <h2 className="font-heading-set text-h2 text-balance">{title}</h2>
          </div>
          <p className="text-lead text-muted text-pretty lg:justify-self-end lg:max-w-md">{prop(node, "caption", "Six quiet minutes with the people, places and patience behind everything we make.")}</p>
        </div>
        {poster}
        <div className="mt-6">{chapterList}</div>
      </Section>
    );
  }
  return (
    <Section label="Film">
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-12">
        <div className="lg:col-span-8">{poster}</div>
        <div className="flex flex-col lg:col-span-4">
          <Eyebrow>{prop(node, "eyebrow", "The film")}</Eyebrow>
          <h2 className="mt-4 font-heading-set text-h3 text-balance">{title}</h2>
          <p className="mt-4 text-muted text-pretty">{prop(node, "caption", "Six quiet minutes with the people, places and patience behind everything we make.")}</p>
          <div className="mt-8 border-t border-border pt-4 lg:mt-auto">
            <p className="mb-2 px-4 text-caption font-semibold uppercase tracking-[0.18em] text-muted">Chapters</p>
            {chapterList}
          </div>
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ tabs_showcase */
const TAB_SUBJECTS: Subject[] = ["product", "space", "leaf", "device"];

function TabsShowcase({ node }: NodeProps) {
  const variant = variantOf(node, "split");
  const labels = listProp(node, "tabs", ["Sourcing", "Making", "Packaging", "Aftercare"]);
  const heads = listProp(node, "headlines", [
    "We know every producer by name",
    "Small batches finished by hand",
    "Packed to arrive as it left us",
    "Looked after long after it lands",
  ]);
  const bodies = listProp(node, "bodies", [
    "Each partner is visited in person before we work together and every season after.",
    "Nothing is made ahead of demand. What you order this week is made this week.",
    "Plastic-free materials cut to fit so nothing shifts and nothing is wasted.",
    "Real people answer within the hour and repairs or swaps are always on us.",
  ]);
  const points = listProp(node, "points", ["Traceable to the source", "Checked at every step", "Guaranteed for life"]);
  const stacked = variant === "stacked";

  const tabs = labels.slice(0, 4).map((l, i) => ({
    id: `tab-${i}`,
    label: l,
    content: (
      <div className={cn("grid gap-10", stacked ? "" : "items-center lg:grid-cols-2 lg:gap-16")}>
        <div className={cn(stacked && "mx-auto max-w-2xl text-center")}>
          <h3 className="font-heading-set text-h3 text-balance">{at(heads, i)}</h3>
          <p className="mt-4 text-lead text-muted text-pretty">{at(bodies, i)}</p>
          <ul className={cn("mt-8 flex gap-3", stacked ? "flex-wrap justify-center" : "flex-col")}>
            {points.map((p) => (
              <li key={p} className={cn("flex items-center gap-3 text-small font-medium", stacked && "rounded-pill border border-border px-4 py-2")}>
                <Check aria-hidden className="size-4 shrink-0 text-accent" strokeWidth={2.5} />{p}
              </li>))}
          </ul>
          {!stacked && <Button variant="secondary" arrow className="mt-10">{prop(node, "cta", "Learn more")}</Button>}
        </div>
        <Media ratio={stacked ? "21/9" : "5/4"} subject={TAB_SUBJECTS[i % TAB_SUBJECTS.length]} tone={i} label={`${l}: ${at(heads, i)}`}
          className={cn("shadow-lg", stacked ? "order-first" : "")} />
      </div>
    ),
  }));

  return (
    <Section label="Product tour" tone={stacked ? "surface" : "default"}>
      <SectionHeader eyebrow={prop(node, "eyebrow", "How we work")} title={prop(node, "title", "Care at every stage")}
        body={prop(node, "subtitle", "A closer look at what happens before anything reaches you.")} align={stacked ? "center" : "start"} />
      <Tabs tabs={tabs} label={prop(node, "tabs_label", "Stages")}
        className={cn(stacked && "[&_[role=tablist]]:justify-start sm:[&_[role=tablist]]:justify-center")} />
    </Section>
  );
}

/* ------------------------------------------------------------------ stats_band */
function StatsBand({ node }: NodeProps) {
  const variant = variantOf(node, "band");
  const values = listProp(node, "values", ["10 yrs", "240k", "4.9", "98%"]);
  const labels = listProp(node, "labels", ["Of doing one thing well", "Orders packed by hand", "Average rating from 3100 reviews", "Of customers order again"]);
  const footnote = prop(node, "footnote", "Figures from our own records, January to December of last year.");
  const shown = values.slice(0, 4);

  if (variant === "split") {
    return (
      <Section label="In numbers">
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-16">
          <div className="lg:col-span-5">
            <Eyebrow>{prop(node, "eyebrow", "In numbers")}</Eyebrow>
            <h2 className="mt-4 font-heading-set text-h2 text-balance">{prop(node, "title", "The proof is in the repeat orders")}</h2>
            <p className="mt-5 text-lead text-muted text-pretty">{prop(node, "body", "We would rather earn a second visit than chase a first one. The numbers suggest it is working.")}</p>
          </div>
          <dl className="grid grid-cols-1 gap-px overflow-hidden rounded-card border border-border bg-border sm:grid-cols-2 lg:col-span-7">
            {shown.map((v, i) => (
              <div key={i} className="flex flex-col bg-bg p-8 md:p-10">
                <dt className="order-2 mt-3 text-small text-muted">{at(labels, i)}{i === 2 && <sup aria-hidden>*</sup>}</dt>
                <dd className="order-1 font-heading-set text-display leading-none tabular-nums">{v}</dd>
              </div>))}
          </dl>
        </div>
        <p className="mt-8 text-caption text-muted lg:text-right">* {footnote}</p>
      </Section>
    );
  }
  return (
    <Section label="In numbers" tone="inverse">
      <div className="mb-12 flex flex-wrap items-end justify-between gap-6 md:mb-16">
        <h2 className="max-w-xl font-heading-set text-h3 text-balance">{prop(node, "title", "The proof is in the repeat orders")}</h2>
        <Eyebrow>{prop(node, "eyebrow", "In numbers")}</Eyebrow>
      </div>
      <dl className="grid grid-cols-1 gap-y-10 sm:grid-cols-2 lg:grid-cols-4">
        {shown.map((v, i) => (
          <div key={i} className="flex flex-col border-t border-border pt-6 lg:border-l lg:border-t-0 lg:pl-8 lg:pt-0 lg:first:border-l-0 lg:first:pl-0">
            <dt className="order-2 mt-3 max-w-[16rem] text-small text-muted">{at(labels, i)}{i === 2 && <sup aria-hidden>*</sup>}</dt>
            <dd className="order-1 font-heading-set text-display leading-none tabular-nums">{v}</dd>
          </div>))}
      </dl>
      <p className="mt-14 border-t border-border pt-6 text-caption text-muted">* {footnote}</p>
    </Section>
  );
}

/* ------------------------------------------------------------------ comparison_table */
type Cell = "yes" | "no" | string;
function CellValue({ value }: { value: Cell }) {
  if (value === "yes")
    return <span className="inline-grid size-7 place-items-center rounded-pill bg-success text-bg"><Check aria-hidden className="size-4" strokeWidth={3} /><span className="sr-only">Included</span></span>;
  if (value === "no")
    return <span className="inline-grid size-7 place-items-center rounded-pill text-muted"><X aria-hidden className="size-4" /><span className="sr-only">Not included</span></span>;
  return <span className="text-small font-medium">{value}</span>;
}

function ComparisonTable({ node }: NodeProps) {
  const variant = variantOf(node, "versus");
  const plans = variant === "plans";
  const rows = listProp(node, "rows", [
    "Made to order", "Sourced direct from producers", "Hand-finished details", "Free returns",
    "Real person support", "Plastic-free packaging", "Lifetime aftercare",
  ]);
  const cols = listProp(node, "columns", plans ? ["Essential", "Signature", "Reserve"] : ["Us", "Typical alternatives"]);
  const fallbackCells = plans
    ? ["yes", "yes", "yes", "no", "yes", "yes", "no", "yes", "yes", "30 days", "60 days", "Always", "Email", "Priority", "Dedicated", "yes", "yes", "yes", "no", "no", "yes"]
    : ["yes", "no", "yes", "Sometimes", "yes", "no", "yes", "14 days", "yes", "no", "yes", "no", "yes", "no"];
  const cells = listProp(node, "cells", fallbackCells);
  const highlight = plans ? 1 : 0;
  const nCols = cols.length;
  const cellAt = (r: number, c: number): Cell => cells[(r * nCols + c) % cells.length];
  const hl = (c: number) => c === highlight && "bg-surface";

  return (
    <Section label="Comparison">
      <SectionHeader eyebrow={prop(node, "eyebrow", "Compare")} title={prop(node, "title", plans ? "Find the right fit" : "The difference is in the detail")}
        body={prop(node, "subtitle", plans ? "Every option includes the same care. Choose how much of it you want." : "What you get with us, side by side with the usual way of doing things.")} />
      {/* Phones scroll the table sideways inside its own frame; the row labels stay pinned. */}
      <div className="relative -mx-4 overflow-x-auto px-4 lg:mx-0 lg:overflow-visible lg:px-0">
        <table className="w-full min-w-[560px] border-separate border-spacing-0 text-left">
          <caption className="sr-only">{prop(node, "title", plans ? "Find the right fit" : "The difference is in the detail")}</caption>
          <thead>
            <tr>
              <th scope="col" className="sticky left-0 z-20 border-b border-border bg-bg py-5 pl-0 pr-6 align-bottom text-small font-semibold text-muted lg:top-0">
                {prop(node, "feature_label", "What you get")}
              </th>
              {cols.map((c, i) => (
                <th key={i} scope="col"
                  className={cn("z-10 border-b border-border bg-bg px-4 py-5 text-center align-bottom lg:sticky lg:top-0", i === highlight && "rounded-t-card bg-surface")}>
                  {i === highlight && <Badge tone="primary" className="mb-3">{prop(node, "badge", plans ? "Most chosen" : "Recommended")}</Badge>}
                  <span className={cn("block font-heading-set text-h4", i !== highlight && "text-muted")}>{c}</span>
                </th>))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, ri) => (
              <tr key={ri} className="group">
                <th scope="row" className="sticky left-0 z-10 border-b border-border bg-bg py-4 pl-0 pr-6 text-small font-medium transition-colors group-hover:bg-surface-alt">{r}</th>
                {cols.map((_, ci) => (
                  <td key={ci} className={cn("border-b border-border bg-bg px-4 py-4 text-center transition-colors group-hover:bg-surface-alt", hl(ci))}>
                    <CellValue value={cellAt(ri, ci)} />
                  </td>))}
              </tr>))}
            {plans && (
              <tr>
                <td className="sticky left-0 border-b-0 bg-bg p-0" />
                {cols.map((c, ci) => (
                  <td key={ci} className={cn("border-b-0 px-4 pb-5 pt-6 text-center", ci === highlight && "rounded-b-card bg-surface")}>
                    <Button variant={ci === highlight ? "primary" : "secondary"} size="sm" aria-label={`Choose ${c}`}>{prop(node, "cta", "Choose")}</Button>
                  </td>))}
              </tr>)}
          </tbody>
        </table>
      </div>
      {!plans && (
        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Button arrow>{prop(node, "cta", "See it for yourself")}</Button>
          <p className="text-small text-muted">{prop(node, "note", "Compared with the three most popular alternatives, checked this season.")}</p>
        </div>)}
    </Section>
  );
}

export const SECTIONS: SectionMap = {
  TestimonialSpotlight, PressQuotes, TeamGrid, MilestoneTimeline: Timeline, HowItWorksSteps: Steps,
  VideoShowcase, TabsShowcase, StatsBand, ComparisonTable,
};
