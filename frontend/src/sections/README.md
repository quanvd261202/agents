# Section conventions

Every semantic component in the catalog (`app/catalog/data/<module>.py`) has one React
implementation here, in the file of the same module, under the key given by its
`implementation.root`. `components/index.tsx` merges every file into the map the renderer
dispatches on.

Reference implementations: `Hero` in `marketing.tsx`, `ProductCard` / `ProductGrid` in
`commerce.tsx`. Match their quality and idiom.

## Build from the primitives

Import from `../ui`: `Section`, `SectionHeader`, `Eyebrow`, `Button`, `Badge`, `Card`, `Media`,
`Price`, `Rating`, `QuantityStepper`, `ChoiceChips`, `Disclosure`, `Tabs`, `Carousel`, `Marquee`,
`Avatar`, `Field`, and the helpers `prop`, `listProp`, `variantOf`, `range`. `cn` is in
`../lib/cn`. Icons come from `lucide-react`. Do not edit `ui/index.tsx`; a helper only you need
goes in your own file.

## Tokens only

- Colours: `bg-bg`, `bg-surface`, `bg-surface-alt`, `text-fg`, `text-muted`, `bg-primary`,
  `text-primary-fg`, `bg-accent`, `text-accent-fg`, `border-border`, `ring-ring`,
  `text-success|warning|danger`, `bg-media-a|b`. Opacity modifiers are fine (`bg-fg/[0.04]`).
  Never a hex value, never a Tailwind palette colour (`bg-amber-500`).
- Type: `text-display|h1|h2|h3|h4|lead|body|small|caption`, headings add `font-heading-set`.
- Radius: `rounded-sm|card|lg|media|button|pill`. Shadow: `shadow-sm|md|lg|xl`.
- Layout: `Section` gives rhythm and the container; `page-x`, `section-y`, `container-page`,
  `container-wide` exist for custom shells. Spacing uses the normal scale (it follows density).
- Easing: `ease-brand`. Durations 200-700ms.

## Tones

`<Section tone="default|surface|alt|inverse|accent">`. Inverse and accent re-scope every colour
role, so the same children stay readable in a dark band. Use tone for rhythm between sections,
not decoration.

## Content

Every visible string is `prop(node, "<slot>", "<fallback>")`, and every slot you read must be
declared in the component's catalog `slots`. Lists use `listProp` with comma-separated values.
Fallback copy is premium, specific-sounding and domain-neutral (it must read well for a cafe, a
boutique or a studio). No lorem ipsum, no "Feature 1", no SaaS jargon.

## Links and the site (M13)

A section never decides where a control goes. The resolver wires the intents the catalog says a
role emits into `node.props.hrefs`; read them with `hrefOf(node, "<role>")` from `../ui` and pass
the result as `href` to `Button` (it renders an `<a>` when given one) or an anchor, and stamp the
control `data-role="<role>"` so the flow check can find it. Without an href the control stays a
button or a `#` anchor: that is a dead control the flow check reports, not something to hide.
Navigation reads `node.props.nav_links`, breadcrumbs `node.props.trail_links`. Live state (cart,
filters, search) comes from `../site/store` and the current item from `../site/context`; every
hook returns nothing when the screen is rendered alone, so keep the prop fallbacks.

## Imagery

`<Media ratio subject src label tone>` is the image. A `media` / `image` slot holds a photo
description ("burlap bag of roasted coffee beans on oak"); the imagery service resolves it to a
photograph in `node.props.images[slot][i]`, and `imageAt(node, slot, i)` supplies `src` (index `i`
for list slots: collection tiles, gallery shots). Without a photo the art-directed silhouette
renders, so always pass a `subject` fallback: `subjectOf(prop(node, "media", ""), "bag")` picks
the first known subject word (cup, bag, leaf, glass, product, person, space, device, chart,
abstract) and vary `tone` across items. Never put text directly on a `Media`: text over imagery
sits on a solid panel (`bg-bg/95`, `bg-primary`).

## Variants and states

- Each variant must look clearly different (composition, not just a colour swap).
- Interactive things have hover, focus-visible and active states (the primitives already do).
- Hover-only affordances must also be reachable by focus and visible on touch (see Quick add).

## Responsive

Mobile first. No horizontal page scroll at 390px. Grids collapse (1 col phone, 2 tablet). Use the
layout engine's `columns` prop when a grid's desktop column count should follow the spec.

## Accessibility (the renderer checks all of these)

- Text contrast AA. Interactive targets at least 44px tall (primitives already are).
- Every control has a label; icon-only buttons have `aria-label`; toggles use `aria-pressed`.
- Heading order: `h1` only in page-leading sections (hero, page header, product detail); sections
  use `h2`, items `h3`.
- Every section has an accessible name (`Section label=...`).

## Checking your work

```bash
cd frontend && npx tsc --noEmit && npx vite build --outDir dist-<you>
cd .. && UIB_FRONTEND_DIST=frontend/dist-<you> uv run uib gallery -c <id> -c <id> --out gallery/<you>
UIB_FRONTEND_DIST=frontend/dist-<you> uv run uib gallery -c <id> --palette midnight --typography grotesk_display --radius none --out gallery/<you>
```

The gallery must print `ok` for every component under both a light and a dark palette. Then open
the PNGs in `gallery/<you>/<palette>/` and review them as a designer would.
