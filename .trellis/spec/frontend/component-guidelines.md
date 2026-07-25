# Component Guidelines

> How components are built in this project.

---

## Overview

<!--
Document your project's component conventions here.

Questions to answer:
- What component patterns do you use?
- How are props defined?
- How do you handle composition?
- What accessibility standards apply?
-->

(To be filled by the team)

---

## Component Structure

<!-- Standard structure of a component file -->

(To be filled by the team)

---

## Props Conventions

<!-- How props should be defined and typed -->

(To be filled by the team)

---

## Styling Patterns

<!-- How styles are applied (CSS modules, styled-components, Tailwind, etc.) -->

(To be filled by the team)

---

## Accessibility

<!-- A11y requirements and patterns -->

(To be filled by the team)

---

## Common Mistakes

<!-- Component-related mistakes your team has made -->

### Dashboard metric cards

The normal dashboard page uses a `QGridLayout` with equal row and column
stretch. Each OBD value is represented by either:

* `GaugeMetric` for values listed in `GAUGE_RANGES`.
* `InfoMetric` for text or numeric values without a gauge.

Cards must expand with the grid. Do not restore fixed card widths or center a
single vertical metric column; that wastes most of the 1280x720 display.

Keep data behavior outside the visual layout. Metric widgets stay registered in
`gauge_metrics` or `info_metrics`, and `update_values()` updates them from
`latest_values`. The reverse-camera page remains a separate page in the
existing `QStackedWidget`.

Use `scaled()` for pixel sizes, margins, spacing, and typography. Verify layout
changes with a real 1280x720 Qt render because widget geometry alone does not
prove that text is readable.
