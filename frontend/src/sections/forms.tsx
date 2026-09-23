/**
 * Forms sections. Keys are the catalog's implementation.root names. See sections/README.md.
 *
 * Every id is prefixed with useId(): several variants render on one page (gallery, settings), and a
 * duplicated id would silently attach a label to the wrong input.
 */
import { useId, useState, type ReactNode } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import * as Switch from "@radix-ui/react-switch";
import {
  Bell, Building2, Check, ChevronDown, CreditCard, Eye, EyeOff, KeyRound, Lock, Mail, Palette, Shield, Store, Truck,
  User, Users, Wallet, X, Zap, type LucideIcon,
} from "lucide-react";
import { Avatar, Button, Media, imageAt, listProp, hrefOf, prop, subjectOf, variantOf } from "../ui";
import { cn } from "../lib/cn";
import { navigate } from "../site/router";
import type { NodeProps, SectionMap } from "./types";

/* ================================================================== field kit */

const control =
  "w-full rounded-button border border-border bg-bg text-body text-fg placeholder:text-muted/70 " +
  "transition-[border-color,box-shadow] duration-200 ease-brand hover:border-fg/30 " +
  "focus:border-ring focus:outline-none focus:ring-4 focus:ring-ring/15";

function Label({ htmlFor, children, optional, aside }: { htmlFor: string; children: ReactNode; optional?: boolean; aside?: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <label htmlFor={htmlFor} className="mb-0 block text-small font-semibold">
        {children}{optional && <span className="ml-1.5 font-normal text-muted">(optional)</span>}
      </label>
      {aside}
    </div>
  );
}

function TextField({ id, label, type = "text", placeholder, autoComplete, hint, defaultValue, prefix, trailing, optional, aside, size = "md", className, value, onChange, inputMode }: {
  id: string; label: string; type?: string; placeholder?: string; autoComplete?: string; hint?: string; defaultValue?: string;
  prefix?: string; trailing?: ReactNode; optional?: boolean; aside?: ReactNode; size?: "md" | "lg"; className?: string;
  value?: string; onChange?: (v: string) => void; inputMode?: "numeric" | "email" | "tel" | "text";
}) {
  const hintId = hint ? `${id}-hint` : undefined;
  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id} optional={optional} aside={aside}>{label}</Label>
      <div className="relative flex">
        {prefix && <span className="inline-flex items-center rounded-l-button border border-r-0 border-border bg-surface-alt px-3 text-small text-fg">{prefix}</span>}
        <input id={id} type={type} placeholder={placeholder} autoComplete={autoComplete} defaultValue={defaultValue} inputMode={inputMode}
          value={value} onChange={onChange ? (e) => onChange(e.target.value) : undefined} aria-describedby={hintId}
          className={cn(control, size === "lg" ? "h-12 px-4" : "h-11 px-3.5", prefix && "rounded-l-none", trailing && "pr-12")} />
        {trailing && <div className="absolute inset-y-0 right-1 flex items-center">{trailing}</div>}
      </div>
      {hint && <p id={hintId} className="text-caption text-muted">{hint}</p>}
    </div>
  );
}

function SelectField({ id, label, options, defaultValue, size = "md", className, autoComplete }: {
  id: string; label: string; options: string[]; defaultValue?: string; size?: "md" | "lg"; className?: string; autoComplete?: string;
}) {
  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <select id={id} defaultValue={defaultValue ?? options[0]} autoComplete={autoComplete}
          className={cn(control, "appearance-none pr-10", size === "lg" ? "h-12 px-4" : "h-11 px-3.5")}>
          {options.map((o) => <option key={o}>{o}</option>)}
        </select>
        <ChevronDown aria-hidden className="pointer-events-none absolute right-3.5 top-1/2 size-4 -translate-y-1/2 text-muted" />
      </div>
    </div>
  );
}

function CheckField({ id, label, description, defaultChecked, checked, onChange }: {
  id: string; label: ReactNode; description?: string; defaultChecked?: boolean; checked?: boolean; onChange?: (v: boolean) => void;
}) {
  return (
    <label htmlFor={id} className="flex min-h-6 cursor-pointer items-start gap-3">
      <input id={id} type="checkbox" defaultChecked={defaultChecked} checked={checked} onChange={onChange ? (e) => onChange(e.target.checked) : undefined}
        className="mt-px size-[18px] min-h-0 shrink-0 cursor-pointer rounded-sm p-0 accent-[var(--color-primary)]" />
      <span className="min-w-0">
        <span className="block text-small font-medium">{label}</span>
        {description && <span className="mt-0.5 block text-small text-muted">{description}</span>}
      </span>
    </label>
  );
}

function Toggle({ label, defaultChecked }: { label: string; defaultChecked?: boolean }) {
  return (
    <Switch.Root aria-label={label} defaultChecked={defaultChecked}
      className="relative inline-flex h-7 w-12 shrink-0 cursor-pointer items-center rounded-pill border border-transparent bg-fg/15 transition-colors duration-200 ease-brand data-[state=checked]:bg-primary">
      <Switch.Thumb className="block size-5 translate-x-1 rounded-pill bg-bg shadow-sm transition-transform duration-200 ease-brand data-[state=checked]:translate-x-6" />
    </Switch.Root>
  );
}

function PasswordField({ id, label, autoComplete, aside, value, onChange, hint, size }: {
  id: string; label: string; autoComplete: string; aside?: ReactNode; value?: string; onChange?: (v: string) => void; hint?: string; size?: "md" | "lg";
}) {
  const [show, setShow] = useState(false);
  return (
    <TextField id={id} label={label} type={show ? "text" : "password"} autoComplete={autoComplete} aside={aside} value={value} onChange={onChange}
      hint={hint} size={size} placeholder="••••••••"
      trailing={
        <button type="button" aria-label={show ? "Hide password" : "Show password"} aria-pressed={show} onClick={() => setShow((v) => !v)}
          className="grid size-10 place-items-center rounded-button text-muted transition-colors hover:text-fg">
          {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
        </button>} />
  );
}

/** Inline link that still meets the 24px target when it is laid out as a flex item. */
const linkCls = "inline-flex min-h-6 items-center text-small font-semibold text-fg underline decoration-fg/25 underline-offset-4 transition-colors hover:decoration-fg";

/** App-shell band for settings sections: tight rhythm, page-width container. */
function Shell({ label, children, className }: { label: string; children: ReactNode; className?: string }) {
  return (
    <section aria-label={label} className={cn("page-x py-4 md:py-5", className)}>
      <div className="container-page @container">{children}</div>
    </section>
  );
}

/* ================================================================== settings navigation */

const NAV_ICONS: Record<string, LucideIcon> = {
  general: Store, profile: User, notifications: Bell, security: Shield, billing: Wallet, team: Users, appearance: Palette,
  integrations: Zap, workspace: Building2, password: KeyRound,
};
const iconFor = (label: string): LucideIcon => NAV_ICONS[label.toLowerCase()] ?? Store;

function SettingsNav({ node }: NodeProps) {
  const variant = variantOf(node, "tabs");
  const items = listProp(node, "items", ["General", "Profile", "Notifications", "Security", "Billing", "Team"]);
  const [active, setActive] = useState(items[0]);
  const label = prop(node, "title", "Settings sections");

  const tabs = (className?: string) => (
    <div className={cn("-mx-1 overflow-x-auto px-1", className)}>
      <ul className="flex min-w-max gap-1 border-b border-border">
        {items.map((it) => (
          <li key={it}>
            <a href={`#${it.toLowerCase().replace(/\s+/g, "-")}`} aria-current={active === it ? "page" : undefined}
              onClick={(e) => { e.preventDefault(); setActive(it); }}
              className={cn("relative -mb-px flex min-h-11 items-center border-b-2 px-3 text-small font-medium transition-colors duration-200",
                active === it ? "border-fg text-fg" : "border-transparent text-muted hover:border-border hover:text-fg")}>
              {it}
              {it === "Team" && <span className="ml-2 rounded-pill bg-fg/[0.07] px-1.5 text-caption font-semibold tabular-nums text-fg">4</span>}
            </a>
          </li>))}
      </ul>
    </div>
  );

  if (variant === "vertical") {
    const groups = listProp(node, "groups", ["Account", "Workspace"]);
    const split = Math.ceil(items.length / 2);
    const grouped = [items.slice(0, split), items.slice(split)].filter((g) => g.length);
    return (
      <Shell label={label}>
        <nav aria-label={label}>
          {tabs("md:hidden")}
          <div className="hidden w-64 space-y-6 md:block">
            {grouped.map((g, gi) => (
              <div key={gi}>
                <p className="mb-2 px-3 text-caption font-semibold uppercase tracking-[0.14em] text-muted">{groups[gi] ?? ""}</p>
                <ul className="space-y-0.5">
                  {g.map((it) => {
                    const Icon = iconFor(it);
                    const on = active === it;
                    return (
                      <li key={it}>
                        <a href={`#${it.toLowerCase().replace(/\s+/g, "-")}`} aria-current={on ? "page" : undefined}
                          onClick={(e) => { e.preventDefault(); setActive(it); }}
                          className={cn("relative flex min-h-10 items-center gap-3 rounded-button px-3 text-small font-medium transition-colors duration-200",
                            on ? "bg-fg/[0.06] text-fg" : "text-muted hover:bg-fg/[0.04] hover:text-fg")}>
                          <Icon aria-hidden className={cn("size-4", on && "text-accent")} />{it}
                        </a>
                      </li>
                    );
                  })}
                </ul>
              </div>))}
          </div>
        </nav>
      </Shell>
    );
  }
  return <Shell label={label}><nav aria-label={label}>{tabs()}</nav></Shell>;
}

/* ================================================================== settings form */

function FormFooter({ note, cta, secondary }: { note: string; cta: string; secondary: string }) {
  const [saved, setSaved] = useState(false);
  return (
    <div className="flex flex-col gap-3 border-t border-border bg-bg/50 px-5 py-4 @xl:flex-row @xl:items-center @xl:justify-between md:px-6">
      <p className="text-small text-muted">{note}</p>
      <div className="flex gap-2 @xl:shrink-0">
        <Button variant="ghost" size="sm" onClick={() => setSaved(false)}>{secondary}</Button>
        <Button size="sm" onClick={() => setSaved(true)} aria-live="polite">
          {saved ? <><Check aria-hidden className="size-4" />Saved</> : cta}
        </Button>
      </div>
    </div>
  );
}

function InlineRow({ id, label, value, hint }: { id: string; label: string; value: string; hint?: string }) {
  const [editing, setEditing] = useState(false);
  const [v, setV] = useState(value);
  return (
    <div className="grid gap-3 px-5 py-4 @2xl:grid-cols-[12rem_minmax(0,1fr)_auto] @2xl:items-center md:px-6">
      <div>
        <p className="text-small font-semibold">{label}</p>
        {hint && <p className="text-caption text-muted">{hint}</p>}
      </div>
      {editing
        ? <div><label htmlFor={id} className="sr-only">{label}</label>
          <input id={id} value={v} onChange={(e) => setV(e.target.value)} autoFocus className={cn(control, "h-10 min-h-0 px-3 text-small")} /></div>
        : <p className="min-w-0 truncate text-small text-muted">{v}</p>}
      <div className="flex gap-2">
        {editing && <Button variant="ghost" size="sm" onClick={() => { setV(value); setEditing(false); }}>Cancel</Button>}
        <Button variant={editing ? "primary" : "secondary"} size="sm" onClick={() => setEditing((e) => !e)}
          aria-label={editing ? `Save ${label.toLowerCase()}` : `Edit ${label.toLowerCase()}`}>{editing ? "Save" : "Edit"}</Button>
      </div>
    </div>
  );
}

function SettingsForm({ node }: NodeProps) {
  const variant = variantOf(node);
  const uid = useId();
  const id = (k: string) => `${uid}-${k}`;
  const [bio, setBio] = useState("Morning person, slow brewer and keeper of the seasonal menu.");
  const cta = prop(node, "cta", "Save changes");
  const secondary = prop(node, "secondary_cta", "Cancel");

  if (variant === "card") {
    const title = prop(node, "title", "Notifications");
    const rows = [
      { label: "New orders", body: "A message the moment an order comes in.", on: true, icon: Mail },
      { label: "Weekly summary", body: "Sales, visitors and top products every Monday.", on: true, icon: Bell },
      { label: "Low stock", body: "When an item falls below its reorder point.", on: false, icon: Store },
      { label: "Product news", body: "Occasional updates about new features.", on: false, icon: Zap },
    ];
    return (
      <Shell label={title}>
        <div className="max-w-3xl overflow-hidden rounded-card border border-border bg-surface shadow-sm">
          <div className="px-5 pt-5 md:px-6 md:pt-6">
            <h2 className="text-body font-semibold tracking-tight">{title}</h2>
            <p className="mt-1 text-small text-muted">{prop(node, "description", "Choose what reaches your inbox. Critical account emails are always sent.")}</p>
          </div>
          <ul className="mt-4 divide-y divide-border border-t border-border">
            {rows.map((r) => {
              const Icon = r.icon;
              return (
                <li key={r.label} className="flex items-center gap-4 px-5 py-4 md:px-6">
                  <span aria-hidden className="hidden size-9 shrink-0 place-items-center rounded-button border border-border bg-bg text-muted @md:grid"><Icon className="size-4" /></span>
                  <div className="min-w-0 flex-1">
                    <p className="text-small font-semibold">{r.label}</p>
                    <p className="text-small text-muted">{r.body}</p>
                  </div>
                  <Toggle label={r.label} defaultChecked={r.on} />
                </li>
              );
            })}
          </ul>
          <FormFooter note="Sent to maya@northfield.co" cta={cta} secondary={secondary} />
        </div>
      </Shell>
    );
  }
  if (variant === "inline") {
    const title = prop(node, "title", "Account");
    return (
      <Shell label={title}>
        <div className="overflow-hidden rounded-card border border-border bg-surface shadow-sm">
          <div className="border-b border-border px-5 py-5 md:px-6">
            <h2 className="text-body font-semibold tracking-tight">{title}</h2>
            <p className="mt-1 text-small text-muted">{prop(node, "description", "Edit one detail at a time; each change saves on its own.")}</p>
          </div>
          <div className="divide-y divide-border">
            <InlineRow id={id("i-name")} label="Display name" value="Maya Chen" />
            <InlineRow id={id("i-email")} label="Email" value="maya@northfield.co" hint="Used to sign in" />
            <InlineRow id={id("i-phone")} label="Phone" value="+1 (415) 555-0142" />
            <InlineRow id={id("i-lang")} label="Language" value="English (United States)" />
          </div>
        </div>
      </Shell>
    );
  }
  const title = prop(node, "title", "Profile");
  return (
    <Shell label={title}>
      <div className="grid gap-6 @4xl:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] @4xl:gap-10">
        <div className="space-y-2 @4xl:pt-1">
          <h2 className="text-h4 font-heading-set">{title}</h2>
          <p className="text-small text-muted text-pretty">{prop(node, "description", "How you appear to your team and to guests who receive your messages.")}</p>
        </div>
        <form className="overflow-hidden rounded-card border border-border bg-surface shadow-sm" onSubmit={(e) => e.preventDefault()}>
          <div className="space-y-6 p-5 md:p-6">
            <div className="flex flex-wrap items-center gap-4">
              <Avatar name="Maya Chen" className="size-16 text-body" />
              <div className="space-y-2">
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm">Upload photo</Button>
                  <Button variant="ghost" size="sm">Remove</Button>
                </div>
                <p className="text-caption text-muted">Square JPG or PNG, at least 256px.</p>
              </div>
            </div>
            <div className="grid gap-5 @xl:grid-cols-2">
              <TextField id={id("first")} label="First name" defaultValue="Maya" autoComplete="given-name" />
              <TextField id={id("last")} label="Last name" defaultValue="Chen" autoComplete="family-name" />
            </div>
            <TextField id={id("email")} label="Email" type="email" defaultValue="maya@northfield.co" autoComplete="email"
              hint="We will send a confirmation link if you change it." />
            <TextField id={id("handle")} label="Username" prefix="@" defaultValue="mayabrews" autoComplete="username" />
            <div className="space-y-2">
              <Label htmlFor={id("bio")} aside={<span className="text-caption tabular-nums text-muted">{bio.length}/160</span>}>Bio</Label>
              <textarea id={id("bio")} rows={3} maxLength={160} value={bio} onChange={(e) => setBio(e.target.value)}
                className={cn(control, "min-h-24 resize-y px-3.5 py-2.5")} />
            </div>
            <div className="grid gap-5 @xl:grid-cols-2">
              <SelectField id={id("tz")} label="Time zone" options={["(GMT-08:00) Pacific Time", "(GMT+00:00) London", "(GMT+01:00) Paris", "(GMT+07:00) Ho Chi Minh City", "(GMT+09:00) Tokyo"]} />
              <SelectField id={id("lang")} label="Language" options={["English", "Français", "Deutsch", "Español", "Tiếng Việt", "日本語"]} />
            </div>
          </div>
          <FormFooter note="Your profile is visible to everyone in your workspace." cta={cta} secondary={secondary} />
        </form>
      </div>
    </Shell>
  );
}

/* ================================================================== danger zone */

function DangerZone({ node }: NodeProps) {
  const uid = useId();
  const title = prop(node, "title", "Danger zone");
  const cta = prop(node, "cta", "Delete workspace");
  const word = prop(node, "confirm_word", "DELETE");
  const [typed, setTyped] = useState("");
  const rows = [
    { title: "Transfer ownership", body: "Hand this workspace to another admin. You will keep member access.", action: "Transfer" },
    { title: "Archive workspace", body: "Hide the workspace and pause all activity. You can restore it within 30 days.", action: "Archive" },
  ];
  const danger = "bg-danger text-bg shadow-sm hover:-translate-y-0.5 hover:shadow-md";
  return (
    <Shell label={title} className="pb-10 md:pb-14">
      <div className="overflow-hidden rounded-card border border-danger/40 bg-surface shadow-sm">
        <div className="border-b border-danger/20 bg-danger/[0.04] px-5 py-4 md:px-6">
          <h2 className="text-body font-semibold text-danger">{title}</h2>
          <p className="mt-1 text-small text-muted">{prop(node, "description", "These actions affect everyone in the workspace. Some cannot be undone.")}</p>
        </div>
        <ul className="divide-y divide-border">
          {rows.map((r) => (
            <li key={r.title} className="flex flex-col gap-3 px-5 py-4 @xl:flex-row @xl:items-center @xl:justify-between md:px-6">
              <div className="min-w-0"><p className="text-small font-semibold">{r.title}</p><p className="text-small text-muted">{r.body}</p></div>
              <Button variant="secondary" size="sm" className="self-start @xl:self-auto">{r.action}</Button>
            </li>))}
          <li className="flex flex-col gap-3 px-5 py-4 @xl:flex-row @xl:items-center @xl:justify-between md:px-6">
            <div className="min-w-0">
              <p className="text-small font-semibold">{cta}</p>
              <p className="text-small text-muted">{prop(node, "body", "Permanently remove the workspace, its orders, customers and files. This cannot be undone.")}</p>
            </div>
            <Dialog.Root onOpenChange={() => setTyped("")}>
              <Dialog.Trigger asChild><Button size="sm" className={cn(danger, "self-start @xl:self-auto")}>{cta}</Button></Dialog.Trigger>
              <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 z-50 bg-fg/40 backdrop-blur-sm" />
                <Dialog.Content role="alertdialog" className="fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-surface p-6 text-fg shadow-xl">
                  <Dialog.Title className="text-h4 font-heading-set">{cta}?</Dialog.Title>
                  <Dialog.Description className="mt-2 text-small text-muted">
                    This permanently deletes everything in the workspace. Type <strong className="font-semibold text-fg">{word}</strong> to confirm.
                  </Dialog.Description>
                  <div className="mt-5">
                    <label htmlFor={`${uid}-confirm`} className="sr-only">Type {word} to confirm</label>
                    <input id={`${uid}-confirm`} value={typed} onChange={(e) => setTyped(e.target.value)} autoComplete="off" className={cn(control, "h-11 px-3.5")} />
                  </div>
                  <div className="mt-6 flex justify-end gap-2">
                    <Dialog.Close asChild><Button variant="secondary" size="sm">Cancel</Button></Dialog.Close>
                    <Button size="sm" className={danger} disabled={typed !== word}>{cta}</Button>
                  </div>
                  <Dialog.Close asChild>
                    <button type="button" aria-label="Close" className="absolute right-3 top-3 grid size-9 place-items-center rounded-button text-muted hover:bg-fg/[0.06] hover:text-fg"><X className="size-4" /></button>
                  </Dialog.Close>
                </Dialog.Content>
              </Dialog.Portal>
            </Dialog.Root>
          </li>
        </ul>
      </div>
    </Shell>
  );
}

/* ================================================================== checkout */

const STEPS = ["Contact", "Shipping", "Delivery", "Payment"];

function Stepper({ steps, current }: { steps: string[]; current: number }) {
  return (
    <ol aria-label="Checkout progress" className="flex items-center gap-2 text-small">
      {steps.map((s, i) => (
        <li key={s} aria-current={i === current ? "step" : undefined} className={cn("flex items-center gap-2", i < steps.length - 1 && "flex-1")}>
          <span className={cn("grid size-6 shrink-0 place-items-center rounded-pill text-caption font-semibold tabular-nums transition-colors duration-300",
            i < current ? "bg-primary text-primary-fg" : i === current ? "border-2 border-primary text-fg" : "border border-border text-muted")}>
            {i < current ? <Check aria-hidden className="size-3.5" /> : i + 1}
          </span>
          <span className={cn("hidden font-medium sm:inline", i <= current ? "text-fg" : "text-muted")}>{s}</span>
          {i < steps.length - 1 && <span aria-hidden className={cn("h-px flex-1 transition-colors duration-300", i < current ? "bg-primary" : "bg-border")} />}
        </li>))}
    </ol>
  );
}

function StepSection({ n, title, aside, children, onFocus }: { n: number; title: string; aside?: ReactNode; children: ReactNode; onFocus: () => void }) {
  return (
    <fieldset className="min-w-0 space-y-5" onFocusCapture={onFocus}>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <legend className="float-left flex items-center gap-3 text-h4 font-heading-set">
          <span aria-hidden className="text-small font-semibold tabular-nums text-muted">{String(n).padStart(2, "0")}</span>{title}
        </legend>
        {aside}
      </div>
      <div className="clear-both space-y-5">{children}</div>
    </fieldset>
  );
}

function DeliveryOptions({ name, options, compact }: { name: string; options: { title: string; note: string; price: string; icon: LucideIcon }[]; compact?: boolean }) {
  return (
    <div className={cn(compact ? "grid gap-2 @xl:grid-cols-3" : "divide-y divide-border overflow-hidden rounded-button border border-border")}>
      {options.map((o, i) => {
        const Icon = o.icon;
        return (
          <label key={o.title}
            className={cn("mb-0 flex cursor-pointer items-center gap-3.5 bg-bg p-4 transition-[background-color,border-color,box-shadow] duration-200 has-[:checked]:bg-fg/[0.035] has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-ring has-[:focus-visible]:ring-inset",
              compact && "flex-col items-start gap-0 rounded-card border border-border has-[:checked]:border-primary has-[:checked]:ring-1 has-[:checked]:ring-primary")}>
            {compact ? (
              <>
                <span className="flex w-full items-center justify-between gap-3">
                  <input type="radio" name={name} value={o.title} defaultChecked={i === 0} className="size-[18px] min-h-0 shrink-0 p-0 accent-[var(--color-primary)]" />
                  <span className="text-small font-semibold tabular-nums">{o.price}</span>
                </span>
                <span className="mt-2 block text-small font-semibold">{o.title}</span>
                <span className="block text-caption text-muted">{o.note}</span>
              </>
            ) : (
              <>
                <input type="radio" name={name} value={o.title} defaultChecked={i === 0} className="size-[18px] min-h-0 shrink-0 p-0 accent-[var(--color-primary)]" />
                <Icon aria-hidden className="size-5 shrink-0 text-muted" />
                <span className="min-w-0 flex-1">
                  <span className="block text-small font-semibold">{o.title}</span>
                  <span className="block text-small text-muted">{o.note}</span>
                </span>
                <span className="text-small font-semibold tabular-nums">{o.price}</span>
              </>
            )}
          </label>
        );
      })}
    </div>
  );
}

const DELIVERY = [
  { title: "Standard", note: "3–5 business days", price: "Free", icon: Truck },
  { title: "Express", note: "1–2 business days", price: "$12.00", icon: Zap },
  { title: "Pick up in store", note: "Ready today after 2 pm", price: "Free", icon: Store },
];

function CardFields({ id, size }: { id: (k: string) => string; size: "md" | "lg" }) {
  return (
    <div className="space-y-5">
      <TextField id={id("card")} label="Card number" autoComplete="cc-number" inputMode="numeric" placeholder="1234 1234 1234 1234" size={size}
        trailing={<Lock aria-hidden className="mr-3 size-4 text-muted" />} />
      <div className="grid grid-cols-2 gap-4">
        <TextField id={id("exp")} label="Expiry" autoComplete="cc-exp" inputMode="numeric" placeholder="MM / YY" size={size} />
        <TextField id={id("cvc")} label="Security code" autoComplete="cc-csc" inputMode="numeric" placeholder="CVC" size={size} />
      </div>
    </div>
  );
}

function CheckoutForm({ node }: NodeProps) {
  const variant = variantOf(node);
  const uid = useId();
  const id = (k: string) => `${uid}-${k}`;
  const [step, setStep] = useState(0);
  const total = prop(node, "total", "$312.12");
  const cta = prop(node, "cta", `Pay ${total}`);
  const title = prop(node, "title", "Checkout");
  const secure = prop(node, "secure_note", "Payments are encrypted and processed securely. We never store your full card number.");
  const countries = ["United States", "Canada", "United Kingdom", "France", "Germany", "Australia", "Japan", "Vietnam"];

  const placeOrder = (
    <div className="space-y-4">
      <Button size="lg" className="w-full" type="submit"><Lock aria-hidden className="size-4" />{cta}</Button>
      <p className="flex items-start gap-2 text-caption text-muted"><Shield aria-hidden className="mt-0.5 size-3.5 shrink-0" />{secure}</p>
    </div>
  );

  if (variant === "express") {
    const wallets = listProp(node, "express_methods", ["Apple Pay", "Google Pay", "PayPal"]);
    return (
      <section aria-label={title} className="page-x py-10 md:py-14 [&_input:not([type=radio]):not([type=checkbox])]:bg-surface [&_select]:bg-surface">
        <div className="container-page @container">
          <div className="mx-auto max-w-xl">
            <div className="mb-6 space-y-3">
              <div className="flex items-center justify-between gap-4 text-small">
                <span className="font-semibold">{step < 2 ? "Step 1 of 2 · Your details" : "Step 2 of 2 · Payment"}</span>
                <span className="text-muted">About a minute</span>
              </div>
              <div role="progressbar" aria-label="Checkout progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={step < 2 ? 50 : 90}
                className="h-1.5 overflow-hidden rounded-pill bg-fg/[0.08]">
                <div className="h-full rounded-pill bg-primary transition-[width] duration-500 ease-brand" style={{ width: step < 2 ? "50%" : "90%" }} />
              </div>
            </div>
            <h1 className="font-heading-set text-h2">{title}</h1>
            <p className="mt-2 text-small text-muted">{prop(node, "subtitle", "Pay in one tap, or enter your details below.")}</p>

            <div className="mt-8 rounded-card border border-border bg-surface p-5 md:p-6">
              <p className="mb-3 text-center text-caption font-semibold uppercase tracking-[0.16em] text-muted">{prop(node, "express_title", "Express checkout")}</p>
              <div className="grid gap-2 @md:grid-cols-3">
                {wallets.map((w, i) => (
                  <Button key={w} variant={i === 0 ? "primary" : "secondary"} className="w-full"><Wallet aria-hidden className="size-4" />{w}</Button>))}
              </div>
            </div>
            <div className="my-8 flex items-center gap-4 text-caption font-semibold uppercase tracking-[0.16em] text-muted">
              <span aria-hidden className="h-px flex-1 bg-border" />or pay with card<span aria-hidden className="h-px flex-1 bg-border" />
            </div>

            <form className="space-y-8" onSubmit={(e) => e.preventDefault()}>
              <fieldset className="space-y-4" onFocusCapture={() => setStep(0)}>
                <legend className="mb-4 text-small font-semibold">Contact and delivery</legend>
                <TextField id={id("email")} label="Email" type="email" autoComplete="email" placeholder="you@example.com" hint="For your receipt and delivery updates." />
                <TextField id={id("name")} label="Full name" autoComplete="name" placeholder="Maya Chen" />
                <TextField id={id("addr")} label="Address" autoComplete="street-address" placeholder="Street, city and postcode" />
              </fieldset>
              <fieldset className="space-y-3" onFocusCapture={() => setStep(1)}>
                <legend className="mb-3 text-small font-semibold">Delivery</legend>
                <DeliveryOptions name={id("ship")} options={DELIVERY} compact />
              </fieldset>
              <fieldset className="space-y-4" onFocusCapture={() => setStep(2)}>
                <legend className="mb-4 text-small font-semibold">Card details</legend>
                <CardFields id={id} size="md" />
              </fieldset>
              {placeOrder}
            </form>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section aria-label={title} className="page-x py-10 md:py-14 [&_input:not([type=radio]):not([type=checkbox])]:bg-surface [&_select]:bg-surface">
      <div className="container-page @container">
        <div className="mx-auto max-w-2xl">
          <p className="flex items-center gap-2 text-caption font-semibold uppercase tracking-[0.16em] text-muted"><Lock aria-hidden className="size-3.5" />{prop(node, "eyebrow", "Secure checkout")}</p>
          <h1 className="mt-3 font-heading-set text-h2">{title}</h1>
          <div className="mt-6"><Stepper steps={STEPS} current={step} /></div>

          <form className="mt-10 space-y-12" onSubmit={(e) => e.preventDefault()}>
            <StepSection n={1} title="Contact" onFocus={() => setStep(0)}
              aside={<p className="text-small text-muted">Have an account? <a href="#" className="font-semibold text-fg underline decoration-fg/25 underline-offset-4 hover:decoration-fg">Sign in</a></p>}>
              <TextField id={id("email")} label="Email" type="email" autoComplete="email" placeholder="you@example.com" size="lg" />
              <CheckField id={id("news")} label="Email me about new arrivals and offers" defaultChecked />
            </StepSection>

            <StepSection n={2} title="Shipping address" onFocus={() => setStep(1)}>
              <SelectField id={id("country")} label="Country or region" options={countries} autoComplete="country-name" size="lg" />
              <div className="grid gap-4 @md:grid-cols-2">
                <TextField id={id("first")} label="First name" autoComplete="given-name" size="lg" />
                <TextField id={id("last")} label="Last name" autoComplete="family-name" size="lg" />
              </div>
              <TextField id={id("addr")} label="Address" autoComplete="address-line1" placeholder="Street and number" size="lg" />
              <TextField id={id("addr2")} label="Apartment, suite, etc." autoComplete="address-line2" optional size="lg" />
              <div className="grid gap-4 @md:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
                <TextField id={id("city")} label="City" autoComplete="address-level2" size="lg" />
                <TextField id={id("zip")} label="Postal code" autoComplete="postal-code" size="lg" />
              </div>
              <TextField id={id("phone")} label="Phone" type="tel" autoComplete="tel" optional size="lg" hint="Only used if the courier needs to reach you." />
            </StepSection>

            <StepSection n={3} title="Delivery method" onFocus={() => setStep(2)}>
              <DeliveryOptions name={id("ship")} options={DELIVERY} />
            </StepSection>

            <StepSection n={4} title="Payment" onFocus={() => setStep(3)}
              aside={<p className="flex items-center gap-1.5 text-small text-muted"><CreditCard aria-hidden className="size-4" />All major cards</p>}>
              <div className="rounded-card border border-border p-5">
                <CardFields id={id} size="lg" />
                <div className="mt-5"><TextField id={id("cname")} label="Name on card" autoComplete="cc-name" size="lg" /></div>
              </div>
              <CheckField id={id("bill")} label="Billing address is the same as shipping" defaultChecked />
            </StepSection>

            {placeOrder}
          </form>
        </div>
      </div>
    </section>
  );
}

/* ================================================================== auth */

function BrandMark({ name }: { name: string }) {
  return (
    <span className="inline-flex items-center gap-2.5 font-heading-set text-body">
      <span aria-hidden className="grid size-9 place-items-center rounded-button bg-primary text-small font-bold text-primary-fg">{name.charAt(0)}</span>
      {name}
    </span>
  );
}

function SocialButtons({ providers, verb }: { providers: string[]; verb: string }) {
  return (
    <div className={cn("grid gap-2", providers.length > 1 && "sm:grid-cols-2", providers.length > 2 && "sm:grid-cols-3")}>
      {providers.map((p) => (
        <Button key={p} variant="secondary" className="w-full" aria-label={`${verb} with ${p}`}>
          <span aria-hidden className="grid size-5 place-items-center rounded-pill bg-fg text-[11px] font-bold text-bg">{p.charAt(0)}</span>{p}
        </Button>))}
    </div>
  );
}

function Divider({ children }: { children: string }) {
  return (
    <div className="flex items-center gap-3 text-caption text-muted">
      <span aria-hidden className="h-px flex-1 bg-border" />{children}<span aria-hidden className="h-px flex-1 bg-border" />
    </div>
  );
}

const RULES: { label: string; test: (p: string) => boolean }[] = [
  { label: "8 or more characters", test: (p) => p.length >= 8 },
  { label: "A number", test: (p) => /\d/.test(p) },
  { label: "An uppercase letter", test: (p) => /[A-Z]/.test(p) },
];

function SignInFields({ node, id }: { node: NodeProps["node"]; id: (k: string) => string }) {
  return (
    <form className="space-y-5" onSubmit={(e) => { e.preventDefault(); const to = hrefOf(node, "cta"); if (to) navigate(to); }}>
      <TextField id={id("email")} label="Email" type="email" autoComplete="email" placeholder="you@example.com" />
      <PasswordField id={id("pw")} label="Password" autoComplete="current-password"
        aside={<a href="#" className={cn(linkCls, "text-caption font-medium")}>{prop(node, "forgot_link", "Forgot password?")}</a>} />
      <CheckField id={id("remember")} label="Keep me signed in on this device" />
      <Button type="submit" data-role="cta" className="w-full">{prop(node, "cta", "Sign in")}</Button>
    </form>
  );
}

function AuthForm({ node }: NodeProps) {
  const variant = variantOf(node, "signin");
  const uid = useId();
  const id = (k: string) => `${uid}-${k}`;
  const brand = prop(node, "brand", "Northfield");
  const providers = listProp(node, "social", ["Google", "Apple"]);
  const [pw, setPw] = useState("");
  const signup = variant === "signup";
  const title = prop(node, "title", signup ? "Create your account" : "Welcome back");
  const subtitle = prop(node, "subtitle", signup ? "Set up in under a minute. No card needed." : "Sign in to pick up where you left off.");
  const footer = (
    <p className="text-center text-small text-muted">
      {prop(node, "footer_prompt", signup ? "Already have an account?" : "New here?")}{" "}
      <a href="#" className="font-semibold text-fg underline decoration-fg/25 underline-offset-4 hover:decoration-fg">{prop(node, "footer_link", signup ? "Sign in" : "Create an account")}</a>
    </p>
  );
  const legal = (
    <p className="text-center text-caption text-muted text-pretty">
      {prop(node, "legal", "By continuing you agree to our")} <a href="#" className="underline underline-offset-2 hover:text-fg">Terms</a> and <a href="#" className="underline underline-offset-2 hover:text-fg">Privacy Policy</a>.
    </p>
  );

  if (variant === "split") {
    return (
      <section aria-label={title} className="page-x py-4 md:py-6">
        <div className="container-wide grid min-h-[min(820px,calc(100vh-3rem))] gap-6 lg:grid-cols-2">
          <div className="flex flex-col px-2 py-8 md:px-8">
            <BrandMark name={brand} />
            <div className="mx-auto my-auto w-full max-w-sm space-y-7 py-12">
              <div className="space-y-2">
                <h1 className="font-heading-set text-h2">{title}</h1>
                <p className="text-body text-muted">{subtitle}</p>
              </div>
              <SocialButtons providers={providers} verb="Sign in" />
              <Divider>or with email</Divider>
              <SignInFields node={node} id={id} />
              {footer}
            </div>
            {legal}
          </div>
          <div className="relative hidden lg:block">
            <Media ratio="auto" subject={subjectOf(prop(node, "media", ""), "space")} src={imageAt(node, "media")?.url} tone={1} label={prop(node, "media_label", `Inside ${brand}`)} zoom={false}
              className="!absolute inset-0 h-full" />
            <figure className="absolute inset-x-6 bottom-6 rounded-lg bg-bg/95 p-7 text-fg shadow-xl backdrop-blur">
              <blockquote className="font-heading-set text-h4 text-pretty">
                “{prop(node, "quote", "Everything we need to run the shop lives in one calm place. Mornings feel lighter.")}”
              </blockquote>
              <figcaption className="mt-5 flex items-center gap-3">
                <Avatar name={prop(node, "quote_author", "Elena Duarte")} className="size-10 text-caption" />
                <span className="text-small"><span className="block font-semibold">{prop(node, "quote_author", "Elena Duarte")}</span>
                  <span className="block text-muted">{prop(node, "quote_role", "Owner, Casa Duarte")}</span></span>
              </figcaption>
            </figure>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section aria-label={title} className="page-x py-14 md:py-20">
      <div className="mx-auto w-full max-w-[440px] space-y-6">
        <div className="flex justify-center"><BrandMark name={brand} /></div>
        <div className="rounded-lg border border-border bg-surface p-6 shadow-sm sm:p-8">
          <div className="mb-7 space-y-2 text-center">
            <h1 className="font-heading-set text-h3">{title}</h1>
            <p className="text-small text-muted">{subtitle}</p>
          </div>
          {signup ? (
            <div className="space-y-6">
              <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
                <TextField id={id("name")} label="Full name" autoComplete="name" placeholder="Maya Chen" />
                <TextField id={id("email")} label="Work or personal email" type="email" autoComplete="email" placeholder="you@example.com" />
                <div className="space-y-3">
                  <PasswordField id={id("pw")} label="Password" autoComplete="new-password" value={pw} onChange={setPw} />
                  <div aria-hidden className="grid grid-cols-3 gap-1.5">
                    {RULES.map((r, i) => (
                      <span key={r.label} className={cn("h-1 rounded-pill transition-colors duration-300",
                        RULES.filter((x) => x.test(pw)).length > i ? "bg-success" : "bg-fg/10")} />))}
                  </div>
                  <ul className="grid gap-1 text-caption" aria-label="Password requirements">
                    {RULES.map((r) => {
                      const ok = r.test(pw);
                      return (
                        <li key={r.label} className={cn("flex items-center gap-2", ok ? "text-success" : "text-muted")}>
                          {ok ? <Check aria-hidden className="size-3.5" /> : <span aria-hidden className="mx-1 size-1.5 rounded-pill bg-current" />}
                          {r.label}<span className="sr-only">{ok ? " (met)" : " (not met)"}</span>
                        </li>
                      );
                    })}
                  </ul>
                </div>
                <CheckField id={id("terms")} label={<>I agree to the <a href="#" className="underline underline-offset-2">Terms</a> and <a href="#" className="underline underline-offset-2">Privacy Policy</a></>} />
                <Button type="submit" className="w-full">{prop(node, "cta", "Create account")}</Button>
              </form>
              <Divider>or sign up with</Divider>
              <SocialButtons providers={providers} verb="Sign up" />
            </div>
          ) : (
            <div className="space-y-6">
              <SocialButtons providers={providers} verb="Sign in" />
              <Divider>or with email</Divider>
              <SignInFields node={node} id={id} />
            </div>
          )}
        </div>
        {footer}
        {!signup && legal}
      </div>
    </section>
  );
}

export const SECTIONS: SectionMap = { SettingsNav, SettingsForm, DangerZone, CheckoutForm, AuthForm };
