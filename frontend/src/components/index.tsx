import type { FC, ReactNode } from "react";
import type { RenderNode } from "../types";

export interface NodeProps { node: RenderNode; children: ReactNode; hasChildren: boolean; }
const p = (n: RenderNode, key: string, fallback: string) => (n.props[key] as string) ?? fallback;

const Inner: FC<{ children: ReactNode; wide?: boolean }> = ({ children, wide }) => (
  <div className="uib-inner" style={wide ? { maxWidth: "var(--container-wide)" } : undefined}>{children}</div>
);
const Eyebrow: FC<{ text: string }> = ({ text }) => <p className="uib-eyebrow">{text}</p>;
const Placeholder: FC<{ ratio?: string; label?: string }> = ({ ratio = "16/10", label }) => (
  <div className="uib-ph" style={{ aspectRatio: ratio }} role="img" aria-label={label ?? "illustration"} />
);
const Btn: FC<{ children: ReactNode; secondary?: boolean }> = ({ children, secondary }) => (
  <button type="button" className={secondary ? "uib-btn secondary" : "uib-btn"}>{children}</button>
);
const Grid: FC<{ cols: number; gap?: string; children: ReactNode }> = ({ cols, gap = "var(--spacing-lg)", children }) => (
  <div style={{ display: "grid", gridTemplateColumns: `repeat(${cols}, minmax(0,1fr))`, gap }}>{children}</div>
);
const repeat = (n: number) => Array.from({ length: n }, (_, i) => i);

/* ---------------------------------------------------------------- structure */
const Page: FC<NodeProps> = ({ children }) => <div data-page>{children}</div>;
const Main: FC<NodeProps> = ({ children }) => <main>{children}</main>;

const NavBar: FC<NodeProps> = ({ node }) => (
  <nav className="uib-nav" aria-label="Main">
    <strong>{p(node, "logo", "Acme")}</strong>
    <div>{["Product", "Pricing", "Docs", "Company"].map((l) => <a key={l} href={`#${l}`}>{l}</a>)}</div>
    <div style={{ display: "flex", gap: "var(--spacing-sm)" }}>
      <Btn secondary>Sign in</Btn><Btn>{p(node, "actions", "Get started")}</Btn>
    </div>
  </nav>
);

const Sidebar: FC<NodeProps> = ({ node }) => (
  <nav className="uib-sidebar" aria-label="Sections">
    <strong style={{ display: "block", marginBottom: "var(--spacing-lg)" }}>{p(node, "logo", "Acme")}</strong>
    {["Overview", "Reports", "Customers", "Billing", "Settings"].map((l, i) => (
      <a key={l} href={`#${l}`} aria-current={i === 0 ? "page" : undefined}>{l}</a>
    ))}
  </nav>
);

const Breadcrumb: FC<NodeProps> = () => (
  <nav aria-label="Breadcrumb" className="uib-section" style={{ paddingBlock: "var(--spacing-md)" }}>
    <Inner><p className="uib-muted">Home / Shoes / Running / <span style={{ color: "var(--color-fg)" }}>Aero Trail 3</span></p></Inner>
  </nav>
);

const PageHeader: FC<NodeProps> = ({ node }) => (
  <header className="uib-section" style={{ paddingBlock: "var(--spacing-lg)" }}>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: "var(--spacing-lg)", flexWrap: "wrap" }}>
      <div><h1 style={{ fontSize: "1.75rem" }}>{p(node, "title", "Overview")}</h1>
        <p className="uib-muted">{p(node, "description", "Everything happening across your workspace.")}</p></div>
      <div style={{ display: "flex", gap: "var(--spacing-sm)" }}><Btn secondary>Export</Btn><Btn>{p(node, "actions", "New report")}</Btn></div>
    </div>
  </header>
);

const Footer: FC<NodeProps> = ({ node }) => (
  <footer className="uib-section" style={{ paddingBlock: "var(--spacing-xl)", borderTop: "1px solid var(--color-border)" }}>
    <Inner>
      {node.props.variant !== "minimal" && (
        <Grid cols={4}>{["Product", "Company", "Resources", "Legal"].map((c) => (
          <div key={c}><strong>{c}</strong>
            <ul style={{ listStyle: "none", padding: 0, marginTop: "var(--spacing-sm)" }}>
              {repeat(3).map((i) => <li key={i} style={{ padding: "4px 0" }}><a href="#" className="uib-muted" style={{ textDecoration: "none" }}>{c} link {i + 1}</a></li>)}
            </ul></div>))}
        </Grid>)}
      <p className="uib-muted" style={{ marginTop: "var(--spacing-lg)" }}>© 2026 Acme, Inc.</p>
    </Inner>
  </footer>
);

/* ---------------------------------------------------------------- marketing */
const Hero: FC<NodeProps> = ({ node }) => {
  const stacked = node.props.variant === "centered" || node.props.variant === "aurora";
  const copy = (
    <div style={{ display: "grid", gap: "var(--spacing-md)", justifyItems: stacked ? "center" : "start", textAlign: stacked ? "center" : "left" }}>
      <Eyebrow text="New" />
      <h1>{p(node, "headline", "Design systems that build themselves")}</h1>
      <p className="uib-muted" style={{ fontSize: "1.125rem", maxWidth: "52ch" }}>
        {p(node, "subhead", "Describe the product you want. Get a responsive, accessible interface in seconds.")}</p>
      <div style={{ display: "flex", gap: "var(--spacing-sm)", flexWrap: "wrap", marginTop: "var(--spacing-sm)" }}>
        <Btn>{p(node, "primary_cta", "Start free")}</Btn><Btn secondary>{p(node, "secondary_cta", "Book a demo")}</Btn>
      </div>
    </div>
  );
  return (
    <section className="uib-section" aria-label="Hero" style={node.props.variant === "aurora"
      ? { background: "radial-gradient(1200px 500px at 50% -10%, var(--color-accent), transparent 70%)" } : undefined}>
      <Inner>{stacked ? <div style={{ display: "grid", gap: "var(--spacing-xl)", justifyItems: "center" }}>{copy}<Placeholder label="product preview" /></div>
        : <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--spacing-xl)", alignItems: "center" }}>{copy}<Placeholder label="product preview" /></div>}</Inner>
    </section>
  );
};

const SocialProof: FC<NodeProps> = () => (
  <section className="uib-section" style={{ paddingBlock: "var(--spacing-xl)" }} aria-label="Trusted by">
    <Inner><p className="uib-eyebrow" style={{ textAlign: "center", marginBottom: "var(--spacing-lg)" }}>Trusted by teams at</p>
      <div style={{ display: "flex", gap: "var(--spacing-xl)", justifyContent: "center", flexWrap: "wrap", opacity: .65 }}>
        {["Northwind", "Contoso", "Globex", "Initech", "Umbrella"].map((n) => <strong key={n}>{n}</strong>)}
      </div></Inner>
  </section>
);

const FeatureCard: FC<NodeProps> = ({ node }) => (
  <article className="uib-card">
    <div style={{ width: 40, height: 40, borderRadius: "var(--radius-base)", background: "var(--color-accent,var(--color-primary))", marginBottom: "var(--spacing-md)" }} />
    <h3>{p(node, "title", "Composable by default")}</h3>
    <p className="uib-muted" style={{ marginTop: 8 }}>{p(node, "body", "Every section is a semantic component with tokens applied automatically.")}</p>
  </article>
);

const FeatureBento: FC<NodeProps> = ({ node, children, hasChildren }) => (
  <section className="uib-section" aria-label="Features">
    <Inner><h2 style={{ marginBottom: "var(--spacing-lg)" }}>{p(node, "title", "Everything you need to ship")}</h2>
      {hasChildren ? children : <Grid cols={3}>{repeat(6).map((i) => (
        <article key={i} className="uib-card"><h3>Feature {i + 1}</h3><p className="uib-muted" style={{ marginTop: 8 }}>A capability that earns its place on the page.</p></article>))}</Grid>}
    </Inner>
  </section>
);

const ProductShowcase: FC<NodeProps> = () => (
  <section className="uib-section" aria-label="Product">
    <Inner><div className="uib-card" style={{ padding: "var(--spacing-md)" }}><Placeholder ratio="16/9" label="product screenshot" /></div></Inner>
  </section>
);

const Metrics: FC<NodeProps> = () => (
  <section className="uib-section" aria-label="Results">
    <Inner><Grid cols={4}>{[["3.2x", "faster delivery"], ["98%", "pass rate"], ["12k", "screens generated"], ["< 5s", "median render"]].map(([v, l]) => (
      <div key={l}><p style={{ fontSize: "2.5rem", fontWeight: 700, letterSpacing: "-0.03em" }}>{v}</p><p className="uib-muted">{l}</p></div>))}</Grid></Inner>
  </section>
);

const Testimonials: FC<NodeProps> = () => (
  <section className="uib-section" aria-label="Testimonials">
    <Inner><h2 style={{ marginBottom: "var(--spacing-lg)" }}>What teams say</h2>
      <Grid cols={3}>{repeat(3).map((i) => (
        <blockquote key={i} className="uib-card" style={{ margin: 0 }}>
          <p>“It replaced three weeks of design QA with a pipeline we can actually reason about.”</p>
          <footer style={{ display: "flex", gap: "var(--spacing-sm)", alignItems: "center", marginTop: "var(--spacing-md)" }}>
            <div style={{ width: 36, height: 36, borderRadius: "50%", background: "var(--color-border)" }} />
            <div><strong>Alex Rivera</strong><p className="uib-muted" style={{ fontSize: ".875rem" }}>Head of Design, Globex</p></div>
          </footer></blockquote>))}</Grid></Inner>
  </section>
);

const PricingTable: FC<NodeProps> = ({ node }) => (
  <section className="uib-section" aria-label="Pricing">
    <Inner><h2 style={{ marginBottom: "var(--spacing-lg)", textAlign: "center" }}>Simple pricing</h2>
      <Grid cols={3}>{[["Starter", "$0"], ["Team", "$49"], ["Scale", "$199"]].map(([name, price], i) => (
        <div key={name} className="uib-card" style={i === 1 && node.props.variant === "highlighted"
          ? { borderColor: "var(--color-primary)", boxShadow: "var(--shadow-lg)" } : undefined}>
          {i === 1 && <span className="uib-eyebrow">Most popular</span>}
          <h3>{name}</h3><p style={{ fontSize: "2rem", fontWeight: 700, margin: "var(--spacing-sm) 0" }}>{price}<span className="uib-muted" style={{ fontSize: "1rem", fontWeight: 400 }}>/mo</span></p>
          <ul style={{ listStyle: "none", padding: 0, margin: "var(--spacing-md) 0" }}>
            {repeat(4).map((f) => <li key={f} style={{ padding: "6px 0" }} className="uib-muted">Included capability {f + 1}</li>)}</ul>
          <Btn secondary={i !== 1}>Choose {name}</Btn></div>))}</Grid></Inner>
  </section>
);

const FAQ: FC<NodeProps> = () => (
  <section className="uib-section" aria-label="FAQ">
    <Inner><h2 style={{ marginBottom: "var(--spacing-lg)" }}>Frequently asked questions</h2>
      <div style={{ display: "grid", gap: "var(--spacing-sm)" }}>
        {["Can I bring my own design tokens?", "How does responsive behaviour work?", "Is the output accessible?", "Can I export the code?"].map((q) => (
          <details key={q} className="uib-card"><summary style={{ cursor: "pointer", fontWeight: 600 }}>{q}</summary>
            <p className="uib-muted" style={{ marginTop: "var(--spacing-sm)" }}>Yes. The deterministic engine expands your tokens and rules into every generated screen.</p></details>))}
      </div></Inner>
  </section>
);

const CTA: FC<NodeProps> = ({ node }) => (
  <section className="uib-section" aria-label="Call to action">
    <Inner><div className="uib-card" style={{ textAlign: "center", padding: "var(--spacing-2xl) var(--spacing-lg)", background: "var(--color-primary)", color: "var(--color-primary-fg)", borderColor: "transparent" }}>
      <h2>{p(node, "headline", "Ready to build your next screen?")}</h2>
      <p style={{ opacity: .85, marginTop: "var(--spacing-sm)" }}>Start free. No credit card required.</p>
      <div style={{ marginTop: "var(--spacing-lg)" }}>
        <button type="button" className="uib-btn" style={{ background: "var(--color-primary-fg)", color: "var(--color-primary)" }}>{p(node, "primary_cta", "Get started")}</button>
      </div></div></Inner>
  </section>
);

/* ---------------------------------------------------------------- commerce */
const ProductCard: FC<NodeProps> = ({ node }) => (
  <article className="uib-card" style={{ padding: "var(--spacing-md)" }}>
    <Placeholder ratio="1/1" label={p(node, "title", "product")} />
    {node.props.badge && <span className="uib-eyebrow" style={{ display: "block", marginTop: 8 }}>{p(node, "badge", "")}</span>}
    <h3 style={{ fontSize: "1rem", marginTop: "var(--spacing-sm)" }}>{p(node, "title", "Aero Trail 3")}</h3>
    <p className="uib-muted" style={{ fontSize: ".875rem" }}>Trail running</p>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "var(--spacing-sm)", gap: "var(--spacing-sm)" }}>
      <strong>{p(node, "price", "$140")}</strong><Btn>Add</Btn></div>
  </article>
);

const ProductGrid: FC<NodeProps> = ({ children, hasChildren }) => (
  <section className="uib-section" aria-label="Products"><Inner>
    {hasChildren ? children : <Grid cols={3}>{repeat(6).map((i) => <ProductCard key={i} node={{ id: `p${i}`, semantic_type: "product_card", implementation: "ProductCard", props: {}, tokens: {}, layout: null, animation: null, children: [] }} children={null} hasChildren={false} />)}</Grid>}
  </Inner></section>
);

const ProductDetail: FC<NodeProps> = ({ node }) => (
  <section className="uib-section" aria-label="Product detail"><Inner>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--spacing-xl)", alignItems: "start" }}>
      <div style={{ display: "grid", gap: "var(--spacing-sm)" }}>
        <Placeholder ratio="1/1" label="product photo" />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "var(--spacing-sm)" }}>
          {repeat(4).map((i) => <Placeholder key={i} ratio="1/1" label={`view ${i + 1}`} />)}</div>
      </div>
      <div style={{ display: "grid", gap: "var(--spacing-md)" }}>
        <Eyebrow text="Trail running" />
        <h1 style={{ fontSize: "2rem" }}>{p(node, "title", "Aero Trail 3")}</h1>
        <p style={{ fontSize: "1.5rem", fontWeight: 600 }}>{p(node, "price", "$140")}</p>
        <p className="uib-muted">A lightweight trail shoe with a rockered midsole for long descents and technical ground.</p>
        <fieldset style={{ border: 0, padding: 0 }}><legend style={{ fontWeight: 600, marginBottom: 8 }}>Size</legend>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>{["7", "8", "9", "10", "11", "12"].map((s) => (
            <label key={s} className="uib-btn secondary" style={{ minWidth: 56, justifyContent: "center" }}>
              <input type="radio" name="size" style={{ width: "auto", minHeight: 0, marginRight: 6 }} defaultChecked={s === "9"} />{s}</label>))}</div>
        </fieldset>
        <Btn>Add to cart</Btn>
        <p className="uib-muted" style={{ fontSize: ".875rem" }}>Free shipping over $75 · 30-day returns</p>
      </div></div></Inner></section>
);

const TrustSignals: FC<NodeProps> = () => (
  <section className="uib-section" style={{ paddingBlock: "var(--spacing-lg)" }} aria-label="Trust"><Inner>
    <Grid cols={4}>{[["Free shipping", "On orders over $75"], ["30-day returns", "No questions asked"], ["2-year warranty", "Covered by Acme"], ["Secure checkout", "Encrypted payments"]].map(([t, s]) => (
      <div key={t}><strong>{t}</strong><p className="uib-muted" style={{ fontSize: ".875rem" }}>{s}</p></div>))}</Grid></Inner></section>
);

const Reviews: FC<NodeProps> = () => (
  <section className="uib-section" aria-label="Reviews"><Inner>
    <h2 style={{ marginBottom: "var(--spacing-lg)" }}>Reviews</h2>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "var(--spacing-xl)" }}>
      <div><p style={{ fontSize: "3rem", fontWeight: 700 }}>4.6</p><p className="uib-muted">Based on 218 reviews</p>
        {[5, 4, 3, 2, 1].map((s) => (<div key={s} style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 6 }}>
          <span className="uib-muted" style={{ width: 12 }}>{s}</span>
          <div style={{ flex: 1, height: 8, background: "var(--color-border)", borderRadius: 999 }}>
            <div style={{ width: `${[72, 18, 6, 2, 2][5 - s]}%`, height: "100%", background: "var(--color-rating,var(--color-primary))", borderRadius: 999 }} /></div></div>))}
      </div>
      <div style={{ display: "grid", gap: "var(--spacing-md)" }}>{repeat(3).map((i) => (
        <article key={i} className="uib-card"><strong>Great on technical ground</strong>
          <p className="uib-muted" style={{ marginTop: 8 }}>Held up over 300km of rocky trail with no hot spots. Sizing runs true.</p></article>))}</div>
    </div></Inner></section>
);

const RelatedProducts: FC<NodeProps> = ({ children, hasChildren }) => (
  <section className="uib-section" aria-label="Related products"><Inner>
    <h2 style={{ marginBottom: "var(--spacing-lg)" }}>You might also like</h2>
    {hasChildren ? children : <Grid cols={4}>{repeat(4).map((i) => <ProductCard key={i} node={{ id: `r${i}`, semantic_type: "product_card", implementation: "ProductCard", props: {}, tokens: {}, layout: null, animation: null, children: [] }} children={null} hasChildren={false} />)}</Grid>}
  </Inner></section>
);

/* ---------------------------------------------------------------- data */
const Stats: FC<NodeProps> = () => (
  <section aria-label="Key metrics" style={{ padding: "0 var(--spacing-lg)" }}>
    <Grid cols={4}>{[["Revenue", "$48,210", "+12.4%"], ["Active users", "8,942", "+3.1%"], ["Churn", "1.8%", "-0.4%"], ["NPS", "62", "+5"]].map(([l, v, d]) => (
      <div key={l} className="uib-card"><p className="uib-muted" style={{ fontSize: ".875rem" }}>{l}</p>
        <p style={{ fontSize: "1.75rem", fontWeight: 700, margin: "4px 0" }}>{v}</p>
        <p style={{ fontSize: ".875rem", color: String(d).startsWith("-") ? "var(--color-muted)" : "var(--color-accent,var(--color-primary))" }}>{d} vs last month</p></div>))}</Grid>
  </section>
);

const ChartPanel: FC<NodeProps> = ({ node }) => {
  const pts = [18, 32, 24, 46, 38, 62, 54, 71, 66, 84, 78, 92];
  const d = pts.map((v, i) => `${(i / (pts.length - 1)) * 100},${100 - v}`).join(" ");
  return (
    <section aria-label="Trend" style={{ padding: "0 var(--spacing-lg)" }}>
      <div className="uib-card"><div style={{ display: "flex", justifyContent: "space-between", marginBottom: "var(--spacing-md)" }}>
        <div><h3>Revenue over time</h3><p className="uib-muted" style={{ fontSize: ".875rem" }}>Last 12 months</p></div>
        <Btn secondary>Last 12 months</Btn></div>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" style={{ width: "100%", height: 220 }} role="img" aria-label="Revenue trend chart">
          <polyline points={d} fill="none" stroke="var(--color-primary)" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
          <polygon points={`0,100 ${d} 100,100`} fill="var(--color-primary)" opacity={node.props.variant === "area" ? .12 : 0} />
        </svg></div></section>
  );
};

const DataTable: FC<NodeProps> = () => (
  <section aria-label="Records" style={{ padding: "0 var(--spacing-lg)" }}>
    <div className="uib-card" style={{ padding: 0, overflow: "hidden" }}>
      <table><thead><tr>{["Customer", "Plan", "MRR", "Status"].map((h) => <th key={h}>{h}</th>)}</tr></thead>
        <tbody>{[["Northwind", "Scale", "$1,990", "Active"], ["Contoso", "Team", "$490", "Active"], ["Globex", "Team", "$490", "Trial"], ["Initech", "Starter", "$0", "Churned"], ["Umbrella", "Scale", "$1,990", "Active"]].map((r) => (
          <tr key={r[0]}>{r.map((c) => <td key={c}>{c}</td>)}</tr>))}</tbody></table></div></section>
);

const ActivityFeed: FC<NodeProps> = () => (
  <section aria-label="Recent activity" style={{ padding: "0 var(--spacing-lg)" }}>
    <div className="uib-card"><h3 style={{ marginBottom: "var(--spacing-md)" }}>Recent activity</h3>
      <ul style={{ listStyle: "none", padding: 0, display: "grid", gap: "var(--spacing-md)" }}>
        {["Northwind upgraded to Scale", "New report shared by Alex", "Invoice #2291 paid", "Globex trial ends in 3 days"].map((t, i) => (
          <li key={t} style={{ display: "flex", gap: "var(--spacing-sm)" }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "var(--color-border)", flexShrink: 0 }} />
            <div><p>{t}</p><p className="uib-muted" style={{ fontSize: ".8rem" }}>{i + 1}h ago</p></div></li>))}</ul></div></section>
);

/* ---------------------------------------------------------------- forms */
const SettingsNav: FC<NodeProps> = ({ node }) => {
  const vertical = node.props.variant === "vertical";
  return (
    <nav aria-label="Settings sections" style={{ padding: "0 var(--spacing-lg)" }}>
      <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: 4, borderBottom: vertical ? "none" : "1px solid var(--color-border)" }}>
        {["Profile", "Notifications", "Security", "Billing"].map((t, i) => (
          <a key={t} href={`#${t}`} aria-current={i === 0 ? "page" : undefined}
            style={{ padding: "12px 16px", textDecoration: "none", color: "inherit", fontWeight: i === 0 ? 600 : 400, borderBottom: !vertical && i === 0 ? "2px solid var(--color-primary)" : "2px solid transparent" }}>{t}</a>))}
      </div></nav>
  );
};

const SettingsForm: FC<NodeProps> = ({ node }) => (
  <section aria-label="Settings" style={{ padding: "0 var(--spacing-lg)" }}>
    <div className="uib-card"><h2 style={{ fontSize: "1.25rem" }}>{p(node, "title", "Profile")}</h2>
      <p className="uib-muted" style={{ marginBottom: "var(--spacing-lg)" }}>{p(node, "description", "How you appear to your team.")}</p>
      <form>{[["Full name", "text"], ["Email", "email"], ["Job title", "text"]].map(([l, t]) => (
        <div key={l} className="uib-field"><label htmlFor={l}>{l}</label><input id={l} type={t} defaultValue="" placeholder={l} /></div>))}
        <div className="uib-field"><label htmlFor="tz">Timezone</label><select id="tz"><option>UTC</option><option>Asia/Ho_Chi_Minh</option></select></div>
        <Btn>Save changes</Btn></form></div></section>
);

const DangerZone: FC<NodeProps> = () => (
  <section aria-label="Danger zone" style={{ padding: "0 var(--spacing-lg) var(--spacing-xl)" }}>
    <div className="uib-card" style={{ borderColor: "var(--color-sale,#dc2626)" }}>
      <h2 style={{ fontSize: "1.25rem" }}>Danger zone</h2>
      <p className="uib-muted" style={{ margin: "var(--spacing-sm) 0 var(--spacing-lg)" }}>Deleting your workspace removes all data permanently.</p>
      <button type="button" className="uib-btn" style={{ background: "#dc2626", color: "#fff" }}>Delete workspace</button></div></section>
);

export const COMPONENTS: Record<string, FC<NodeProps>> = {
  Page, Main, NavBar, Sidebar, Breadcrumb, PageHeader, Footer,
  Hero, SocialProof, FeatureBento, FeatureCard, ProductShowcase, Metrics, Testimonials, PricingTable, FAQ, CTA,
  ProductCard, ProductGrid, ProductDetail, TrustSignals, Reviews, RelatedProducts,
  Stats, ChartPanel, DataTable, ActivityFeed, SettingsNav, SettingsForm, DangerZone,
};
