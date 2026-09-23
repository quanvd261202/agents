/** Content and editorial sections. Keys are the catalog's implementation.root names. See sections/README.md. */
import { useState, type FormEvent, type ReactNode } from "react";
import {
  ArrowUpRight, Award, Check, ChevronDown, Clock, Gift, Hand, Heart, Leaf, Mail, MapPin, MessageCircle, Navigation, Phone,
  Quote, Recycle, ShieldCheck, Sparkles, Truck,
} from "lucide-react";
import { Avatar, Button, Disclosure, Eyebrow, Field, Media, Section, SectionHeader, listProp, prop, range, variantOf } from "../ui";
import { cn } from "../lib/cn";
import type { RenderNode } from "../types";
import type { NodeProps, SectionMap } from "./types";

/* ------------------------------------------------------------------ shared helpers */
type Subject = Parameters<typeof Media>[0]["subject"];
const SUBJECTS = ["cup", "bag", "leaf", "glass", "abstract", "person", "space", "device", "chart", "product"];
/** The `media` slot names what the image shows; a known subject picks the matching silhouette. */
const subjectOf = (value: string, fallback: Subject): Subject =>
  (SUBJECTS.includes(value) ? value : fallback) as Subject;

/** Numbered slots (`body_1`, `answer_2`...) for long copy that may itself contain commas. */
const nth = (n: RenderNode, key: string, i: number, fallback: string) => prop(n, `${key}_${i + 1}`, fallback);
/** When the spec fills any numbered slot, only the filled ones render; otherwise the fallbacks do. */
const filledCount = (n: RenderNode, key: string, max: number, fallback: number) => {
  const filled = range(max).filter((i) => typeof n.props[`${key}_${i + 1}`] === "string" && String(n.props[`${key}_${i + 1}`]).trim());
  return filled.length ? filled[filled.length - 1] + 1 : fallback;
};
const pad2 = (i: number) => String(i + 1).padStart(2, "0");

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
/** Wraps each occurrence of the given phrases in <em>, so a statement can carry highlighted words. */
function emphasize(text: string, phrases: string[], className: string): ReactNode[] {
  const list = phrases.filter(Boolean).map(escapeRe);
  if (!list.length) return [text];
  return text.split(new RegExp(`(${list.join("|")})`, "gi")).map((part, i) =>
    i % 2 ? <em key={i} className={className}>{part}</em> : part);
}

/** Founder or author line: a short rule, the name set in the heading face, the role beneath. */
function Signature({ name, role, align = "start" }: { name: string; role: string; align?: "start" | "center" }) {
  return (
    <div className={cn("flex items-center gap-4", align === "center" && "justify-center")}>
      <span aria-hidden className="h-px w-10 bg-fg/40" />
      <div>
        <p className="font-heading-set text-h4 italic">{name}</p>
        <p className="text-caption uppercase tracking-[0.16em] text-muted">{role}</p>
      </div>
    </div>
  );
}

function PullQuote({ text, small, className }: { text: string; small?: boolean; className?: string }) {
  return (
    <blockquote className={cn("border-l-2 border-fg pl-6 md:pl-8", className)}>
      <p className={cn("font-heading-set italic text-balance", small ? "text-h4" : "text-h3")}>“{text}”</p>
    </blockquote>
  );
}

/* ------------------------------------------------------------------ FAQ */
const FAQ_FALLBACK: [string, string][] = [
  ["How soon will my order arrive?", "Most orders leave us within two working days. Seasonal and made-to-order pieces show their own dispatch date before you pay, so there are no surprises."],
  ["Do you offer gift wrapping?", "Every order can be wrapped in recycled paper and tied by hand. Add a note at checkout and we will write it out for you rather than print it."],
  ["What if something is not quite right?", "Tell us within thirty days and we will make it right: an exchange, a replacement or a full refund. No forms, just a short email to the team."],
  ["Can I visit in person?", "Our doors are open six days a week. Drop by and we will happily walk you through what is new, what is in season and what we are enjoying right now."],
  ["Do you work with businesses and events?", "We partner with a small number of businesses each season. Tell us what you have in mind and we will reply within two working days."],
];

function FAQ({ node }: NodeProps) {
  const variant = variantOf(node);
  const count = filledCount(node, "question", 6, FAQ_FALLBACK.length);
  const items = range(count).map((i) => ({
    q: nth(node, "question", i, FAQ_FALLBACK[i]?.[0] ?? FAQ_FALLBACK[0][0]),
    a: nth(node, "answer", i, FAQ_FALLBACK[i]?.[1] ?? FAQ_FALLBACK[0][1]),
  }));
  const eyebrow = prop(node, "eyebrow", "Good to know");
  const title = prop(node, "title", "Questions, answered honestly.");
  const intro = prop(node, "intro", "Everything you might want to know before your first visit or order. If your question is not here, we are only a message away.");
  const contactTitle = prop(node, "contact_title", "Still wondering?");
  const contactBody = prop(node, "contact_body", "Write to us and a real person on the team will reply within one working day.");
  const contactCta = prop(node, "contact_cta", "Get in touch");

  if (variant === "two_column") {
    return (
      <Section label={title} tone="surface">
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-16">
          <div className="lg:col-span-5">
            <div className="space-y-5 lg:sticky lg:top-24">
              <Eyebrow>{eyebrow}</Eyebrow>
              <h2 className="font-heading-set text-h2 text-balance">{title}</h2>
              <p className="max-w-md text-lead text-muted text-pretty">{intro}</p>
              <div className="mt-10 flex max-w-md items-start gap-4 rounded-card border border-border bg-bg p-6 shadow-sm">
                <Avatar name={prop(node, "contact_name", "Maya Okafor")} />
                <div className="space-y-2">
                  <p className="font-semibold">{contactTitle}</p>
                  <p className="text-small text-muted">{contactBody}</p>
                  <Button variant="link" arrow className="mt-1 h-11 px-0">{contactCta}</Button>
                </div>
              </div>
            </div>
          </div>
          <Disclosure items={items} className="lg:col-span-7" />
        </div>
      </Section>
    );
  }
  return (
    <Section label={title}>
      <div className="mx-auto max-w-3xl">
        <SectionHeader align="center" eyebrow={eyebrow} title={title} body={intro} />
        <Disclosure items={items} />
        <div className="mt-12 flex flex-col gap-5 rounded-card border border-border p-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <span className="grid size-11 shrink-0 place-items-center rounded-pill bg-surface-alt"><MessageCircle aria-hidden className="size-5" /></span>
            <div>
              <p className="font-semibold">{contactTitle}</p>
              <p className="text-small text-muted">{contactBody}</p>
            </div>
          </div>
          <Button variant="secondary" arrow className="shrink-0">{contactCta}</Button>
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ brand story */
function BrandStory({ node }: NodeProps) {
  const variant = variantOf(node, "image_left");
  const eyebrow = prop(node, "eyebrow", "Our story");
  const title = prop(node, "title", "It began with one small room and a stubborn idea.");
  const body = prop(node, "body", "We opened in 2014 with a single counter, a borrowed table and the belief that everyday things deserve more care than they usually get. We still choose every piece ourselves, and we still know most of our makers by their first name.");
  const body2 = prop(node, "body_2", "A decade on, the room is bigger but the rule has not changed. It is slower, and it means saying no more often than yes, but it is the only way we know how to work, and the reason so many of you keep coming back.");
  const quote = prop(node, "quote", "If we would not keep it at home, it does not belong on our shelves.");
  const name = prop(node, "signature", "Clara Moreau");
  const role = prop(node, "signature_role", "Founder");
  const cta = prop(node, "cta", "Read the full story");
  const subject = subjectOf(prop(node, "media", ""), "space");
  const label = prop(node, "media_label", "The first shop, on a quiet morning");
  const dropCap = "first-letter:float-left first-letter:mr-3 first-letter:mt-1 first-letter:font-heading first-letter:text-[3.6em] first-letter:leading-[0.8]";

  if (variant === "overlap") {
    return (
      <Section label={eyebrow} tone="surface" wide>
        <div className="mb-12 grid gap-6 md:mb-16 lg:grid-cols-12">
          <Eyebrow className="lg:col-span-3 lg:pt-4">{eyebrow}</Eyebrow>
          <h2 className="font-heading-set text-h1 text-balance lg:col-span-8">{title}</h2>
        </div>
        <div className="grid lg:grid-cols-12">
          <Media ratio="16/10" subject={subject} label={label} className="shadow-lg lg:col-span-8 lg:col-start-1 lg:row-start-1" />
          <div className="relative z-10 mx-4 -mt-16 space-y-8 rounded-lg bg-bg p-8 shadow-xl md:mx-12 md:-mt-24 md:p-12 lg:col-span-5 lg:col-start-8 lg:row-start-1 lg:mx-0 lg:mt-0 lg:self-center">
            <p className={cn("text-lead text-pretty", dropCap)}>{body}</p>
            <PullQuote text={quote} small />
          </div>
          <div className="mt-12 grid gap-8 md:grid-cols-2 lg:col-span-12 lg:mt-16 lg:grid-cols-12 lg:gap-8">
            <p className="max-w-[60ch] text-muted text-pretty lg:col-span-5 lg:col-start-2">{body2}</p>
            <div className="flex flex-wrap items-center justify-between gap-6 lg:col-span-5 lg:col-start-8 lg:self-start">
              <Signature name={name} role={role} />
              <Button variant="link" arrow className="px-0">{cta}</Button>
            </div>
          </div>
        </div>
      </Section>
    );
  }
  if (variant === "stacked") {
    return (
      <Section label={eyebrow} size="lg">
        <div className="mx-auto max-w-3xl space-y-6 text-center">
          <Eyebrow>{eyebrow}</Eyebrow>
          <h2 className="font-heading-set text-h1 text-balance">{title}</h2>
        </div>
        <Media ratio="21/9" subject={subject} label={label} className="mt-14 shadow-lg md:mt-20" />
        <div className="mx-auto mt-14 grid max-w-5xl gap-10 md:mt-20 md:grid-cols-12">
          <p className={cn("text-lead text-pretty md:col-span-5", dropCap)}>{body}</p>
          <div className="space-y-8 md:col-span-6 md:col-start-7">
            <p className="text-muted text-pretty">{body2}</p>
            <PullQuote text={quote} />
            <div className="flex flex-wrap items-center justify-between gap-6">
              <Signature name={name} role={role} />
              <Button variant="secondary" arrow>{cta}</Button>
            </div>
          </div>
        </div>
      </Section>
    );
  }
  return (
    <Section label={eyebrow} wide>
      <div className="grid items-start gap-16 lg:grid-cols-12 lg:gap-12">
        <figure className="relative pb-12 pr-8 md:pr-16 lg:col-span-5 lg:pb-16 lg:pr-0">
          <Media ratio="4/5" subject={subject} label={label} className="shadow-lg" />
          <Media ratio="1/1" subject="leaf" tone={2} label={prop(node, "detail_label", "A detail from the workshop")}
            className="absolute bottom-0 right-0 w-36 border-4 border-bg shadow-lg md:w-48 lg:-right-12" />
          <figcaption className="mt-4 max-w-[60%] text-caption text-muted">{label}</figcaption>
        </figure>
        <div className="space-y-8 lg:col-span-6 lg:col-start-7 lg:pt-10">
          <Eyebrow>{eyebrow}</Eyebrow>
          <h2 className="font-heading-set text-h2 text-balance">{title}</h2>
          <div className="max-w-[60ch] space-y-5">
            <p className={cn("text-lead text-pretty", dropCap)}>{body}</p>
            <p className="text-muted text-pretty">{body2}</p>
          </div>
          <PullQuote text={quote} className="max-w-xl py-2" />
          <div className="flex flex-wrap items-center gap-x-10 gap-y-6 pt-2">
            <Signature name={name} role={role} />
            <Button variant="link" arrow className="px-0">{cta}</Button>
          </div>
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ media + text rows */
const ROWS = [
  { title: "Chosen at the source", body: "We travel to meet the people who grow, weave and make what we offer. Every relationship is direct, every price is agreed face to face, and every piece has a name behind it.", subject: "leaf" as Subject },
  { title: "Finished by hand", body: "Nothing leaves the studio without a last look from someone who cares. Working in small batches means we notice the details a production line would never catch.", subject: "product" as Subject },
  { title: "Made to be kept", body: "We would rather you own one thing you love for a decade than ten you replace next year. Repairs, refills and honest advice are part of the price.", subject: "bag" as Subject },
];

function MediaText({ node }: NodeProps) {
  const variant = variantOf(node, "alternating");
  const titles = listProp(node, "items", ROWS.map((r) => r.title)).slice(0, 4);
  const stats = listProp(node, "stats", ["14", "48 hrs", "10 yrs"]);
  const statLabels = listProp(node, "stat_labels", ["partner makers", "from bench to door", "average life of a piece"]);
  const link = prop(node, "link_label", "Learn more");
  const flip = variant === "reversed";
  return (
    <Section label={prop(node, "title", "How we work")} wide>
      <SectionHeader eyebrow={prop(node, "eyebrow", "How we work")} title={prop(node, "title", "Three things we refuse to rush.")}
        body={prop(node, "intro", "The quiet decisions behind everything we make, pour and pack.")} className="md:mb-20" />
      <div className="space-y-20 md:space-y-28">
        {titles.map((t, i) => {
          const mediaRight = (i % 2 === 1) !== flip;
          const row = ROWS[i % ROWS.length];
          return (
            <div key={i} className="grid items-center gap-8 md:grid-cols-2 md:gap-12 lg:grid-cols-12 lg:gap-8">
              <Media ratio={i % 2 ? "4/3" : "5/4"} subject={row.subject} tone={i} label={t}
                className={cn("lg:col-span-7", mediaRight && "md:order-2 lg:col-start-6")} />
              <div className={cn("space-y-5 lg:col-span-4", mediaRight ? "md:order-1 lg:col-start-1 lg:row-start-1" : "lg:col-start-9")}>
                <p className="flex items-center gap-4 text-caption font-semibold tracking-[0.18em] text-muted">
                  <span className="tabular-nums">{pad2(i)}</span><span aria-hidden className="h-px w-12 bg-border" />
                </p>
                <h3 className="font-heading-set text-h3 text-balance">{t}</h3>
                <p className="text-muted text-pretty">{nth(node, "body", i, row.body)}</p>
                {variant === "stats" && stats[i] && (
                  <p className="flex items-baseline gap-3 border-t border-border pt-5">
                    <span className="font-heading-set text-h2 tabular-nums">{stats[i]}</span>
                    <span className="text-small text-muted">{statLabels[i] ?? ""}</span>
                  </p>)}
                <Button variant="link" arrow className="px-0">{link}</Button>
              </div>
            </div>
          );
        })}
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ manifesto */
function Manifesto({ node }: NodeProps) {
  const variant = variantOf(node);
  const eyebrow = prop(node, "eyebrow", "What we believe");
  const statement = prop(node, "statement", "We believe good things are made slowly, chosen with care and kept for years. Not louder, not faster. Simply better, for the people who notice the difference.");
  const highlight = listProp(node, "highlight", ["made slowly", "kept for years", "people who notice"]);
  const name = prop(node, "signature", "The team");
  const role = prop(node, "signature_role", "Written on our first day, still true");

  if (variant === "inverse") {
    return (
      <Section label={eyebrow} tone="inverse" size="lg">
        <div className="mx-auto max-w-5xl py-6 text-center md:py-12">
          <Eyebrow>{eyebrow}</Eyebrow>
          <h2 className="mt-10 font-heading-set text-h1 text-balance text-muted md:text-display">
            {emphasize(statement, highlight, "not-italic text-fg")}
          </h2>
          <div className="mt-14"><Signature name={name} role={role} align="center" /></div>
        </div>
      </Section>
    );
  }
  if (variant === "split") {
    return (
      <Section label={eyebrow} tone="alt" size="lg" wide>
        <div className="grid gap-10 lg:grid-cols-12 lg:gap-8">
          <div className="space-y-6 lg:col-span-3">
            <Eyebrow>{eyebrow}</Eyebrow>
            <p className="max-w-xs text-small text-muted">{prop(node, "body", "Five sentences we wrote before we sold a single thing, and still read aloud to everyone who joins.")}</p>
            <Button variant="link" arrow className="px-0">{prop(node, "cta", "Meet the people behind it")}</Button>
          </div>
          <h2 className="font-heading-set text-h1 text-pretty lg:col-span-8 lg:col-start-5">
            {emphasize(statement, highlight, "not-italic bg-linear-to-t from-accent/35 from-[34%] to-transparent to-[34%] [box-decoration-break:clone]")}
          </h2>
        </div>
      </Section>
    );
  }
  return (
    <Section label={eyebrow} size="lg" wide>
      <div className="grid gap-10 py-4 lg:grid-cols-12 md:py-10">
        <p className="flex items-center gap-4 text-caption font-semibold uppercase tracking-[0.18em] text-muted lg:col-span-12">
          <span aria-hidden className="h-px w-12 bg-fg/40" />{eyebrow}
        </p>
        <h2 className="font-heading-set text-h1 text-balance lg:col-span-11 lg:text-display">
          {emphasize(statement, highlight, "italic underline decoration-accent decoration-[0.06em] underline-offset-[0.14em]")}
        </h2>
        <div className="lg:col-span-5 lg:col-start-8 lg:mt-6"><Signature name={name} role={role} /></div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ editorial quote */
function EditorialQuote({ node }: NodeProps) {
  const variant = variantOf(node, "centered");
  const quote = prop(node, "quote", "They treat every visit as if it were the only one that day. You feel it the moment you walk through the door.");
  const author = prop(node, "author", "Hannah Lindqvist");
  const role = prop(node, "role", "A regular since 2019");
  const label = "Quote";

  if (variant === "with_media") {
    return (
      <Section label={label} wide>
        <figure className="grid items-center gap-12 md:grid-cols-12 md:gap-10">
          <Media ratio="4/5" subject={subjectOf(prop(node, "media", ""), "person")} tone={1}
            label={prop(node, "media_label", `Portrait of ${author}`)} className="md:col-span-5 lg:col-span-4 lg:col-start-2" />
          <div className="space-y-10 md:col-span-7 lg:col-span-6 lg:col-start-7">
            <Quote aria-hidden className="size-10 text-accent" strokeWidth={1.5} />
            <blockquote><p className="font-heading-set text-h2 text-pretty">{quote}</p></blockquote>
            <figcaption className="flex items-center gap-4 border-t border-border pt-6">
              <div><p className="font-semibold">{author}</p><p className="text-small text-muted">{role}</p></div>
            </figcaption>
          </div>
        </figure>
      </Section>
    );
  }
  if (variant === "band") {
    return (
      <Section label={label} tone="inverse" size="lg" wide>
        <figure className="grid gap-12 lg:grid-cols-12">
          <Eyebrow className="lg:col-span-2 lg:pt-5">{prop(node, "eyebrow", "In their words")}</Eyebrow>
          <div className="space-y-12 lg:col-span-9">
            <blockquote><p className="font-heading-set text-h1 text-balance">“{quote}”</p></blockquote>
            <figcaption className="flex flex-wrap items-center gap-x-6 gap-y-2">
              <span aria-hidden className="h-px w-16 bg-fg/50" />
              <p className="font-semibold">{author}</p>
              <p className="text-muted">{role}</p>
            </figcaption>
          </div>
        </figure>
      </Section>
    );
  }
  return (
    <Section label={label} tone="surface" size="lg">
      <figure className="mx-auto flex max-w-4xl flex-col items-center gap-10 text-center">
        <Quote aria-hidden className="size-12 text-accent" strokeWidth={1.25} />
        <blockquote><p className="font-heading-set text-h2 text-balance md:text-h1">{quote}</p></blockquote>
        <figcaption className="flex items-center gap-4 text-left">
          <Avatar name={author} className="bg-bg" />
          <div><p className="font-semibold">{author}</p><p className="text-small text-muted">{role}</p></div>
        </figcaption>
      </figure>
    </Section>
  );
}

/* ------------------------------------------------------------------ gallery */
const GALLERY_SUBJECTS: Subject[] = ["space", "person", "product", "cup", "leaf", "glass", "bag"];
/** [tile index, ratio] per column; heights per column: 1.25+0.75, 0.75+1.25, 1.333+0.667. */
const MASONRY_COLUMNS: [number, string][][] = [[[0, "4/5"], [1, "4/3"]], [[2, "4/3"], [3, "4/5"]], [[4, "3/4"], [5, "3/2"]]];

function GalleryMasonry({ node }: NodeProps) {
  const variant = variantOf(node, "masonry");
  const captions = listProp(node, "captions", [
    "Morning light, before the doors open", "Hands at work in the studio", "Details worth a closer look",
    "Where every piece is finished", "Our corner of the neighbourhood", "A table set for slow afternoons",
    "Colour of the season, gathered weekly",
  ]);
  const title = prop(node, "title", "A look inside.");
  const header = (
    <SectionHeader eyebrow={prop(node, "eyebrow", "Gallery")} title={title}
      body={prop(node, "intro", "Moments from the room, the bench and the people who make it what it is.")}
      action={<Button variant="link" arrow className="px-0">{prop(node, "cta", "Follow along")}</Button>} />
  );

  if (variant === "mosaic") {
    // Five tiles on a six-column grid: one hero tile, one tall, three supporting. Explicit spans keep
    // the composition intentional instead of whatever a packing algorithm produces.
    const spans = [
      "col-span-2 row-span-2 md:col-span-4",
      "md:col-span-2",
      "row-span-2 md:col-span-2",
      "md:col-span-2",
      "col-span-2 md:col-span-2",
    ];
    return (
      <Section label={title} wide>
        {header}
        <div className="grid auto-rows-[170px] grid-cols-2 gap-3 md:auto-rows-[220px] md:grid-cols-6 md:gap-5 lg:auto-rows-[260px]">
          {spans.map((span, i) => (
            <figure key={i} className={cn("relative", span)}>
              <Media ratio="auto" subject={GALLERY_SUBJECTS[i]} tone={i} label={captions[i % captions.length]} className="h-full" />
              <figcaption className="absolute bottom-3 left-3 right-3 w-fit max-w-[calc(100%-1.5rem)] rounded-sm bg-bg/95 px-3 py-1.5 text-caption font-medium text-fg shadow-sm md:bottom-4 md:left-4">
                {captions[i % captions.length]}
              </figcaption>
            </figure>))}
        </div>
      </Section>
    );
  }
  return (
    <Section label={title} wide>
      {header}
      {/* Three hand-balanced columns (each sums to the same height), the middle one dropped for a
          staggered, editorial rhythm. Phones read the tiles in order as one column. */}
      <div className="grid gap-8 md:grid-cols-3 md:gap-6 lg:gap-8">
        {MASONRY_COLUMNS.map((col, c) => (
          <div key={c} className={cn("flex flex-col gap-8 lg:gap-10", c === 1 && "md:pt-20")}>
            {col.map(([i, ratio]) => (
              <figure key={i}>
                <Media ratio={ratio} subject={GALLERY_SUBJECTS[i % GALLERY_SUBJECTS.length]} tone={i} label={captions[i % captions.length]} />
                <figcaption className="mt-3 flex gap-3 text-small">
                  <span className="tabular-nums text-muted">{pad2(i)}</span>
                  <span>{captions[i % captions.length]}</span>
                </figcaption>
              </figure>))}
          </div>))}
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ article grid */
const ARTICLE_SUBJECTS: Subject[] = ["cup", "person", "leaf", "space"];

function ArticleGrid({ node }: NodeProps) {
  const variant = variantOf(node, "featured");
  const titles = listProp(node, "titles", [
    "A slow morning, from first light to open doors", "Five things our makers taught us this year",
    "How to care for the pieces you love", "Inside the studio, the week before launch",
  ]);
  const cats = listProp(node, "categories", ["Journal", "Makers", "Guides", "Behind the scenes"]);
  const times = listProp(node, "read_times", ["6 min read", "4 min read", "3 min read", "5 min read"]);
  const dates = listProp(node, "dates", ["12 Sept", "3 Sept", "28 Aug", "19 Aug"]);
  const excerpt = prop(node, "excerpt", "What happens in the quiet hours before anyone arrives: the rituals, the tools and the small decisions that shape everything that follows.");
  const title = prop(node, "title", "Notes from the journal.");
  const at = (list: string[], i: number) => list[i % list.length];
  const Meta = ({ i, className }: { i: number; className?: string }) => (
    <p className={cn("flex flex-wrap items-center gap-x-3 gap-y-1 text-caption text-muted", className)}>
      <span className="font-semibold uppercase tracking-[0.16em] text-fg">{at(cats, i)}</span>
      <span aria-hidden>·</span><span>{at(dates, i)}</span><span aria-hidden>·</span><span>{at(times, i)}</span>
    </p>
  );
  /** Whole card is the link target; the anchor stays inside the heading so the name is the title. */
  const linkCls = "after:absolute after:inset-0 decoration-1 underline-offset-4 group-hover:underline focus-visible:outline-none";
  const cardCls = "group relative focus-within:outline-2 focus-within:outline-offset-4 focus-within:outline-ring";
  const header = (
    <SectionHeader eyebrow={prop(node, "eyebrow", "Journal")} title={title}
      body={prop(node, "intro", "Stories, guides and small discoveries from the people behind the counter.")}
      action={<Button variant="secondary" arrow>{prop(node, "cta", "All stories")}</Button>} />
  );

  if (variant === "list") {
    return (
      <Section label={title}>
        {header}
        <ol className="border-t border-border">
          {titles.slice(0, 5).map((t, i) => (
            <li key={i} className={cn(cardCls, "grid grid-cols-[1fr_auto] items-center gap-6 border-b border-border py-7 md:grid-cols-[8rem_1fr_7rem_auto] md:gap-10")}>
              <p className="hidden text-small tabular-nums text-muted md:block">{at(dates, i)}</p>
              <div className="min-w-0 space-y-2">
                <p className="text-caption font-semibold uppercase tracking-[0.16em] text-muted">{at(cats, i)}</p>
                <h3 className="font-heading-set text-h3 text-balance"><a href="#" className={linkCls}>{t}</a></h3>
              </div>
              <p className="hidden text-small text-muted md:block">{at(times, i)}</p>
              <span aria-hidden className="grid size-11 place-items-center rounded-pill border border-border transition-[background-color,color,transform] duration-300 ease-brand group-hover:rotate-45 group-hover:bg-primary group-hover:text-primary-fg">
                <ArrowUpRight className="size-4" />
              </span>
            </li>))}
        </ol>
      </Section>
    );
  }
  if (variant === "grid") {
    return (
      <Section label={title} tone="surface">
        {header}
        <div className="grid gap-x-6 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
          {titles.slice(0, 3).map((t, i) => (
            <article key={i} className={cn(cardCls, "flex flex-col gap-5")}>
              <Media ratio="4/3" subject={ARTICLE_SUBJECTS[i % 4]} tone={i} label={t} />
              <Meta i={i} />
              <h3 className="font-heading-set text-h4 text-balance"><a href="#" className={linkCls}>{t}</a></h3>
            </article>))}
        </div>
      </Section>
    );
  }
  return (
    <Section label={title} wide>
      {header}
      <div className="grid gap-12 lg:grid-cols-12 lg:gap-10">
        <article className={cn(cardCls, "flex flex-col gap-6 lg:col-span-7")}>
          <Media ratio="16/11" subject={ARTICLE_SUBJECTS[0]} label={titles[0]} className="shadow-sm" />
          <div className="max-w-2xl space-y-4">
            <Meta i={0} />
            <h3 className="font-heading-set text-h2 text-balance"><a href="#" className={linkCls}>{titles[0]}</a></h3>
            <p className="text-lead text-muted text-pretty">{excerpt}</p>
          </div>
        </article>
        <div className="flex flex-col divide-y divide-border border-t border-border lg:col-span-5 lg:border-t-0">
          {titles.slice(1, 4).map((t, k) => {
            const i = k + 1;
            return (
              <article key={i} className={cn(cardCls, "grid grid-cols-[7rem_1fr] items-start gap-5 py-6 first:pt-6 sm:grid-cols-[9rem_1fr] lg:first:pt-0")}>
                <Media ratio="1/1" subject={ARTICLE_SUBJECTS[i % 4]} tone={i} label={t} className="rounded-card" />
                <div className="min-w-0 space-y-3">
                  <Meta i={i} />
                  <h3 className="font-heading-set text-h4 text-balance"><a href="#" className={linkCls}>{t}</a></h3>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ image band */
function ImageBand({ node }: NodeProps) {
  const variant = variantOf(node, "caption_left");
  const eyebrow = prop(node, "eyebrow", "Plate Nº 04 · The studio");
  const title = prop(node, "title", "Made in the same room, by the same hands, every day since we opened.");
  const caption = prop(node, "caption", "We moved in when the building was empty and the floors needed sanding. Most of what you see on the shelves is still finished within a few metres of this window.");
  const cta = prop(node, "cta", "Plan a visit");
  const subject = subjectOf(prop(node, "media", ""), "space");
  const label = prop(node, "media_label", "The studio in late afternoon light");

  if (variant === "letterbox") {
    return (
      <Section label={eyebrow} wide size="sm">
        <figure>
          <Media ratio="21/9" subject={subject} label={label} zoom={false} className="min-h-72" />
          <figcaption className="mt-8 grid gap-6 border-t border-border pt-8 md:grid-cols-12">
            <Eyebrow className="md:col-span-3">{eyebrow}</Eyebrow>
            <h2 className="font-heading-set text-h3 text-balance md:col-span-5">{title}</h2>
            <div className="space-y-4 md:col-span-4">
              <p className="text-small text-muted text-pretty">{caption}</p>
              <Button variant="link" arrow className="px-0">{cta}</Button>
            </div>
          </figcaption>
        </figure>
      </Section>
    );
  }
  const right = variant === "caption_right";
  return (
    <section aria-label={eyebrow} className="tone-default">
      <div className="relative md:min-h-[600px] lg:min-h-[720px]">
        <Media ratio="4/3" subject={subject} label={label} zoom={false}
          className="rounded-none md:!absolute md:inset-0 md:h-full md:!aspect-auto" />
        <div className="page-x relative -mt-14 pb-10 md:absolute md:inset-x-0 md:bottom-0 md:mt-0 md:pb-14">
          <div className="container-wide">
            <div className={cn("max-w-md space-y-5 rounded-lg p-8 shadow-xl md:p-10",
              right ? "tone-inverse md:ml-auto" : "bg-bg/95 text-fg backdrop-blur")}>
              <Eyebrow>{eyebrow}</Eyebrow>
              <h2 className="font-heading-set text-h3 text-balance">{title}</h2>
              <p className="text-small text-muted text-pretty">{caption}</p>
              <Button arrow className="mt-2">{cta}</Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ rich text */
function RichText({ node }: NodeProps) {
  const variant = variantOf(node);
  const title = prop(node, "title", "Our standards, in plain words.");
  const h1 = prop(node, "heading_1", "What we look for");
  const h2 = prop(node, "heading_2", "What we will not do");
  const anchor = (k: number) => `${node.id}-part-${k}`;
  const list = listProp(node, "list", [
    "Materials we can trace back to where they began", "Makers who are paid fairly and on time",
    "Packaging that is recycled, or can be", "Quality that outlasts a single season",
  ]);
  const prose = (
    <div className="max-w-[66ch] space-y-6 text-body text-pretty">
      <p className="text-lead">{prop(node, "lead", "We are often asked how we decide what earns a place on our shelves. The honest answer is slowly, and with a short list of rules we have kept since the very first day.")}</p>
      <h3 id={anchor(1)} className="scroll-mt-24 pt-6 font-heading-set text-h3">{h1}</h3>
      <p className="text-fg/80">{prop(node, "body_1", "Before anything reaches you it passes through three sets of hands: the people who make it, the people who choose it and the people who pack it. Each of them is allowed to say no, and often does.")}</p>
      <ul className="space-y-3 pl-7">
        {list.map((l) => (
          <li key={l} className="relative before:absolute before:-left-7 before:top-[0.8em] before:h-px before:w-4 before:bg-fg">{l}</li>))}
      </ul>
      <h3 id={anchor(2)} className="scroll-mt-24 pt-6 font-heading-set text-h3">{h2}</h3>
      <p className="text-fg/80">{prop(node, "body_2", "We will not chase trends we do not believe in, discount so often that prices stop meaning anything, or add something new simply because there is space for it.")}</p>
      <figure className="my-10 border-y border-border py-8">
        <blockquote><p className="font-heading-set text-h3 italic text-balance">“{prop(node, "quote", "A shelf is not a space to fill. It is a promise to keep.")}”</p></blockquote>
        <figcaption className="mt-4 text-small text-muted">{prop(node, "quote_author", "From our first staff handbook")}</figcaption>
      </figure>
      <p className="text-fg/80">{prop(node, "body_3", "If you ever feel we have fallen short, tell us. Every message is read by someone on the team, and many of our best changes began as a note from a customer.")}</p>
    </div>
  );
  const eyebrow = prop(node, "eyebrow", "Standards");
  const meta = prop(node, "meta", "Updated September 2026");

  if (variant === "with_aside") {
    return (
      <Section label={title} wide>
        <div className="grid gap-12 lg:grid-cols-12 lg:gap-8">
          <aside className="lg:col-span-3">
            <div className="space-y-8 lg:sticky lg:top-24">
              <div className="space-y-2">
                <Eyebrow>{eyebrow}</Eyebrow>
                <p className="text-small text-muted">{meta}</p>
              </div>
              <nav aria-label="On this page" className="border-t border-border pt-6">
                <p className="mb-2 text-small font-semibold">On this page</p>
                <ul>
                  {[h1, h2].map((h, k) => (
                    <li key={h}><a href={`#${anchor(k + 1)}`} className="inline-flex min-h-11 items-center text-small text-muted transition-colors hover:text-fg">{h}</a></li>))}
                </ul>
              </nav>
            </div>
          </aside>
          <article className="lg:col-span-8 lg:col-start-5">
            <h2 className="mb-10 font-heading-set text-h1 text-balance">{title}</h2>
            {prose}
          </article>
        </div>
      </Section>
    );
  }
  return (
    <Section label={title}>
      <article className="mx-auto max-w-[66ch]">
        <header className="mb-12 space-y-5 border-b border-border pb-10">
          <Eyebrow>{eyebrow}</Eyebrow>
          <h2 className="font-heading-set text-h1 text-balance">{title}</h2>
          <p className="text-small text-muted">{meta}</p>
        </header>
        {prose}
      </article>
    </Section>
  );
}

/* ------------------------------------------------------------------ contact */
const controlCls = "w-full rounded-button border border-border bg-bg px-4 text-body text-fg placeholder:text-muted/70 transition-[border-color,box-shadow] duration-200 focus:border-ring focus:outline-none focus:ring-4 focus:ring-ring/15";

function useSent() {
  const [sent, setSent] = useState(false);
  return { sent, onSubmit: (e: FormEvent) => { e.preventDefault(); setSent(true); } };
}

function ContactSection({ node }: NodeProps) {
  const variant = variantOf(node, "split");
  const id = node.id;
  const title = prop(node, "title", "We would love to hear from you.");
  const topics = listProp(node, "topics", ["A general question", "An existing order", "Private events and bookings", "Press and partnerships"]);
  const details = [
    { icon: Mail, label: "Email", value: prop(node, "email", "hello@thehouse.studio") },
    { icon: Phone, label: "Phone", value: prop(node, "phone", "+44 20 7946 0321") },
    { icon: MapPin, label: "Visit", value: prop(node, "address", "14 Market Row, London E1 6QL") },
    { icon: Clock, label: "Hours", value: prop(node, "hours", "Mon to Sat, 9:00 to 18:00") },
  ];
  const { sent, onSubmit } = useSent();
  const form = (
    <form onSubmit={onSubmit} className="grid gap-5 sm:grid-cols-2" aria-label={prop(node, "form_title", "Send us a message")}>
      <Field id={`${id}-name`} label="Your name" placeholder="Alex Morgan" autoComplete="name" />
      <Field id={`${id}-email`} label="Email" type="email" placeholder="you@example.com" autoComplete="email" />
      <div className="space-y-2 sm:col-span-2">
        <label htmlFor={`${id}-topic`} className="block text-small font-semibold">What is it about?</label>
        <div className="relative">
          <select id={`${id}-topic`} className={cn(controlCls, "h-12 appearance-none pr-12")}>
            {topics.map((t) => <option key={t}>{t}</option>)}
          </select>
          <ChevronDown aria-hidden className="pointer-events-none absolute right-4 top-1/2 size-4 -translate-y-1/2 text-muted" />
        </div>
      </div>
      <div className="space-y-2 sm:col-span-2">
        <label htmlFor={`${id}-message`} className="block text-small font-semibold">Message</label>
        <textarea id={`${id}-message`} rows={5} placeholder="Tell us a little about what you have in mind" className={cn(controlCls, "resize-y py-3")} />
      </div>
      <div className="flex flex-col-reverse items-start gap-4 sm:col-span-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-caption text-muted" aria-live="polite">
          {sent ? "Thank you. We will reply within one working day." : prop(node, "privacy", "We only use your details to reply to you.")}
        </p>
        <Button type="submit" size="lg" arrow>{prop(node, "submit", "Send message")}</Button>
      </div>
    </form>
  );
  const eyebrow = prop(node, "eyebrow", "Contact");
  const intro = prop(node, "intro", "Questions about an order, a private booking or working together. Write to us and a real person will reply within one working day.");

  if (variant === "stacked") {
    return (
      <Section label={title}>
        <SectionHeader align="center" eyebrow={eyebrow} title={title} body={intro} />
        <dl className="mx-auto mb-14 grid max-w-5xl gap-px overflow-hidden rounded-card border border-border bg-border sm:grid-cols-2 lg:grid-cols-4">
          {details.map(({ icon: Icon, label, value }) => (
            <div key={label} className="space-y-2 bg-bg p-6">
              <dt className="flex items-center gap-2 text-caption font-semibold uppercase tracking-[0.16em] text-muted"><Icon aria-hidden className="size-4" />{label}</dt>
              <dd className="font-medium">{value}</dd>
            </div>))}
        </dl>
        <div className="mx-auto max-w-2xl">{form}</div>
      </Section>
    );
  }
  return (
    <Section label={title} tone="surface" wide>
      <div className="grid gap-12 lg:grid-cols-12 lg:gap-10">
        <div className="space-y-10 lg:col-span-5">
          <div className="space-y-5">
            <Eyebrow>{eyebrow}</Eyebrow>
            <h2 className="font-heading-set text-h2 text-balance">{title}</h2>
            <p className="max-w-md text-lead text-muted text-pretty">{intro}</p>
          </div>
          <dl className="grid gap-6 border-t border-border pt-8 sm:grid-cols-2 lg:grid-cols-1 xl:gap-5">
            {details.map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex gap-4">
                <span className="grid size-11 shrink-0 place-items-center rounded-pill border border-border bg-bg"><Icon aria-hidden className="size-4" /></span>
                <div className="min-w-0">
                  <dt className="text-caption font-semibold uppercase tracking-[0.16em] text-muted">{label}</dt>
                  <dd className="mt-1 break-words font-medium">{value}</dd>
                </div>
              </div>))}
          </dl>
        </div>
        <div className="rounded-lg border border-border bg-bg p-6 shadow-lg md:p-10 lg:col-span-7">
          <h3 className="mb-8 font-heading-set text-h3">{prop(node, "form_title", "Send us a message")}</h3>
          {form}
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ locations */
/** A drawn street map in the palette's own colours: suggests a place without pretending to be one. */
function MapArt({ label, pin, className, variant = 0 }: { label: string; pin: string; className?: string; variant?: number }) {
  const v = variant % 3;
  return (
    <div role="img" aria-label={label} className={cn("relative isolate overflow-hidden rounded-media border border-border bg-surface", className)}>
      <svg aria-hidden viewBox="0 0 400 300" preserveAspectRatio="xMidYMid slice" className="absolute inset-0 h-full w-full text-fg">
        <g transform={v === 1 ? "rotate(8 200 150)" : v === 2 ? "rotate(-6 200 150) translate(-30 10)" : undefined}>
          <rect x="235" y="30" width="120" height="80" rx="6" fill="currentColor" opacity="0.06" />
          <rect x="40" y="190" width="90" height="70" rx="6" fill="currentColor" opacity="0.06" />
          <path d="M-20 250 C 80 210, 140 280, 240 230 S 380 200, 440 240" fill="none" stroke="currentColor" strokeOpacity="0.1" strokeWidth="26" />
          <g fill="none" stroke="currentColor" strokeOpacity="0.07" strokeWidth="1">
            {range(9).map((i) => <path key={`v${i}`} d={`M${i * 50} -20 V 320`} />)}
            {range(7).map((i) => <path key={`h${i}`} d={`M-20 ${i * 50} H 420`} />)}
          </g>
          <g fill="none" stroke="currentColor" strokeOpacity="0.16" strokeLinecap="round">
            <path d="M-20 140 H 420" strokeWidth="7" />
            <path d="M210 -20 V 320" strokeWidth="7" />
            <path d="M-20 40 L 420 250" strokeWidth="4" />
          </g>
        </g>
      </svg>
      <div className="absolute left-[53%] top-[47%] flex -translate-x-1/2 -translate-y-full flex-col items-center">
        <span className="rounded-sm bg-bg px-3 py-1.5 text-caption font-semibold text-fg shadow-md">{pin}</span>
        <span className="mt-2 grid size-11 place-items-center rounded-pill bg-primary text-primary-fg shadow-lg ring-8 ring-primary/15">
          <MapPin aria-hidden className="size-5" />
        </span>
      </div>
    </div>
  );
}

function HoursTable({ days, times, className }: { days: string[]; times: string[]; className?: string }) {
  return (
    <table className={cn("w-full text-small", className)}>
      <caption className="sr-only">Opening hours</caption>
      <tbody>
        {days.map((d, i) => (
          <tr key={d} className="border-b border-border last:border-b-0">
            <th scope="row" className="py-3 pl-0 pr-4 text-left font-medium">{d}</th>
            <td className="py-3 pl-4 pr-0 text-right tabular-nums text-muted">{times[i] ?? ""}</td>
          </tr>))}
      </tbody>
    </table>
  );
}

function LocationHours({ node }: NodeProps) {
  const variant = variantOf(node, "single");
  const title = prop(node, "title", "Come and find us.");
  const names = listProp(node, "locations", ["Market Row", "Harbour Street", "The Arcade"]);
  const addressFallback = ["14 Market Row, London E1 6QL", "3 Harbour Street, Brighton BN1 1HL", "Unit 7, The Arcade, Bath BA1 1LN"];
  const days = listProp(node, "days", ["Monday to Friday", "Saturday", "Sunday"]);
  const times = listProp(node, "times", ["7:30 to 18:00", "8:30 to 17:00", "9:00 to 15:00"]);
  const directions = prop(node, "directions_cta", "Get directions");
  const eyebrow = prop(node, "eyebrow", "Visit");
  const intro = prop(node, "intro", "Pull up a chair, take your time and ask us anything. The kettle is usually on.");

  if (variant === "multiple") {
    return (
      <Section label={title} tone="alt" wide>
        <SectionHeader eyebrow={eyebrow} title={title} body={intro} />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {names.slice(0, 3).map((n, i) => (
            <article key={n} className="flex flex-col rounded-lg border border-border bg-bg p-4 shadow-sm">
              <MapArt label={`Map showing ${n}`} pin={n} variant={i} className="aspect-[4/3]" />
              <div className="flex flex-1 flex-col gap-4 px-2 pb-2 pt-6">
                <div>
                  <p className="text-caption font-semibold uppercase tracking-[0.16em] text-muted">{pad2(i)}</p>
                  <h3 className="mt-1 font-heading-set text-h4">{n}</h3>
                  <p className="mt-1 text-small text-muted">{nth(node, "address", i, addressFallback[i % 3])}</p>
                </div>
                <HoursTable days={days} times={times} />
                <Button variant="secondary" className="mt-auto w-full"><Navigation aria-hidden className="size-4" />{directions}</Button>
              </div>
            </article>))}
        </div>
      </Section>
    );
  }
  const name = names[0];
  return (
    <Section label={title} tone="alt" wide>
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-8">
        <MapArt label={`Map showing ${name}`} pin={name} className="min-h-80 lg:col-span-7 lg:min-h-full" />
        <div className="space-y-8 lg:col-span-5 lg:py-6 lg:pl-8">
          <div className="space-y-5">
            <Eyebrow>{eyebrow}</Eyebrow>
            <h2 className="font-heading-set text-h2 text-balance">{title}</h2>
            <p className="text-lead text-muted text-pretty">{intro}</p>
          </div>
          <div className="rounded-lg border border-border bg-bg p-6 shadow-sm md:p-8">
            <h3 className="font-heading-set text-h4">{name}</h3>
            <p className="mt-2 flex items-start gap-2 text-muted"><MapPin aria-hidden className="mt-1 size-4 shrink-0" />{nth(node, "address", 0, addressFallback[0])}</p>
            <HoursTable days={days} times={times} className="mt-6 border-t border-border" />
            <p className="mt-4 text-caption text-muted">{prop(node, "note", "Bank holidays 9:00 to 15:00. Dogs always welcome.")}</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Button arrow><Navigation aria-hidden className="size-4" />{directions}</Button>
              <Button variant="secondary"><Phone aria-hidden className="size-4" />{prop(node, "phone", "+44 20 7946 0321")}</Button>
            </div>
          </div>
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ newsletter */
function NewsletterSignup({ node }: NodeProps) {
  const variant = variantOf(node, "inline");
  const id = `${node.id}-email`;
  const title = prop(node, "title", "A short letter, once a month.");
  const body = prop(node, "body", "New arrivals before anyone else, seasonal notes from the team and the occasional invitation. Nothing more.");
  const perks = listProp(node, "perks", ["First look at new arrivals", "Invitations to tastings and events", "Unsubscribe in one click"]);
  const privacy = prop(node, "privacy", "We never share your address. Unsubscribe whenever you like.");
  const eyebrow = prop(node, "eyebrow", "The letter");
  const { sent, onSubmit } = useSent();
  const form = (stack?: boolean) => (
    <form onSubmit={onSubmit} aria-label={title} className="space-y-3">
      <label htmlFor={id} className={cn("block text-small font-semibold", !stack && "sr-only")}>Email address</label>
      <div className={cn("flex flex-col gap-3", !stack && "sm:flex-row")}>
        <input id={id} type="email" required autoComplete="email" aria-describedby={`${id}-note`}
          placeholder={prop(node, "placeholder", "you@example.com")} className={cn(controlCls, "h-12 min-h-12 min-w-0 flex-1")} />
        <Button type="submit" size="md" arrow className="shrink-0">{prop(node, "submit", "Subscribe")}</Button>
      </div>
      <p id={`${id}-note`} aria-live="polite" className={cn("flex items-center gap-2 text-caption text-muted", sent && "text-fg")}>
        {sent && <Check aria-hidden className="size-4" />}
        {sent ? "You are on the list. Check your inbox to confirm." : privacy}
      </p>
    </form>
  );
  const perkList = (className?: string) => (
    <ul className={cn("gap-3 text-small", className)}>
      {perks.map((p) => (
        <li key={p} className="flex items-center gap-3"><Check aria-hidden className="size-4 shrink-0" />{p}</li>))}
    </ul>
  );

  if (variant === "card") {
    return (
      <Section label={title} tone="surface">
        <div className="mx-auto grid max-w-5xl overflow-hidden rounded-lg border border-border bg-bg shadow-lg md:grid-cols-5">
          <Media ratio="4/5" subject={subjectOf(prop(node, "media", ""), "bag")} tone={1}
            label={prop(node, "media_label", "This month's letter, folded on the counter")}
            className="h-full rounded-none md:col-span-2 md:!aspect-auto" zoom={false} />
          <div className="space-y-6 p-8 md:col-span-3 md:p-12">
            <Eyebrow>{eyebrow}</Eyebrow>
            <h2 className="font-heading-set text-h3 text-balance">{title}</h2>
            <p className="text-muted text-pretty">{body}</p>
            {perkList("grid")}
            <div className="border-t border-border pt-6">{form(true)}</div>
          </div>
        </div>
      </Section>
    );
  }
  if (variant === "band") {
    return (
      <Section label={title} tone="inverse" size="lg" wide>
        <div className="grid items-end gap-12 lg:grid-cols-12 lg:gap-8">
          <div className="space-y-6 lg:col-span-7">
            <Eyebrow>{eyebrow}</Eyebrow>
            <h2 className="font-heading-set text-h1 text-balance">{title}</h2>
            {perkList("flex flex-wrap gap-x-8")}
          </div>
          <div className="space-y-5 lg:col-span-5 lg:col-start-8">
            <p className="text-lead text-muted text-pretty">{body}</p>
            {form()}
          </div>
        </div>
      </Section>
    );
  }
  return (
    <Section label={title} size="sm" wide>
      <div className="grid gap-8 border-y border-border py-12 md:py-16 lg:grid-cols-12 lg:items-center lg:gap-8">
        <div className="space-y-4 lg:col-span-5">
          <Eyebrow>{eyebrow}</Eyebrow>
          <h2 className="font-heading-set text-h3 text-balance">{title}</h2>
        </div>
        <div className="space-y-5 lg:col-span-6 lg:col-start-7">
          <p className="text-muted text-pretty">{body}</p>
          {form()}
        </div>
      </div>
    </Section>
  );
}

/* ------------------------------------------------------------------ feature split */
const ICONS = { leaf: Leaf, sparkles: Sparkles, recycle: Recycle, heart: Heart, truck: Truck, shield: ShieldCheck, gift: Gift, clock: Clock, award: Award, hand: Hand };
type IconName = keyof typeof ICONS;
const BENEFITS = [
  { title: "Sourced with intent", body: "Every material is traced to where it began, and every maker is someone we have met in person.", icon: "leaf" },
  { title: "Small batches, always", body: "We make a little at a time, so what reaches you is fresh, considered and never overstock.", icon: "sparkles" },
  { title: "Packed without plastic", body: "Paper, card and plant-based tape. Everything we send can be recycled or composted at home.", icon: "recycle" },
  { title: "Here when you need us", body: "Real people answer every message, usually within a few hours and always within a day.", icon: "heart" },
];

function FeatureSplit({ node }: NodeProps) {
  const variant = variantOf(node, "media_left");
  const titles = listProp(node, "items", BENEFITS.map((b) => b.title)).slice(0, 4);
  const icons = listProp(node, "icons", BENEFITS.map((b) => b.icon));
  const title = prop(node, "title", "Details you will only notice once you have them.");
  const subject = subjectOf(prop(node, "media", ""), "product");
  const label = prop(node, "media_label", "A finished piece, ready to be wrapped");
  const Icon = (i: number) => ICONS[(icons[i] in ICONS ? icons[i] : BENEFITS[i % 4].icon) as IconName];
  const header = (
    <div className="space-y-5">
      <Eyebrow>{prop(node, "eyebrow", "Why it feels different")}</Eyebrow>
      <h2 className="font-heading-set text-h2 text-balance">{title}</h2>
      <p className="text-lead text-muted text-pretty">{prop(node, "intro", "Four promises we keep with every order, visit and conversation.")}</p>
    </div>
  );
  const item = (t: string, i: number) => {
    const I = Icon(i);
    return (
      <li key={i} className="grid grid-cols-[auto_1fr] gap-5 border-t border-border pt-7">
        <span className="grid size-12 place-items-center rounded-card border border-border bg-bg"><I aria-hidden className="size-5" strokeWidth={1.75} /></span>
        <div className="space-y-2">
          <h3 className="font-heading-set text-h4">{t}</h3>
          <p className="text-muted text-pretty">{nth(node, "body", i, BENEFITS[i % 4].body)}</p>
        </div>
      </li>
    );
  };
  const badge = prop(node, "badge", "Finished by hand in our studio");

  if (variant === "grid") {
    return (
      <Section label={title} tone="alt" wide>
        <div className="grid gap-8 lg:grid-cols-12 lg:items-end">
          <div className="lg:col-span-6">{header}</div>
          <div className="lg:col-span-4 lg:col-start-9 lg:pb-2"><Button variant="secondary" arrow>{prop(node, "cta", "See how we work")}</Button></div>
        </div>
        <Media ratio="21/9" subject={subject} label={label} className="mt-12 min-h-64 md:mt-16" />
        <ul className="mt-12 grid gap-x-8 gap-y-10 sm:grid-cols-2 lg:grid-cols-4">{titles.map(item)}</ul>
      </Section>
    );
  }
  const right = variant === "media_right";
  return (
    <Section label={title} tone={right ? "surface" : "default"} wide>
      <div className="grid gap-12 lg:grid-cols-12 lg:gap-8">
        <div className={cn("lg:col-span-6 lg:self-start lg:sticky lg:top-24", right && "lg:order-2 lg:col-start-7")}>
          <div className="relative">
            <Media ratio="4/5" subject={subject} label={label} className="shadow-lg" />
            <p className="absolute bottom-4 left-4 rounded-sm bg-bg/95 px-4 py-2 text-small font-medium text-fg shadow-md">{badge}</p>
          </div>
        </div>
        <div className={cn("space-y-12 lg:col-span-5 lg:py-8", right ? "lg:order-1 lg:col-start-1" : "lg:col-start-8")}>
          {header}
          <ul className="space-y-7">{titles.map(item)}</ul>
          <Button arrow>{prop(node, "cta", "See how we work")}</Button>
        </div>
      </div>
    </Section>
  );
}

export const SECTIONS: SectionMap = {
  FAQ, BrandStory, MediaText, Manifesto, EditorialQuote, GalleryMasonry, ArticleGrid, ImageBand, RichText,
  ContactSection, LocationHours, NewsletterSignup, FeatureSplit,
};
