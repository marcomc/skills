---
name: apply-liquid-glass-ui
description: Use when refactoring the visual presentation of a graphical app UI toward Apple's modern Liquid Glass design language, including web apps, sites, iOS apps, macOS apps, HTML/CSS/JS frontends, SwiftUI, UIKit, AppKit, dashboards, forms, toolbars, cards, modals, inputs, and buttons, while preserving existing product logic and workflows.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Apply Liquid Glass UI

## Overview

Refactor an existing graphical interface so it feels aligned with Apple's current
HIG and Liquid Glass direction without changing application behavior. Preserve
workflows, routes, data flow, copy intent, and domain logic unless the user
explicitly requests product changes.

Read `references/apple-liquid-glass-guidance.md` when the task needs Apple HIG
grounding, platform-specific choices, or official reference links.

## Workflow

1. Inspect the current UI structure, styles, design tokens, component patterns,
   and available verification path before editing.
2. Identify the smallest visual surface that can create a coherent system:
   colors, typography, radii, material surfaces, focus states, shadows, spacing,
   motion, and dark-mode behavior.
3. Refactor existing styling first. Prefer CSS variables, SwiftUI modifiers,
   UIKit/AppKit appearances, or local component styles over new dependencies.
4. Make minimal markup or view-structure changes only when styling alone cannot
   express the visual layer cleanly.
5. Add concise comments only for non-obvious design decisions such as material
   fallbacks, accessibility constraints, or cross-platform token mapping.
6. Verify the UI visually and functionally. For web apps, run the local app and
   inspect desktop and mobile widths with a real browser when practical. For
   iOS/macOS, build and run the relevant simulator or app target when practical.

## Design System Rules

Use a small token set and apply it consistently:

- Typography: prefer `"SF Pro Display"`, `"SF Pro Text"`, `system-ui`,
  `sans-serif`; use hierarchy through weight, size, and spacing rather than
  dense decoration.
- Shape: use soft, concentric radii. Use capsules for compact controls and
  larger rounded rectangles for cards, sheets, inputs, popovers, and panels.
- Materials: reserve strong glass treatment for navigation, toolbars, floating
  controls, modals, and transient interactive layers. Use quieter standard
  translucent surfaces for content cards.
- Color: keep backgrounds neutral and low-saturation. Let content remain the
  focal point. Use accent color sparingly for one primary action per region.
- Depth: prefer subtle borders, blur, tint, and diffuse shadows over hard
  elevation.
- Motion: animate opacity, transform, background, border, and blur subtly,
  typically around 160-280 ms with calm easing. Respect reduced motion.
- Accessibility: preserve readable contrast, visible focus states, hit targets
  near Apple guidance, and dark-mode clarity. Do not let translucency obscure
  text or controls.

## Platform Guidance

For web apps and sites:

- Build tokens in CSS custom properties, including color, radius, shadow,
  material, border, focus, and motion values.
- Use `backdrop-filter` with solid-color fallbacks. Keep glass blur moderate and
  avoid stacking many blurred panels over dense text.
- Restyle existing buttons, inputs, cards, dropdowns, dialogs, nav bars,
  toolbars, tables, and alerts. Do not introduce a landing-page layout unless
  the app is actually a marketing site.
- Check responsive behavior and text fitting at narrow and desktop widths.

For iOS apps:

- Prefer standard SwiftUI/UIKit navigation, toolbar, button, sheet, list, and
  form components so the system can provide platform behavior.
- Apply custom Liquid Glass-like styling only where standard components cannot
  express the needed app-specific surface.
- Keep touch targets comfortable and primary actions visually singular.

For macOS apps:

- Preserve desktop density where the app is operational, but add breathing room,
  clearer grouping, and native-feeling toolbar/sidebar/window surfaces.
- Prefer AppKit/SwiftUI standard materials and toolbar idioms before custom
  glass simulation.
- Keep keyboard focus, hover, selection, and disabled states explicit.

## Implementation Guardrails

- Do not change backend behavior, application routes, persistence, auth,
  business rules, or workflow order.
- Do not add large UI frameworks or icon systems unless already present or
  clearly justified.
- Do not over-glass the content layer. Content should stay legible and stable;
  glass belongs mainly to functional layers and floating controls.
- Do not use loud gradients, saturated palettes, hard shadows, or decorative
  blobs as a substitute for hierarchy.
- Keep the diff maintainable: consolidate repeated values into tokens and adapt
  existing components rather than duplicating one-off styles.

## Verification

Before reporting completion:

- Run the repository's relevant frontend checks if available.
- Run required project linting for edited Markdown or shell files.
- Verify at least one realistic interactive path still works.
- Inspect the rendered UI for overlap, clipped text, unreadable glass, missing
  focus states, broken dark mode, and layout regressions.
- Summarize what changed visually and what was deliberately left untouched.
