/** Structure and navigation sections. Keys are the catalog's implementation.root names. See sections/README.md. */
import { forwardRef, useEffect, useState, type ButtonHTMLAttributes, type ComponentType, type ReactNode } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as Tooltip from "@radix-ui/react-tooltip";
import {
  ArrowRight, Calendar, ChartColumn, ChevronLeft, ChevronRight, ChevronsUpDown, CreditCard, Download, Ellipsis,
  Globe, House, Inbox, LayoutDashboard, LifeBuoy, Mail, Menu, Package, Plus, Receipt, Search, Settings,
  Share2, ShoppingBag, SlidersHorizontal, Sparkles, Store, User, UserPlus, Users, X, type LucideProps,
} from "lucide-react";
import { Avatar, Button, Eyebrow, Media, Section, listProp, prop, variantOf } from "../ui";
import { cn } from "../lib/cn";
import type { NodeProps, SectionMap } from "./types";

type Icon = ComponentType<LucideProps>;
type Subject = Parameters<typeof Media>[0]["subject"];
const slug = (s: string) => `#${s.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;

/** Sheet and toast motion. Kept local so the primitives file stays untouched; skipped under reduced motion. */
const MOTION_CSS = `
@keyframes uib-sheet-right { from { transform: translateX(100%); } }
@keyframes uib-sheet-left { from { transform: translateX(-100%); } }
@keyframes uib-overlay { from { opacity: 0; } }`;

function Logo({ name, mark = true, className }: { name: string; mark?: boolean; className?: string }) {
  return (
    <a href="#top" aria-label={`${name}, home`}
      className={cn("inline-flex min-h-11 shrink-0 items-center gap-2.5 rounded-button font-heading-set text-h4 leading-none text-fg", className)}>
      {mark && (
        <span aria-hidden className="grid size-8 place-items-center rounded-button bg-primary text-small font-bold text-primary-fg">
          {name.trim().charAt(0).toUpperCase()}
        </span>)}
      <span className="whitespace-nowrap">{name}</span>
    </a>
  );
}

/** Round icon-only control used across the bars. Always carries an aria-label; forwards its ref for Radix triggers. */
const IconButton = forwardRef<HTMLButtonElement, { label: string; children: ReactNode; className?: string } & ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ label, children, className, ...rest }, ref) => (
    <button ref={ref} type="button" aria-label={label} {...rest}
      className={cn("relative grid size-11 shrink-0 place-items-center rounded-pill text-fg transition-[background-color,transform] duration-200 ease-brand hover:bg-fg/[0.06] active:scale-95", className)}>
      {children}
    </button>
  ));
IconButton.displayName = "IconButton";

/* ================================================================== NavBar */
type NavAction = { kind: "cart" | "search" | "account" | "button"; label: string };
const classifyAction = (label: string): NavAction => ({
  label,
  kind: /cart|bag|basket/i.test(label) ? "cart" : /search/i.test(label) ? "search"
    : /sign in|log in|login|account|profile/i.test(label) ? "account" : "button",
});
const NAV_ACTIONS: Record<string, string[]> = {
  standard: ["Search", "Sign in", "Book a visit"],
  transparent: ["Sign in", "Book a visit"],
  minimal: ["Get in touch"],
  centered: ["Search", "Account", "Cart"],
};

function CartButton({ count }: { count: string }) {
  return (
    // data-cart-target: where the motion runtime flies an added product; data-cart-count: what it bumps.
    <IconButton label={`Cart, ${count} ${count === "1" ? "item" : "items"}`} data-cart-target="">
      <ShoppingBag className="size-5" aria-hidden />
      {count !== "0" && (
        <span aria-hidden data-cart-count="" className="absolute right-0.5 top-0.5 grid h-5 min-w-5 place-items-center rounded-pill bg-accent px-1 text-caption font-bold leading-none text-accent-fg tabular-nums ring-2 ring-bg">
          {count}
        </span>)}
    </IconButton>
  );
}

function NavLink({ label, className }: { label: string; className?: string }) {
  return (
    <a href={slug(label)}
      className={cn("relative inline-flex min-h-11 items-center whitespace-nowrap rounded-button px-3 text-small font-medium text-muted transition-colors duration-200 hover:text-fg",
        "after:absolute after:inset-x-3 after:bottom-2 after:h-px after:origin-left after:scale-x-0 after:bg-current after:transition-transform after:duration-300 after:ease-brand hover:after:scale-x-100 focus-visible:after:scale-x-100",
        className)}>{label}</a>
  );
}

function MobileMenu({ logo, links, buttons, side = "right" }: { logo: string; links: string[]; buttons: NavAction[]; side?: "left" | "right" }) {
  const [open, setOpen] = useState(false);
  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Trigger asChild>
        <IconButton label={open ? "Close menu" : "Open menu"} className="lg:hidden"><Menu className="size-5" aria-hidden /></IconButton>
      </Dialog.Trigger>
      <Dialog.Portal>
        <style>{MOTION_CSS}</style>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-fg/40 backdrop-blur-sm motion-safe:animate-[uib-overlay_300ms_ease-out]" />
        <Dialog.Content aria-describedby={undefined}
          className={cn("fixed inset-y-0 z-50 flex w-[min(24rem,88vw)] flex-col bg-bg p-6 text-fg shadow-xl focus:outline-none",
            side === "right" ? "right-0 motion-safe:animate-[uib-sheet-right_400ms_var(--ease-brand)]" : "left-0 motion-safe:animate-[uib-sheet-left_400ms_var(--ease-brand)]")}>
          <div className="flex items-center justify-between">
            <Dialog.Title className="font-heading-set text-h4">{logo}</Dialog.Title>
            <Dialog.Close asChild><IconButton label="Close menu"><X className="size-5" aria-hidden /></IconButton></Dialog.Close>
          </div>
          <nav aria-label="Mobile" className="mt-10">
            <ul className="divide-y divide-border border-y border-border">
              {links.map((l) => (
                <li key={l}>
                  <a href={slug(l)} onClick={() => setOpen(false)}
                    className="group flex min-h-14 items-center justify-between font-heading-set text-h4 transition-colors hover:text-muted">
                    {l}<ArrowRight aria-hidden className="size-4 -translate-x-1 opacity-0 transition-[opacity,transform] duration-300 ease-brand group-hover:translate-x-0 group-hover:opacity-100" />
                  </a>
                </li>))}
            </ul>
          </nav>
          <div className="mt-auto grid gap-3 pt-8">
            {buttons.map((b, i) => (
              <Button key={b.label} variant={i === buttons.length - 1 ? "primary" : "secondary"} className="w-full">{b.label}</Button>))}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

function NavBar({ node }: NodeProps) {
  const variant = variantOf(node);
  const logo = prop(node, "logo", "Maison Nord");
  const allLinks = listProp(node, "links", ["Shop", "Collections", "Journal", "About", "Visit"]);
  const links = variant === "minimal" ? allLinks.slice(0, 3) : allLinks;
  const actions = listProp(node, "actions", NAV_ACTIONS[variant] ?? NAV_ACTIONS.standard).map(classifyAction);
  const cartCount = prop(node, "cart_count", "2");
  const hasCart = actions.some((a) => a.kind === "cart");
  const hasSearch = actions.some((a) => a.kind === "search");
  const buttons = actions.filter((a) => a.kind === "button" || a.kind === "account");
  const primary = actions.filter((a) => a.kind === "button").at(-1);
  const account = actions.find((a) => a.kind === "account");
  const menu = <MobileMenu logo={logo} links={allLinks} buttons={buttons} side={variant === "centered" ? "left" : "right"} />;

  const searchBtn = hasSearch && <IconButton label="Search" className="hidden sm:grid"><Search className="size-5" aria-hidden /></IconButton>;
  const cartBtn = hasCart && <CartButton count={cartCount} />;

  if (variant === "centered") {
    // Boutique pattern: the wordmark owns the centre, links split either side of it.
    const half = Math.ceil(links.length / 2);
    return (
      <header aria-label="Site header" className="relative z-40 border-b border-border bg-bg page-x">
        <div className="container-wide grid h-20 grid-cols-[1fr_auto_1fr] items-center gap-4">
          <div className="flex items-center">
            {menu}
            <nav aria-label="Main" className="hidden items-center lg:flex">{links.slice(0, half).map((l) => <NavLink key={l} label={l} />)}</nav>
          </div>
          <Logo name={logo} mark={false} className="justify-self-center text-h3 tracking-tight" />
          <div className="flex items-center justify-end gap-1">
            <nav aria-label="More" className="mr-2 hidden items-center lg:flex">{links.slice(half).map((l) => <NavLink key={l} label={l} />)}</nav>
            {searchBtn}
            {account && <IconButton label={account.label} className="hidden sm:grid"><User className="size-5" aria-hidden /></IconButton>}
            {cartBtn}
            {primary && <Button size="sm" className="ml-2 hidden sm:inline-flex">{primary.label}</Button>}
          </div>
        </div>
      </header>
    );
  }

  if (variant === "transparent") {
    // Sits over a hero: no fill, no rule; the links float in a soft capsule so they read on any image band.
    return (
      <header aria-label="Site header" className="relative z-40 bg-transparent page-x">
        <div className="container-wide grid h-24 grid-cols-[1fr_auto] items-center gap-6 lg:grid-cols-[1fr_auto_1fr]">
          <Logo name={logo} />
          <nav aria-label="Main" className="hidden items-center rounded-pill bg-fg/[0.05] p-1 backdrop-blur-md lg:flex">
            {links.map((l) => (
              <a key={l} href={slug(l)}
                className="inline-flex min-h-10 items-center whitespace-nowrap rounded-pill px-4 text-small font-medium text-fg transition-[background-color,box-shadow] duration-200 ease-brand hover:bg-bg hover:shadow-sm">
                {l}</a>))}
          </nav>
          <div className="flex items-center justify-end gap-2">
            {account && <Button variant="ghost" size="sm" className="hidden rounded-pill lg:inline-flex">{account.label}</Button>}
            {cartBtn}
            {primary && <Button size="sm" arrow className="hidden rounded-pill sm:inline-flex">{primary.label}</Button>}
            {menu}
          </div>
        </div>
      </header>
    );
  }

  if (variant === "minimal") {
    return (
      <header aria-label="Site header" className="relative z-40 bg-bg page-x">
        <div className="container-page flex h-16 items-center justify-between gap-6">
          <Logo name={logo} className="text-body font-semibold" />
          <div className="flex items-center gap-2">
            <nav aria-label="Main" className="hidden items-center md:flex">{links.map((l) => <NavLink key={l} label={l} />)}</nav>
            {cartBtn}
            {primary && <Button variant="link" arrow className="ml-3 hidden min-h-11 px-0 text-small md:inline-flex">{primary.label}</Button>}
            <div className="md:hidden">{menu}</div>
          </div>
        </div>
      </header>
    );
  }

  return (
    <header aria-label="Site header" className="sticky top-0 z-40 border-b border-border bg-bg/90 backdrop-blur-md page-x">
      <div className="container-wide flex h-[72px] items-center gap-8">
        <Logo name={logo} />
        <nav aria-label="Main" className="hidden flex-1 items-center gap-1 lg:flex">{links.map((l) => <NavLink key={l} label={l} />)}</nav>
        <div className="ml-auto flex items-center gap-1.5">
          {searchBtn}
          {account && <Button variant="ghost" size="sm" className="hidden lg:inline-flex">{account.label}</Button>}
          {cartBtn}
          {primary && <Button size="sm" className="ml-1.5 hidden sm:inline-flex">{primary.label}</Button>}
          {menu}
        </div>
      </div>
    </header>
  );
}

/* ================================================================== Sidebar */
const ICONS: [RegExp, Icon][] = [
  [/overview|home|dashboard/i, LayoutDashboard], [/order|sale/i, Receipt], [/customer|client|member|team|people/i, Users],
  [/product|inventory|stock|catalog/i, Package], [/analytic|report|insight|metric/i, ChartColumn],
  [/message|inbox|chat|support/i, Inbox], [/booking|calendar|schedule|reservation|event/i, Calendar],
  [/billing|payment|invoice/i, CreditCard], [/store|shop|location/i, Store], [/setting|preference/i, Settings],
  [/help|guide|docs/i, LifeBuoy], [/campaign|marketing|mail/i, Mail],
];
const iconFor = (label: string): Icon => ICONS.find(([re]) => re.test(label))?.[1] ?? Sparkles;
/** "Orders (12)" -> label + count, so the model can write counts inline in a comma list. */
const parseItem = (raw: string) => {
  const m = raw.match(/^(.*?)\s*\((\d+)\)\s*$/);
  return m ? { label: m[1], count: m[2] } : { label: raw, count: "" };
};

type SideItem = { label: string; count: string };
function SideLink({ item, active, rail, stacked }: { item: SideItem; active: boolean; rail?: boolean; stacked?: boolean }) {
  const I = iconFor(item.label);
  const base = "group relative flex items-center rounded-button text-small font-medium transition-[background-color,color] duration-200 ease-brand";
  const state = active ? "bg-fg/[0.07] text-fg" : "text-muted hover:bg-fg/[0.04] hover:text-fg";
  if (stacked) {
    return (
      <a href={slug(item.label)} aria-current={active ? "page" : undefined}
        className={cn(base, state, "min-h-16 w-full flex-col justify-center gap-1 px-1 text-center text-caption")}>
        <I aria-hidden className="size-5" />
        <span className="max-w-full truncate">{item.label}</span>
        {item.count && <span aria-hidden className="absolute right-2.5 top-2 size-2 rounded-pill bg-accent" />}
      </a>
    );
  }
  if (rail) {
    return (
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <a href={slug(item.label)} aria-label={item.count ? `${item.label}, ${item.count} new` : item.label} aria-current={active ? "page" : undefined}
            className={cn(base, state, "size-11 justify-center")}>
            <I aria-hidden className="size-5" />
            {item.count && <span aria-hidden className="absolute right-2 top-2 size-2 rounded-pill bg-accent ring-2 ring-surface" />}
          </a>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content side="right" sideOffset={10} className="z-50 rounded-sm bg-fg px-2.5 py-1.5 text-caption font-semibold text-bg shadow-md">
            {item.label}
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    );
  }
  return (
    <a href={slug(item.label)} aria-current={active ? "page" : undefined} className={cn(base, state, "min-h-10 gap-3 px-3")}>
      {active && <span aria-hidden className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 rounded-pill bg-accent" />}
      <I aria-hidden className={cn("size-[18px] shrink-0 transition-colors", active ? "text-fg" : "text-muted group-hover:text-fg")} />
      <span className="flex-1 truncate">{item.label}</span>
      {item.count && (
        <span className={cn("rounded-pill px-2 py-0.5 text-caption font-semibold tabular-nums", active ? "bg-primary text-primary-fg" : "bg-surface-alt text-fg")}>
          {item.count}</span>)}
    </a>
  );
}

type SidebarData = {
  logo: string; workspace: string; items: SideItem[]; secondary: SideItem[]; active: string;
  user: string; role: string; usageTitle: string; usageBody: string;
};

function SidebarFull({ d, onNavigate }: { d: SidebarData; onNavigate?: () => void }) {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col gap-5 overflow-y-auto p-4" onClick={(e) => { if ((e.target as HTMLElement).closest("a")) onNavigate?.(); }}>
      <button type="button" aria-label={`Switch workspace, current ${d.logo}`}
        className="flex min-h-14 items-center gap-3 rounded-card p-2 text-left transition-colors hover:bg-fg/[0.04]">
        <span aria-hidden className="grid size-10 shrink-0 place-items-center rounded-button bg-primary font-heading-set text-body text-primary-fg shadow-sm">
          {d.logo.charAt(0).toUpperCase()}</span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-small font-semibold text-fg">{d.logo}</span>
          <span className="block truncate text-caption text-muted">{d.workspace}</span>
        </span>
        <ChevronsUpDown aria-hidden className="size-4 text-muted" />
      </button>

      <button type="button" className="flex min-h-11 items-center gap-2.5 rounded-button border border-border bg-bg px-3 text-small text-muted transition-[border-color,color] duration-200 hover:border-fg/30 hover:text-fg">
        <Search aria-hidden className="size-4" /><span className="flex-1 text-left">Search</span>
        <kbd className="rounded-sm border border-border bg-surface px-1.5 font-sans text-caption text-muted">⌘K</kbd>
      </button>

      <nav aria-label="Workspace" className="flex flex-col gap-6">
        {[["Workspace", d.items], ["Account", d.secondary]].map(([title, items]) => (
          <div key={title as string}>
            <p className="px-3 pb-2 text-caption font-semibold uppercase tracking-[0.14em] text-muted">{title as string}</p>
            <ul className="space-y-0.5">
              {(items as SideItem[]).map((it) => <li key={it.label}><SideLink item={it} active={it.label === d.active} /></li>)}
            </ul>
          </div>))}
      </nav>

      <div className="mt-auto space-y-4">
        <div className="rounded-card border border-border bg-bg p-4">
          <div className="flex items-center justify-between">
            <p className="text-small font-semibold text-fg">{d.usageTitle}</p>
            <span className="text-caption font-semibold tabular-nums text-muted">72%</span>
          </div>
          <div role="progressbar" aria-label={d.usageTitle} aria-valuenow={72} aria-valuemin={0} aria-valuemax={100}
            className="mt-3 h-1.5 overflow-hidden rounded-pill bg-surface-alt">
            <div className="h-full w-[72%] rounded-pill bg-accent" />
          </div>
          <p className="mt-3 text-caption text-muted">{d.usageBody}</p>
          <Button variant="secondary" size="sm" className="mt-3 w-full">Upgrade plan</Button>
        </div>
        <div className="flex items-center gap-3 border-t border-border pt-4">
          <Avatar name={d.user} className="size-10 bg-primary text-primary-fg" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-small font-semibold text-fg">{d.user}</p>
            <p className="truncate text-caption text-muted">{d.role}</p>
          </div>
          <IconButton label="Account options"><Ellipsis aria-hidden className="size-4" /></IconButton>
        </div>
      </div>
    </div>
  );
}

function SidebarRail({ d, stacked }: { d: SidebarData; stacked?: boolean }) {
  return (
    <div className={cn("flex h-full flex-col items-center gap-5 py-4", stacked ? "px-2" : "px-3")}>
      <span aria-hidden className="grid size-11 place-items-center rounded-button bg-primary font-heading-set text-body text-primary-fg shadow-sm">
        {d.logo.charAt(0).toUpperCase()}</span>
      <nav aria-label="Workspace" className="flex w-full flex-col items-center gap-1 border-t border-border pt-5">
        {d.items.map((it) => <SideLink key={it.label} item={it} active={it.label === d.active} rail={!stacked} stacked={stacked} />)}
      </nav>
      <div className="mt-auto flex w-full flex-col items-center gap-1 border-t border-border pt-4">
        {d.secondary.map((it) => <SideLink key={it.label} item={it} active={it.label === d.active} rail={!stacked} stacked={stacked} />)}
        <Avatar name={d.user} className="mt-3 size-10 bg-primary text-primary-fg" />
      </div>
    </div>
  );
}

function Sidebar({ node }: NodeProps) {
  const variant = variantOf(node);
  const [open, setOpen] = useState(false);
  const items = listProp(node, "items", ["Overview", "Orders (12)", "Customers", "Products", "Analytics", "Messages (3)"]).map(parseItem);
  const d: SidebarData = {
    logo: prop(node, "logo", "Maison Nord"),
    workspace: prop(node, "workspace", "Flagship · Pro plan"),
    items,
    secondary: listProp(node, "secondary_items", ["Settings", "Help"]).map(parseItem),
    active: parseItem(prop(node, "active", items[0]?.label ?? "Overview")).label,
    user: prop(node, "user_name", "Clara Moreau"),
    role: prop(node, "user_role", "Owner"),
    usageTitle: prop(node, "usage_title", "Monthly orders"),
    usageBody: prop(node, "usage_body", "7,240 of 10,000 used. Resets in 9 days."),
  };
  const floating = variant === "floating";
  const shell = floating
    ? "md:rounded-lg md:border md:border-border md:bg-surface md:shadow-lg"
    : "md:border-r md:border-border md:bg-surface";

  return (
    <Tooltip.Provider delayDuration={150}>
      <aside aria-label="Sidebar" className={cn("text-fg md:sticky md:top-0 md:flex md:h-screen md:min-h-[46rem] md:w-fit", floating && "md:p-3")}>
        {/* Phone: an app bar; the full sidebar opens as a drawer. */}
        <div className="flex h-16 items-center gap-3 border-b border-border bg-surface page-x md:hidden">
          <Dialog.Root open={open} onOpenChange={setOpen}>
            <Dialog.Trigger asChild>
              <IconButton label={open ? "Close navigation" : "Open navigation"} className="-ml-2"><Menu aria-hidden className="size-5" /></IconButton>
            </Dialog.Trigger>
            <Dialog.Portal>
              <style>{MOTION_CSS}</style>
              <Dialog.Overlay className="fixed inset-0 z-50 bg-fg/40 backdrop-blur-sm motion-safe:animate-[uib-overlay_300ms_ease-out]" />
              <Dialog.Content aria-describedby={undefined}
                className="fixed inset-y-0 left-0 z-50 w-[min(20rem,86vw)] overflow-y-auto bg-surface text-fg shadow-xl focus:outline-none motion-safe:animate-[uib-sheet-left_400ms_var(--ease-brand)]">
                <Dialog.Title className="sr-only">Navigation</Dialog.Title>
                <Dialog.Close asChild><IconButton label="Close navigation" className="absolute right-3 top-5"><X aria-hidden className="size-5" /></IconButton></Dialog.Close>
                <SidebarFull d={d} onNavigate={() => setOpen(false)} />
              </Dialog.Content>
            </Dialog.Portal>
          </Dialog.Root>
          <span className="flex-1 truncate font-heading-set text-h4">{d.active}</span>
          <IconButton label="Search"><Search aria-hidden className="size-5" /></IconButton>
          <Avatar name={d.user} className="size-9 bg-primary text-primary-fg" />
        </div>

        {/* Tablet: icon rail (compact keeps a labelled rail at every width). */}
        <div className={cn("hidden", shell, variant === "compact" ? "md:flex md:w-[88px]" : "md:flex md:w-[72px] lg:hidden")}>
          <SidebarRail d={d} stacked={variant === "compact"} />
        </div>
        {variant !== "compact" && (
          <div className={cn("hidden w-72 lg:flex", shell)}><SidebarFull d={d} /></div>)}
      </aside>
    </Tooltip.Provider>
  );
}

/* ================================================================== Breadcrumb */
function Breadcrumb({ node }: NodeProps) {
  const variant = variantOf(node);
  const trail = listProp(node, "items", ["Home", "Shop", "Tea", "Garden Reserve"]);
  const [expanded, setExpanded] = useState(false);
  const current = trail[trail.length - 1];
  const parents = trail.slice(0, -1);

  if (variant === "compact") {
    return (
      <nav aria-label="Breadcrumb" className="page-x py-3">
        <div className="container-page">
          <ol className="inline-flex max-w-full flex-wrap items-center gap-x-0.5 rounded-pill border border-border bg-surface px-2 text-small">
            {parents.map((c) => (
              <li key={c} className="flex items-center gap-0.5">
                <a href={slug(c)} className="inline-flex min-h-10 items-center rounded-pill px-2.5 text-muted transition-colors hover:bg-fg/[0.05] hover:text-fg">{c}</a>
                <span aria-hidden className="text-muted/60">/</span>
              </li>))}
            <li><span aria-current="page" className="inline-flex min-h-10 items-center px-2.5 font-semibold text-fg">{current}</span></li>
          </ol>
        </div>
      </nav>
    );
  }
  // Long trails collapse their middle on phones behind an expandable ellipsis.
  const collapsible = parents.length > 2 && !expanded;
  return (
    <nav aria-label="Breadcrumb" className="page-x pb-2 pt-6">
      <div className="container-page">
        <ol className="flex flex-wrap items-center gap-x-1 text-small">
          {parents.map((c, i) => {
            const hideOnPhone = collapsible && i > 0;
            return (
              <li key={c} className={cn("flex items-center gap-1", hideOnPhone && "hidden sm:flex")}>
                <a href={slug(c)} aria-label={i === 0 ? c : undefined}
                  className="inline-flex min-h-11 items-center gap-1.5 rounded-sm px-1.5 text-muted underline-offset-4 transition-colors hover:text-fg hover:underline">
                  {i === 0 ? <><House aria-hidden className="size-4" /><span className="hidden sm:inline">{c}</span></> : c}
                </a>
                <ChevronRight aria-hidden className="size-3.5 text-muted" />
              </li>
            );
          })}
          {collapsible && (
            <li className="flex items-center gap-1 sm:hidden">
              <IconButton label="Show full path" aria-expanded={false} onClick={() => setExpanded(true)} className="size-11 rounded-sm">
                <Ellipsis aria-hidden className="size-4 text-muted" /></IconButton>
              <ChevronRight aria-hidden className="size-3.5 text-muted" />
            </li>)}
          <li className="min-w-0">
            <span aria-current="page" className="inline-flex min-h-11 max-w-[22ch] items-center truncate px-1.5 font-semibold text-fg">{current}</span>
          </li>
        </ol>
      </div>
    </nav>
  );
}

/* ================================================================== PageHeader */
const actionIcon = (label: string): Icon | null =>
  /export|download/i.test(label) ? Download : /share/i.test(label) ? Share2 : /filter/i.test(label) ? SlidersHorizontal
    : /invite/i.test(label) ? UserPlus : /new|add|create/i.test(label) ? Plus : null;

function HeaderActions({ actions, size = "md" }: { actions: string[]; size?: "sm" | "md" }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {actions.map((a, i) => {
        const I = actionIcon(a);
        const primary = i === actions.length - 1;
        return (
          <Button key={a} size={size === "sm" ? "sm" : "md"} variant={primary ? "primary" : "secondary"} className={cn(size === "md" && "h-11 px-5 text-small")}>
            {I && <I aria-hidden className="size-4" />}{a}
          </Button>
        );
      })}
    </div>
  );
}

function PageHeader({ node }: NodeProps) {
  const variant = variantOf(node);
  const title = prop(node, "title", "Overview");
  const description = prop(node, "description", "How the shop is performing this month, across every channel.");
  const actions = listProp(node, "actions", ["Export", "New order"]);
  const trail = listProp(node, "breadcrumb", ["Maison Nord", "Dashboard"]);
  const status = prop(node, "status", "Live");
  const meta = listProp(node, "meta", ["Last 30 days", "Updated 2 minutes ago"]);
  const tabs = listProp(node, "tabs", ["Summary", "Sales (24)", "Customers", "Inventory (3)", "Payouts"]).map(parseItem);
  const [tab, setTab] = useState(0);

  if (variant === "compact") {
    return (
      <header aria-label={title} className="border-b border-border bg-bg page-x py-4">
        <div className="container-wide flex flex-wrap items-center justify-between gap-4">
          <div className="flex min-w-0 flex-wrap items-baseline gap-x-3 gap-y-1">
            <h1 className="font-heading-set text-h4">{title}</h1>
            <p className="text-small text-muted">{description}</p>
          </div>
          <HeaderActions actions={actions} size="sm" />
        </div>
      </header>
    );
  }

  return (
    <header aria-label={title} className={cn("bg-bg page-x pt-8", variant === "with_tabs" ? "border-b border-border" : "border-b border-border pb-8")}>
      <div className="container-wide">
        <nav aria-label="Breadcrumb">
          <ol className="flex flex-wrap items-center gap-1 text-small text-muted">
            {trail.map((c, i) => (
              <li key={c} className="flex items-center gap-1">
                {i > 0 && <ChevronRight aria-hidden className="size-3.5" />}
                {i === trail.length - 1
                  ? <span aria-current="page" className="font-medium text-fg">{c}</span>
                  : <a href={slug(c)} className="inline-flex min-h-6 items-center transition-colors hover:text-fg">{c}</a>}
              </li>))}
          </ol>
        </nav>
        <div className="mt-4 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div className="min-w-0 max-w-2xl">
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="font-heading-set text-h2">{title}</h1>
              {status && (
                <span className="inline-flex items-center gap-1.5 rounded-pill border border-border bg-surface px-2.5 py-1 text-caption font-semibold text-fg">
                  <span aria-hidden className="relative flex size-2">
                    <span className="absolute inset-0 rounded-pill bg-success opacity-60 motion-safe:animate-ping" />
                    <span className="relative size-2 rounded-pill bg-success" />
                  </span>{status}
                </span>)}
            </div>
            <p className="mt-2 text-body text-muted text-pretty">{description}</p>
            <ul className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-small text-muted">
              {meta.map((m, i) => (
                <li key={m} className="flex items-center gap-1.5">
                  {i === 0 ? <Calendar aria-hidden className="size-4" /> : <span aria-hidden className="size-1 rounded-pill bg-muted" />}{m}
                </li>))}
            </ul>
          </div>
          <HeaderActions actions={actions} />
        </div>
        {variant === "with_tabs" && (
          <nav aria-label={`${title} sections`} className="mt-8 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden overflow-x-auto">
            <ul className="flex gap-6">
              {tabs.map((t, i) => (
                <li key={t.label} className="shrink-0">
                  <a href={slug(t.label)} aria-current={i === tab ? "page" : undefined}
                    onClick={(e) => { e.preventDefault(); setTab(i); }}
                    className={cn("relative inline-flex min-h-12 items-center gap-2 text-small font-semibold transition-colors duration-200",
                      "after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:rounded-pill after:transition-colors",
                      i === tab ? "text-fg after:bg-fg" : "text-muted hover:text-fg after:bg-transparent hover:after:bg-border")}>
                    {t.label}
                    {t.count && <span className="rounded-pill bg-surface-alt px-1.5 py-0.5 text-caption tabular-nums text-fg">{t.count}</span>}
                  </a>
                </li>))}
            </ul>
          </nav>)}
      </div>
    </header>
  );
}

/* ================================================================== Footer */
const FOOTER_LINKS: Record<string, string[]> = {
  shop: ["New arrivals", "Best sellers", "Gift cards", "Subscriptions"],
  visit: ["Locations", "Opening hours", "Private events", "Wholesale"],
  about: ["Our story", "Journal", "Sustainability", "Careers"],
  help: ["Shipping", "Returns", "FAQ", "Contact us"],
  studio: ["Workshops", "Commissions", "Press", "Partners"],
};
const linksFor = (heading: string) => FOOTER_LINKS[heading.toLowerCase()] ?? ["Overview", "Latest", "Guides", "Contact"];

/** Brand glyphs are drawn inline: the icon set deliberately ships no logos. */
const SOCIAL: Record<string, ReactNode> = {
  instagram: <><rect x="3" y="3" width="18" height="18" rx="5" /><circle cx="12" cy="12" r="4" /><circle cx="17.5" cy="6.5" r="0.6" fill="currentColor" /></>,
  x: <path d="M4 4l16 16M20 4L4 20" />,
  youtube: <><rect x="2.5" y="5.5" width="19" height="13" rx="4" /><path d="M10 9.5v5l4.5-2.5z" fill="currentColor" /></>,
  pinterest: <><circle cx="12" cy="12" r="9" /><path d="M11 8.5c3-1 5 .5 5 3s-2 4-3.5 3.5M12 11l-2 9" /></>,
  tiktok: <path d="M14 3v11.5a3.5 3.5 0 1 1-3.5-3.5M14 3c.5 2.5 2.2 4 5 4.3" />,
  linkedin: <><rect x="3" y="3" width="18" height="18" rx="3" /><path d="M8 10.5V16M8 7.5v.1M12 16v-5.5M12 13c0-1.5 1-2.5 2.3-2.5S16.5 11.5 16.5 13v3" /></>,
};
function SocialLinks({ networks, className }: { networks: string[]; className?: string }) {
  return (
    <ul className={cn("flex flex-wrap gap-2", className)}>
      {networks.map((n) => (
        <li key={n}>
          <a href={slug(n)} aria-label={n}
            className="grid size-11 place-items-center rounded-pill border border-border text-fg transition-[background-color,border-color,transform] duration-200 ease-brand hover:-translate-y-0.5 hover:border-fg/40 hover:bg-fg/[0.05]">
            <svg viewBox="0 0 24 24" aria-hidden className="size-[18px]" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
              {SOCIAL[n.toLowerCase()] ?? <circle cx="12" cy="12" r="8" />}
            </svg>
          </a>
        </li>))}
    </ul>
  );
}

function FooterColumns({ columns, className }: { columns: string[]; className?: string }) {
  return (
    <div className={cn("grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-[repeat(var(--fcols),minmax(0,1fr))]", className)}
      style={{ ["--fcols" as string]: Math.min(columns.length, 5) }}>
      {columns.map((c) => (
        <div key={c}>
          <h2 className="text-small font-semibold text-fg">{c}</h2>
          <ul className="mt-3">
            {linksFor(c).map((l) => (
              <li key={l}>
                <a href={slug(l)} className="inline-flex min-h-10 items-center text-small text-muted transition-colors duration-200 hover:text-fg">{l}</a>
              </li>))}
          </ul>
        </div>))}
    </div>
  );
}

function LegalLinks() {
  return (
    <ul className="flex flex-wrap items-center gap-x-5">
      {["Privacy", "Terms", "Cookies"].map((l) => (
        <li key={l}><a href={slug(l)} className="inline-flex min-h-10 items-center text-small text-muted transition-colors hover:text-fg">{l}</a></li>))}
    </ul>
  );
}

function Footer({ node }: NodeProps) {
  const variant = variantOf(node);
  const logo = prop(node, "logo", "Maison Nord");
  const tagline = prop(node, "tagline", "Small-batch goods, chosen slowly and shared generously since 2014.");
  const legal = prop(node, "legal", `© 2026 ${logo}. All rights reserved.`);
  const social = listProp(node, "social", ["Instagram", "Pinterest", "YouTube"]);

  if (variant === "minimal") {
    return (
      <footer aria-label="Footer" className="border-t border-border bg-bg page-x py-6">
        <div className="container-wide flex flex-col items-center gap-3 text-center sm:flex-row sm:justify-between sm:text-left">
          <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
            <Logo name={logo} mark={false} className="text-body font-semibold" />
            <p className="text-small text-muted">{legal}</p>
          </div>
          <LegalLinks />
        </div>
      </footer>
    );
  }

  if (variant === "mega") {
    const columns = listProp(node, "columns", ["Shop", "Visit", "About", "Help"]);
    return (
      <footer aria-label="Footer" className="tone-inverse relative isolate overflow-hidden page-x pt-16 md:pt-24">
        <div className="container-wide">
          <div className="grid gap-10 border-b border-border pb-14 lg:grid-cols-2 lg:items-end">
            <div className="max-w-xl space-y-4">
              <Eyebrow>{prop(node, "newsletter_eyebrow", "The letter")}</Eyebrow>
              <h2 className="font-heading-set text-h2 text-balance">{prop(node, "newsletter_title", "First to know, never too often.")}</h2>
              <p className="text-lead text-muted">{prop(node, "newsletter_body", "New arrivals, seasonal releases and invitations to our tastings. Once a month.")}</p>
            </div>
            <form className="w-full lg:justify-self-end lg:max-w-lg" onSubmit={(e) => e.preventDefault()}>
              <label htmlFor="footer-email" className="sr-only">Email address</label>
              <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-2 sm:flex-row">
                <input id="footer-email" type="email" autoComplete="email" placeholder="you@example.com"
                  className="h-12 min-h-12 min-w-0 flex-1 rounded-button bg-transparent px-4 text-body text-fg placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-ring/40" />
                <Button type="submit" arrow>{prop(node, "newsletter_cta", "Subscribe")}</Button>
              </div>
              <p className="mt-3 text-small text-muted">No spam. Unsubscribe in one click.</p>
            </form>
          </div>

          <div className="grid gap-14 py-14 lg:grid-cols-12">
            <div className="space-y-6 lg:col-span-4">
              <Logo name={logo} />
              <p className="max-w-xs text-body text-muted">{tagline}</p>
              <address className="not-italic text-small text-muted">{prop(node, "contact", "14 Rue des Ateliers, Lyon · hello@maisonnord.com")}</address>
              <SocialLinks networks={social} />
            </div>
            <FooterColumns columns={columns} className="lg:col-span-8" />
          </div>

          <div className="flex flex-col gap-4 border-t border-border py-6 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-small text-muted">{legal}</p>
            <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
              <LegalLinks />
              <Button variant="secondary" size="sm" className="rounded-pill"><Globe aria-hidden className="size-4" /> English · USD</Button>
            </div>
          </div>
        </div>
        {/* Decorative wordmark, bled off the bottom edge. */}
        <div aria-hidden className="pointer-events-none -mb-[0.22em] select-none whitespace-nowrap text-center font-heading-set leading-none text-fg/[0.07]"
          style={{ fontSize: `min(16rem, ${(150 / Math.max(logo.length, 4)).toFixed(2)}vw)` }}>{logo}</div>
      </footer>
    );
  }

  const columns = listProp(node, "columns", ["Shop", "About", "Help"]);
  return (
    <footer aria-label="Footer" className="tone-surface border-t border-border page-x pt-16 md:pt-20">
      <div className="container-wide">
        <div className="grid gap-12 lg:grid-cols-12">
          <div className="space-y-5 lg:col-span-5">
            <Logo name={logo} />
            <p className="max-w-sm text-body text-muted">{tagline}</p>
            <SocialLinks networks={social} />
          </div>
          <FooterColumns columns={columns} className="lg:col-span-7" />
        </div>
        <div className="mt-14 flex flex-col gap-3 border-t border-border py-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-small text-muted">{legal}</p>
          <LegalLinks />
        </div>
      </div>
    </footer>
  );
}

/* ================================================================== AnnouncementBar */
function AnnouncementBar({ node }: NodeProps) {
  const variant = variantOf(node);
  const [open, setOpen] = useState(true);
  if (!open) return null;
  const message = prop(node, "message", "Free delivery on orders over $50, this week only.");
  const link = prop(node, "link_label", "Shop now");
  const close = (
    <IconButton label="Dismiss announcement" onClick={() => setOpen(false)} className="size-10 justify-self-end hover:bg-fg/10">
      <X aria-hidden className="size-4" />
    </IconButton>
  );

  if (variant === "marquee") {
    const messages = listProp(node, "messages", ["Free delivery over $50", "New seasonal collection is here", "Gift wrapping on every order", "Visit our new studio in the old town"]);
    return (
      <div role="region" aria-label="Announcement" className="tone-alt border-b border-border page-x">
        <div className="container-wide grid min-h-11 grid-cols-[1fr_auto] items-center gap-2">
          <p className="sr-only">{messages.join(". ")}</p>
          <div aria-hidden className="min-w-0">
            <div className="group relative flex overflow-hidden [mask-image:linear-gradient(90deg,transparent,black_8%,black_92%,transparent)]">
              {[0, 1].map((k) => (
                <div key={k} className="flex shrink-0 items-center gap-10 pr-10 motion-safe:animate-[uib-marquee_40s_linear_infinite] group-hover:[animation-play-state:paused]">
                  {messages.map((m) => (
                    <span key={m} className="flex items-center gap-10 whitespace-nowrap text-small font-medium text-fg">
                      {m}<span aria-hidden className="text-accent">✦</span></span>))}
                </div>))}
            </div>
          </div>
          {close}
        </div>
      </div>
    );
  }

  const accent = variant === "accent";
  return (
    <div role="region" aria-label="Announcement" className={cn(accent ? "tone-accent" : "tone-inverse", "page-x")}>
      <div className="container-wide grid min-h-11 grid-cols-[2.5rem_1fr_2.5rem] items-center gap-2">
        <span aria-hidden />
        <p className="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 py-2 text-center text-small">
          {accent && <span className="rounded-pill bg-fg px-2 py-0.5 text-caption font-bold uppercase tracking-wider text-bg">{prop(node, "badge", "New")}</span>}
          <span className="font-medium">{message}</span>
          <a href={slug(link)} className="group inline-flex min-h-6 items-center gap-1 font-semibold underline decoration-current/40 underline-offset-4 transition-colors hover:decoration-current">
            {link}<ArrowRight aria-hidden className="size-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
          </a>
        </p>
        {close}
      </div>
    </div>
  );
}

/* ================================================================== CategoryNav */
const CATEGORY_SUBJECTS: Subject[] = ["product", "cup", "leaf", "bag", "glass", "abstract", "space", "person"];

function CategoryNav({ node }: NodeProps) {
  const variant = variantOf(node);
  const items = listProp(node, "items", ["All", "New in", "Best sellers", "Seasonal", "Gifts", "Essentials", "Limited", "Accessories"]).map(parseItem);
  const initial = Math.max(0, items.findIndex((i) => i.label === prop(node, "active", "")));
  const [active, setActive] = useState(initial);
  const label = prop(node, "label", "Categories");
  const pick = (i: number) => (e: React.MouseEvent) => { e.preventDefault(); setActive(i); };
  // Scroll rail: momentum on touch, a soft fade at the trailing edge on small screens only.
  const rail = "flex snap-x overflow-x-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden [mask-image:linear-gradient(90deg,black_85%,transparent)] md:[mask-image:none]";

  if (variant === "visual") {
    return (
      <Section label={label} size="sm">
        <nav aria-label={label}>
          <ul className={cn(rail, "gap-5 py-2 md:flex-wrap md:justify-center md:gap-8")}>
            {items.map((it, i) => (
              <li key={it.label} className="shrink-0 snap-start">
                <a href={slug(it.label)} aria-current={i === active ? "page" : undefined} onClick={pick(i)}
                  className="group flex w-20 flex-col items-center gap-3 rounded-card text-center md:w-24">
                  <span className={cn("block w-full rounded-pill p-1 ring-2 transition-[box-shadow,transform] duration-300 ease-brand group-hover:-translate-y-1",
                    i === active ? "ring-primary" : "ring-transparent group-hover:ring-border")}>
                    <Media ratio="1/1" subject={CATEGORY_SUBJECTS[i % CATEGORY_SUBJECTS.length]} tone={i} label={it.label} className="rounded-pill" />
                  </span>
                  <span className={cn("text-small", i === active ? "font-semibold text-fg" : "font-medium text-muted group-hover:text-fg")}>{it.label}</span>
                </a>
              </li>))}
          </ul>
        </nav>
      </Section>
    );
  }

  if (variant === "pills") {
    return (
      <Section label={label} size="none" className="py-5">
        <nav aria-label={label} className="flex items-center gap-3">
          <ul className={cn(rail, "min-w-0 flex-1 gap-2")}>
            {items.map((it, i) => (
              <li key={it.label} className="shrink-0 snap-start">
                <a href={slug(it.label)} aria-current={i === active ? "page" : undefined} onClick={pick(i)}
                  className={cn("inline-flex min-h-11 items-center gap-2 whitespace-nowrap rounded-pill border px-5 text-small font-semibold transition-[background-color,color,border-color,transform] duration-200 ease-brand active:scale-[0.97]",
                    i === active ? "border-primary bg-primary text-primary-fg shadow-sm" : "border-border text-fg hover:border-fg/40 hover:bg-fg/[0.04]")}>
                  {it.label}
                  {it.count && <span className={cn("text-caption tabular-nums", i === active ? "text-primary-fg" : "text-muted")}>{it.count}</span>}
                </a>
              </li>))}
          </ul>
          <Button variant="secondary" size="icon" aria-label="Filters" className="hidden shrink-0 rounded-pill sm:inline-flex"><SlidersHorizontal aria-hidden className="size-4" /></Button>
        </nav>
      </Section>
    );
  }

  return (
    <Section label={label} size="none" className="border-b border-border">
      <nav aria-label={label} className="flex items-center justify-between gap-6">
        <ul className={cn(rail, "min-w-0 flex-1 gap-7")}>
          {items.map((it, i) => (
            <li key={it.label} className="shrink-0 snap-start">
              <a href={slug(it.label)} aria-current={i === active ? "page" : undefined} onClick={pick(i)}
                className={cn("relative inline-flex min-h-14 min-w-11 items-center justify-center gap-1.5 whitespace-nowrap text-small font-semibold transition-colors duration-200",
                  "after:absolute after:inset-x-0 after:-bottom-px after:h-0.5 after:origin-center after:bg-fg after:transition-transform after:duration-300 after:ease-brand",
                  i === active ? "text-fg after:scale-x-100" : "text-muted after:scale-x-0 hover:text-fg hover:after:scale-x-50")}>
                {it.label}
                {it.count && <sup className="text-caption font-medium text-muted">{it.count}</sup>}
              </a>
            </li>))}
        </ul>
        <a href="#all" className="group hidden min-h-11 shrink-0 items-center gap-1.5 text-small font-semibold text-fg md:inline-flex">
          {prop(node, "cta", "View all")}<ArrowRight aria-hidden className="size-4 transition-transform duration-200 group-hover:translate-x-0.5" />
        </a>
      </nav>
    </Section>
  );
}

/* ================================================================== Pagination */
/** 1 … 4 5 6 … 12; phones keep no siblings so the row always fits 390px. */
function pageList(current: number, total: number, siblings: number): (number | "gap")[] {
  const out: (number | "gap")[] = [];
  const lo = Math.max(2, current - siblings), hi = Math.min(total - 1, current + siblings);
  out.push(1);
  if (lo > 2) out.push("gap");
  for (let p = lo; p <= hi; p++) out.push(p);
  if (hi < total - 1) out.push("gap");
  if (total > 1) out.push(total);
  return out;
}

function useNarrow(query = "(max-width: 639px)") {
  const [narrow, setNarrow] = useState(() => typeof window !== "undefined" && window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const on = () => setNarrow(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [query]);
  return narrow;
}

const num = (v: string, fallback: number) => { const n = parseInt(v, 10); return Number.isFinite(n) && n > 0 ? n : fallback; };

function Pagination({ node }: NodeProps) {
  const variant = variantOf(node);
  const total = num(prop(node, "total_pages", "12"), 12);
  const perPage = num(prop(node, "per_page", "24"), 24);
  const totalItems = num(prop(node, "total_items", String(total * perPage - 10)), total * perPage - 10);
  const noun = prop(node, "item_label", "products");
  const [page, setPage] = useState(Math.min(total, num(prop(node, "current_page", "3"), 3)));
  const narrow = useNarrow();
  const from = (page - 1) * perPage + 1, to = Math.min(totalItems, page * perPage);

  if (variant === "load_more") {
    const shown = Math.min(totalItems, page * perPage);
    const pct = Math.round((shown / totalItems) * 100);
    return (
      <Section label="Pagination" size="sm">
        <div className="mx-auto flex max-w-sm flex-col items-center gap-5 text-center">
          <p className="text-small text-muted" aria-live="polite">
            Showing <span className="font-semibold text-fg tabular-nums">{shown}</span> of <span className="tabular-nums">{totalItems}</span> {noun}
          </p>
          <div role="progressbar" aria-label={`${noun} loaded`} aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}
            className="h-1 w-full overflow-hidden rounded-pill bg-surface-alt">
            <div className="h-full rounded-pill bg-fg transition-[width] duration-500 ease-brand" style={{ width: `${pct}%` }} />
          </div>
          <Button variant="secondary" disabled={shown >= totalItems} onClick={() => setPage((p) => Math.min(total, p + 1))} className="min-w-48">
            {shown >= totalItems ? "You have seen everything" : prop(node, "cta", "Load more")}
          </Button>
        </div>
      </Section>
    );
  }

  if (variant === "compact") {
    return (
      <Section label="Pagination" size="none" className="py-6">
        <nav aria-label="Pagination" className="flex items-center justify-between gap-4 border-t border-border pt-6">
          <p className="text-small text-muted" aria-live="polite">Page <span className="font-semibold text-fg tabular-nums">{page}</span> of <span className="tabular-nums">{total}</span></p>
          <div className="flex overflow-hidden rounded-button border border-border">
            <button type="button" aria-label="Previous page" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}
              className="grid size-11 place-items-center text-fg transition-colors hover:bg-fg/[0.05] disabled:text-muted disabled:opacity-50"><ChevronLeft aria-hidden className="size-4" /></button>
            <span aria-hidden className="w-px bg-border" />
            <button type="button" aria-label="Next page" disabled={page >= total} onClick={() => setPage((p) => p + 1)}
              className="grid size-11 place-items-center text-fg transition-colors hover:bg-fg/[0.05] disabled:text-muted disabled:opacity-50"><ChevronRight aria-hidden className="size-4" /></button>
          </div>
        </nav>
      </Section>
    );
  }

  return (
    <Section label="Pagination" size="sm">
      <nav aria-label="Pagination" className="flex flex-col items-center gap-5 md:flex-row md:justify-between">
        <p className="order-2 text-small text-muted md:order-1" aria-live="polite">
          Showing <span className="font-semibold text-fg tabular-nums">{from}–{to}</span> of <span className="tabular-nums">{totalItems}</span> {noun}
        </p>
        <div className="order-1 flex items-center gap-1 md:order-2 sm:gap-2">
          <Button variant="secondary" size="sm" aria-label="Previous page" disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="h-11 px-3 sm:px-4">
            <ChevronLeft aria-hidden className="size-4" /><span className="hidden sm:inline">Previous</span>
          </Button>
          <ul className="flex items-center gap-1">
            {pageList(page, total, narrow ? 0 : 1).map((p, i) => (
              <li key={p === "gap" ? `gap-${i}` : p}>
                {p === "gap"
                  ? <span aria-hidden className="grid size-11 place-items-center text-muted"><Ellipsis className="size-4" /></span>
                  : <button type="button" aria-label={`Page ${p}`} aria-current={p === page ? "page" : undefined} onClick={() => setPage(p)}
                      className={cn("grid size-11 place-items-center rounded-button text-small font-semibold tabular-nums transition-[background-color,color,transform] duration-200 ease-brand active:scale-95",
                        p === page ? "bg-primary text-primary-fg shadow-sm" : "text-fg hover:bg-fg/[0.06]")}>{p}</button>}
              </li>))}
          </ul>
          <Button variant="secondary" size="sm" aria-label="Next page" disabled={page >= total} onClick={() => setPage((p) => p + 1)} className="h-11 px-3 sm:px-4">
            <span className="hidden sm:inline">Next</span><ChevronRight aria-hidden className="size-4" />
          </Button>
        </div>
      </nav>
    </Section>
  );
}

/* ================================================================== SectionHeaderBlock */
function SectionHeaderBlock({ node }: NodeProps) {
  const variant = variantOf(node);
  const eyebrow = prop(node, "eyebrow", "The collection");
  const title = prop(node, "title", "Made in small batches, for the people who notice.");
  const body = prop(node, "body", "Every piece is sourced from growers and makers we know by name, then finished by hand in our studio.");
  const cta = prop(node, "cta", "Explore the range");

  if (variant === "centered") {
    return (
      <Section label={title} size="none" className="py-16 md:py-24">
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 text-center">
          <Eyebrow className="inline-flex items-center gap-3 text-fg">
            <span aria-hidden className="h-px w-8 bg-accent" />{eyebrow}<span aria-hidden className="h-px w-8 bg-accent" />
          </Eyebrow>
          <h2 className="font-heading-set text-h1 text-balance">{title}</h2>
          <p className="max-w-2xl text-lead text-muted text-pretty">{body}</p>
          <div className="mt-2 flex flex-wrap justify-center gap-3">
            <Button arrow>{cta}</Button>
            <Button variant="secondary">{prop(node, "secondary_cta", "How we source")}</Button>
          </div>
        </div>
      </Section>
    );
  }

  if (variant === "split") {
    return (
      <Section label={title} size="none" wide className="py-16 md:py-24">
        <div className="flex items-center justify-between gap-4 border-t border-fg pt-5">
          <Eyebrow className="text-fg">{eyebrow}</Eyebrow>
          <span className="font-heading-set text-small tabular-nums text-muted">{prop(node, "index", "01 / 04")}</span>
        </div>
        <div className="mt-10 grid gap-8 lg:grid-cols-12 lg:items-end lg:gap-12">
          <h2 className="font-heading-set text-h1 text-balance lg:col-span-7">{title}</h2>
          <div className="space-y-6 lg:col-span-4 lg:col-start-9">
            <p className="text-lead text-muted text-pretty">{body}</p>
            <Button variant="link" arrow className="min-h-11 px-0">{cta}</Button>
          </div>
        </div>
      </Section>
    );
  }

  return (
    <Section label={title} size="none" className="py-16 md:py-20">
      <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
        <div className="max-w-2xl space-y-4">
          <Eyebrow className="flex items-center gap-3 text-fg"><span aria-hidden className="h-px w-8 bg-accent" />{eyebrow}</Eyebrow>
          <h2 className="font-heading-set text-h2 text-balance">{title}</h2>
          <p className="text-lead text-muted text-pretty">{body}</p>
        </div>
        <Button variant="secondary" arrow className="shrink-0 self-start md:self-end">{cta}</Button>
      </div>
    </Section>
  );
}

/* ================================================================== StickyCtaBar */
function StickyCtaBar({ node }: NodeProps) {
  const variant = variantOf(node);
  const title = prop(node, "title", "Nº1 Signature");
  const summary = prop(node, "summary", "250 g · Whole bean · Ships tomorrow");
  const price = prop(node, "price", "$24");
  const cta = prop(node, "cta", "Add to bag");

  if (variant === "floating") {
    return (
      <section aria-label="Quick purchase" className="page-x py-6">
        <div className="sticky bottom-4 z-30 mx-auto flex max-w-2xl items-center gap-3 rounded-pill border border-border bg-bg/95 p-2 pl-2 shadow-xl backdrop-blur-md sm:gap-4">
          <Media ratio="1/1" subject="bag" label={title} zoom={false} className="w-12 shrink-0 rounded-pill" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-small font-semibold text-fg">{title}</p>
            <p className="truncate text-caption text-muted">{summary}</p>
          </div>
          <p className="hidden font-semibold tabular-nums text-fg sm:block">{price}</p>
          <Button className="shrink-0 rounded-pill px-5"><ShoppingBag aria-hidden className="size-4" /><span className="hidden sm:inline">{cta}</span><span className="sm:hidden">{price}</span></Button>
        </div>
      </section>
    );
  }

  if (variant === "promo") {
    return (
      <section aria-label="Offer" className="tone-inverse sticky bottom-0 z-30 page-x">
        <div className="container-wide flex flex-col gap-3 py-4 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
          <div className="flex min-w-0 items-center gap-3">
            <span aria-hidden className="grid size-10 shrink-0 place-items-center rounded-pill bg-surface-alt text-fg"><Sparkles className="size-4" /></span>
            <div className="min-w-0">
              <p className="font-semibold">{prop(node, "promo_title", "Your first order, 15% off")}</p>
              <p className="text-small text-muted">{prop(node, "promo_body", "Use code WELCOME at checkout. Ends Sunday.")}</p>
            </div>
          </div>
          <div className="flex shrink-0 gap-2">
            <Button variant="ghost" size="sm" className="h-11">{prop(node, "secondary_cta", "Details")}</Button>
            <Button size="sm" arrow className="h-11 flex-1 sm:flex-none">{prop(node, "promo_cta", "Claim offer")}</Button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section aria-label="Quick purchase" className="sticky bottom-0 z-30 border-t border-border bg-bg/95 page-x shadow-[0_-12px_32px_-16px_rgb(0_0_0/0.18)] backdrop-blur-md">
      <div className="container-wide flex items-center gap-4 py-3">
        <Media ratio="1/1" subject="bag" label={title} zoom={false} className="hidden w-14 shrink-0 rounded-sm sm:block" />
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold text-fg">{title}</p>
          <p className="truncate text-small text-muted">{summary}</p>
        </div>
        <div className="hidden text-right md:block">
          <p className="font-semibold tabular-nums text-fg">{price}</p>
          <p className="text-caption text-muted">{prop(node, "price_note", "Free delivery over $50")}</p>
        </div>
        <Button variant="secondary" className="hidden h-12 lg:inline-flex">{prop(node, "secondary_cta", "Save for later")}</Button>
        <Button className="h-12 shrink-0"><Plus aria-hidden className="size-4" />{cta}<span className="md:hidden">· {price}</span></Button>
      </div>
    </section>
  );
}

export const SECTIONS: SectionMap = {
  NavBar, Sidebar, Breadcrumb, PageHeader, Footer,
  AnnouncementBar, CategoryNav, Pagination, SectionHeaderBlock, StickyCtaBar,
};
