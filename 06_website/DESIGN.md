---
name: "POPIN"
description: "Light research observatory for comparative populism data."
colors:
  bg: "#f3f5f7"
  card: "#fff"
  card2: "#edf3f6"
  text: "#172d3d"
  text2: "#465e6e"
  text3: "#596b79"
  brand: "#006b73"
  brand2: "#183b56"
  brand-gl: "#e5f1f1"
  border: "#dfe6eb"
  border2: "#bdcbd5"
  score-0: "#e8f1fa"
  score-25: "#b5d1e8"
  score-50: "#70a3c8"
  score-75: "#3a7099"
  plot-ink: "#334155"
  plot-grid: "#e2e8f0"
  plot-teal: "#007f86"
  focus: "#178eaa"
  error: "#a92a2a"
typography:
  headline: {"fontFamily":"IBM Plex Sans, system-ui, sans-serif","fontSize":"29px","fontWeight":600,"lineHeight":1.2,"letterSpacing":"-0.7px"}
  body: {"fontFamily":"IBM Plex Sans, system-ui, sans-serif","fontSize":"14px","fontWeight":400,"lineHeight":1.5}
  label: {"fontFamily":"IBM Plex Sans, system-ui, sans-serif","fontSize":"12px","fontWeight":400,"lineHeight":1.5}
  metric: {"fontFamily":"IBM Plex Sans, system-ui, sans-serif","fontSize":"27px","fontWeight":500,"lineHeight":1.3,"letterSpacing":"-0.5px"}
  plot-tick: {"fontFamily":"IBM Plex Mono, monospace","fontSize":"11px"}
rounded:
  radius: "8px"
  rsm: "4px"
  badge: "3px"
spacing:
  control-gap: "6px"
  compact-gap: "12px"
  panel-gap: "24px"
  desktop-gutter: "32px"
  mobile-gutter: "16px"
components:
  button-text: {"backgroundColor":"transparent","textColor":"{colors.brand}","padding":"0 2px"}
  button-toggle: {"backgroundColor":"{colors.card}","rounded":"{rounded.rsm}","padding":"6px 10px"}
  button-toggle-active: {"backgroundColor":"{colors.brand-gl}","textColor":"{colors.brand}","rounded":"{rounded.rsm}","padding":"6px 10px"}
  button-retry: {"backgroundColor":"{colors.card}","textColor":"{colors.brand}","rounded":"{rounded.rsm}","padding":"8px 16px"}
  chip: {"backgroundColor":"{colors.card}","rounded":"{rounded.rsm}","padding":"7px 12px"}
  chip-active: {"backgroundColor":"{colors.brand-gl}","textColor":"#005c63","rounded":"{rounded.rsm}","padding":"7px 12px"}
  badge: {"backgroundColor":"{colors.card2}","textColor":"{colors.text2}","rounded":"{rounded.badge}","padding":"3px 7px"}
  field: {"backgroundColor":"{colors.card}","rounded":"{rounded.rsm}","padding":"8px 12px"}
  nav: {"backgroundColor":"transparent","textColor":"{colors.text2}","padding":"4px 13px 0"}
  card: {"backgroundColor":"{colors.card}","rounded":"{rounded.radius}","padding":"22px"}
---

# Design System: POPIN

## Overview

**Creative North Star: "Observatório público de dados"**

POPIN is a light research observatory for researchers and journalists. Navy anchors identity and quantitative reading; teal identifies actions and selection. Useful density comes from aligned numbers, broad comparison surfaces and restrained borders.

The implemented surface has a horizontal header, five exploration sections, a research About section and a shared discourse-type scope. Its visual language supports reading the available corpus, comparing coverage and opening a leader profile without losing context. The interface remains light and uses native HTML/CSS/JavaScript with Plotly.

Evidence: `REWORK.md`, `static/index.html`, `static/css/style.css` and `static/js/app.js`. This record is extracted from source, including JavaScript-generated components and localized copy. No screenshots were available here and this documentation pass performed no visual verification; live-browser QA was reported by the parent task. The full-corpus baseline of 45,492 observations comes from the authorized brief and REWORK; it was not re-queried in this pass.

**Key Characteristics:**

- Light neutral surfaces with navy and teal.
- Continuous blue score encoding from 0 to 100.
- IBM Plex Sans with tabular numbers and selective IBM Plex Mono.
- Coverage and distribution beside comparative means.

## Colors

Cool paper, white research surfaces and muted ink establish a quiet base for directional teal and quantitative blues. Frontmatter values are normative; CSS names are retained where they are actual shared variables.

### Primary

- **Research Navy** (`brand2`): POPIN identity, single-series trend lines and score maximum.
- **Instrument Teal** (`brand`): navigation selection, interactive text and selected control borders.

### Secondary

- **Selection Wash** (`brand-gl`): active chips and mobile navigation.
- **Score Blues** (`score-0` through `score-75`, ending at `brand2`): the map legend, choropleth, score marks and dimension bars share these five anchors. JavaScript interpolates RGB channels between anchors.
- **Plot Teal** (`plot-teal`): last-year endpoint and one categorical series color; distinct from control teal. The existing 19-color series array in JavaScript identifies countries consistently across radar and time-series comparisons.
- **Focus Cyan** (`focus`) and **Error Red** (`error`): keyboard focus and data-loading failure, respectively.

### Neutral

- **Cool Paper** (`bg`), **White Surface** (`card`) and **Inset Mist** (`card2`): page, panels/fields and metadata badges.
- **Research Ink** (`text`), **Secondary Ink** (`text2`) and **Annotation Ink** (`text3`): primary reading, controls and supporting notes.
- **Quiet Divider** (`border`) and **Control Stroke** (`border2`): structural separation and field/chip boundaries.
- **Plot Ink** (`plot-ink`) and **Plot Grid** (`plot-grid`): chart labels, quartile intervals and axes.

**The Continuous Score Rule.** Use the same continuous blue interpolation for score magnitude. The stops at 0, 25, 50, 75 and 100 are interpolation anchors, never score categories.

**The Identity Color Rule.** Use teal for control selection and stable categorical colors for compared series or endpoint identity; neither defines a score threshold.

Sidecar tonal ramps are synthesized swatch previews, not additional shipped tokens or replacements for the five-stop score scale.

## Typography

**Display Font:** IBM Plex Sans, with system-ui and sans-serif fallback.
**Body Font:** IBM Plex Sans, with system-ui and sans-serif fallback.
**Label/Mono Font:** IBM Plex Mono, with monospace fallback, for ISO codes, ranks, legend endpoints and chart ticks.

The same sans family spans headings and controls; weight and size establish hierarchy without a separate editorial display face. Numeric precision comes from tabular figures rather than ornamental badges.

### Hierarchy

- **Headline:** section titles use the frontmatter headline role; mobile reduces them to 25px.
- **Body:** the frontmatter body role governs reading and controls; section descriptions constrain line length with a 750px maximum width.
- **Label:** supporting labels, captions and metadata use the 12px role, with contextual 11px notes.
- **Metric:** KPI values use the metric role, reducing to 24px on mobile. Corpus average and drawer score are contextual enlargements, not an additional reusable type scale.
- **Chart ticks:** the mono tick role separates numerical axes from sans chart labels.

The HTML chart headings are plain `h2` elements. The stylesheet's 16px card-title selector is not attached to those headings, so it is not recorded as their implemented type token. The legacy serif-named CSS variable resolves to IBM Plex Sans and does not establish a serif family.

**The Comparable Numbers Rule.** Use tabular numerals for metrics, scores and coverage; preserve localized decimal formatting and the dash for unavailable values.

## Layout

The header and main content share a centered 1480px maximum width and 32px desktop gutters. The sticky white header is at least 88px tall, with brand, six horizontal navigation items and language/repository actions. The global filter strip precedes exploration sections and is hidden on About, whose research evidence is a fixed audit snapshot.

The exploration order is Visão geral, Países, Líderes, Série temporal and Dimensões. Overview pairs a map and a coverage table in a 1fr / 1.05fr grid; other comparison panels use equal columns. A four-column ruled KPI strip communicates corpus coverage. Recurring panel gaps are 24px; panel padding is 22px. About follows Dimensões in the menu. It uses a reading column and document sidebar, stacked below 900px, with PT/EN copy, dissertation PDF and audit CSV downloads. The footer retains only identity and repository access.

- At 1180px and below: 24px gutters, 18px panel padding, tighter header and a 1fr / 1.1fr overview split; the repository link is hidden.
- At 900px and below: overview and comparison grids stack; the table keeps local overflow.
- At 768px and below: the 72px header exposes a button-controlled vertical menu beneath it; content gutters become 16px, KPIs form two columns, fields wrap, search spans the row and panels use 16px / 12px padding. Compact supporting ISO codes are hidden.
- At 1500px and above: the overview map and table gain vertical room.

Chart containers have purpose-specific heights. Row charts set both Plotly layout height and the element's inline height, preserving their data-dependent sizing through ResizeObserver. Country intervals and dimension bars use max(450, rows × 27 + 120)px; endpoint comparisons use max(400, rows × 27 + 120)px. The horizontal group-interval chart uses max(420, rows × 28 + 145)px, a 115px bottom margin and legend y = −0.18. Newly visible plots and resized containers are remeasured; the mobile CSS height of 400px is only a fallback, not the row-chart sizing rule. The profile is a right-hand drawer with width `min(560px,100%)`, separate scrolling content and an inert background.

## Elevation & Depth

Research panels are flat white surfaces delineated by thin borders. Header stickiness, the mobile navigation overlay and the modal profile establish functional layers; cards and the profile do not carry decorative shadows.

### Shadow Vocabulary

- **Mobile navigation:** `0 12px 18px rgba(23,45,61,.05)`, under the open mobile menu.
- **Modal scrim:** `rgba(16,37,53,.28)`, behind the profile; mobile navigation uses `rgba(16,37,53,.22)`.

**The Flat Surface Rule.** Use borders and tonal separation for research surfaces; reserve the implemented shadow for the open mobile navigation.

## Shapes

Panels have gently rounded corners using `radius`; chips, fields, segmented controls and icon buttons use `rsm`. Metadata badges use `badge`. Mobile panels reduce to 6px. Fine one-pixel borders and straight table/ranking rules carry structure. Thin score tracks are measurements, with their numerical values retained as text.

## Components

### Buttons

Compact and textual. CSV export is an underlined teal text button; dimension toggles are bordered white controls with a teal selection wash. Retry uses a bordered white button. Close and mobile-menu buttons are 40px squares with inline SVG icons. No filled primary CTA variant is established. Global focus is a 3px cyan outline with 3px offset; disabled buttons have .55 opacity and a wait cursor. Do not invent hover motion absent from the implementation.

### Chips

Discourse-type and country-selection chips use the frontmatter chip geometry and 36px minimum height. Selected chips use the selection wash, teal border, dark teal text and 600 weight. Hover shifts the border and text to control teal. Counts use tabular numerals, and selected state is conveyed with `aria-pressed`. The small metadata badge is passive, not a filter.

### Cards / Containers

White, bordered, flat research panels use the frontmatter card token. Header content wraps when needed; chart captions and statistical notes remain adjacent to their evidence. The KPI strip and leader ranking are ruled rows, not separate elevated cards.

### Inputs / Fields

Labeled native selects and the leader search field share white fill, control stroke, small corners and 40px minimum height. Labels sit above fields with a 6px gap. The global focus outline supplies keyboard feedback; input caret is teal. Search filters the currently loaded leaders, and the result badge reports that scope.

### Navigation

Desktop navigation uses 14px medium-weight text; active items become teal and semibold with a 3px lower rule. Hover adds a pale background. On mobile the active rule moves to the left and selection gains a teal wash. Section controls use `aria-current`; the closed mobile menu is inert. PT/EN localizes chart labels, counts and numbers while preserving data identities.

### Quantitative comparison

The persistent map legend marks 0, 25, 50, 75 and 100. Score axes normally span 0–100; the dimension bar chart extends its plotting range to 105 for outside labels without changing score semantics. The coverage table pairs means with counts and p25–p75, keeps sticky column headings and links each country to the leader view. Interval charts draw the actual quartile endpoints and overlay means. Temporal charts use stable series colors and gentle spline curves (smoothing 0.5), with observed annual values retained as markers. Curves are visual interpolation, not intermediate observations. Quartile intervals and radar geometry remain straight; unavailable values are not filled with zero.

### Profile and resource states

Leader rows open a modal profile with numerical score, six dimension bars, historical trend and radar. Escape, backdrop and close button dismiss it; Tab is contained and focus returns to the trigger. Reduced motion disables CSS transitions and animations. Normal operation uses localized per-region loading, empty and retryable error states; the initial full-page loader is hidden by JavaScript. The refresh summary announces status without making the whole interface unusable.

## Do's and Don'ts

### Do:

- Do preserve all five exploration sections and the shared active-scope summary.
- Do show means with discourse counts and p25–p75 wherever supplied; the interval describes the middle 50% of discourses.
- Do retain the continuous 0–100 legend, localized numbers, keyboard focus and reduced-motion behavior.
- Do derive displayed totals from the real filtered dataset; the authorized full-corpus baseline is 45,492 observations.

### Don't:

- Don't add artificial populist/non-populist categories or color thresholds.
- Don't describe quartiles as confidence intervals or standard errors, or turn missing values into zero.
- Don't introduce a dark theme, a permanent desktop sidebar, decorative score medals or a new display font.
- Don't change backend contracts, source observations or score values as part of visual documentation.

Not canonized: the GitHub arrow glyph is an incidental icon substitute, and the unused card-title/serif-era selectors are legacy implementation residue; none defines a reusable house style.
