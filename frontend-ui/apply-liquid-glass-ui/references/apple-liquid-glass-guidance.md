# Apple Liquid Glass Guidance

Use these notes to ground visual refactors in official Apple design guidance
without copying platform behavior blindly into every stack.

## Official References

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [HIG: Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
- [HIG: Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons)
- [HIG: Toolbars](https://developer.apple.com/design/human-interface-guidelines/toolbars)
- [Technology overview: Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/liquid-glass)
- [Adopting Liquid Glass](https://developer.apple.com/documentation/TechnologyOverviews/adopting-liquid-glass)
- [WWDC 2025 session 356](https://developer.apple.com/videos/play/wwdc2025/356/)
- [Apple Newsroom announcement](https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/)

## Interpreted Principles

- Hierarchy: controls and navigation should sit in a clearly functional layer
  above content. Do not make every content card look like a toolbar.
- Harmony: shapes should feel concentric and related. If a container has a large
  radius, inner controls need compatible smaller radii.
- Consistency: repeated controls should share size, radius, material, state, and
  spacing rules across the app.
- Content focus: glass, blur, and refraction effects should support orientation
  and interaction, not compete with text or data.
- Platform fit: native platforms should prefer standard SwiftUI, UIKit, and
  AppKit controls first; web implementations should simulate the material with
  CSS tokens and accessibility-aware fallbacks.

## Practical Token Starting Point

Adapt values to the existing product, but this is a reasonable first pass for
web CSS:

```css
:root {
  --font-display: "SF Pro Display", "SF Pro Text", system-ui, sans-serif;
  --radius-sm: 12px;
  --radius-md: 18px;
  --radius-lg: 26px;
  --radius-pill: 999px;
  --surface-page: #f5f5f7;
  --surface-glass: rgb(255 255 255 / 68%);
  --surface-glass-strong: rgb(255 255 255 / 82%);
  --border-glass: rgb(255 255 255 / 54%);
  --text-primary: #1d1d1f;
  --text-secondary: rgb(29 29 31 / 68%);
  --accent: #007aff;
  --shadow-glass: 0 18px 48px rgb(0 0 0 / 10%);
  --blur-glass: blur(22px) saturate(180%);
  --motion-calm: 220ms cubic-bezier(.2, .8, .2, 1);
}

@media (prefers-color-scheme: dark) {
  :root {
    --surface-page: #050506;
    --surface-glass: rgb(28 28 30 / 68%);
    --surface-glass-strong: rgb(44 44 46 / 82%);
    --border-glass: rgb(255 255 255 / 14%);
    --text-primary: #f5f5f7;
    --text-secondary: rgb(245 245 247 / 68%);
    --shadow-glass: 0 18px 48px rgb(0 0 0 / 34%);
  }
}
```

## Review Checklist

- Is there a single coherent token system rather than many one-off colors and
  radii?
- Are toolbars, nav bars, floating actions, and dialogs visually distinct from
  content?
- Are content-heavy areas calm and readable instead of over-blurred?
- Does the primary action stand out without turning the whole interface into a
  saturated accent surface?
- Are hover, pressed, disabled, selected, loading, and focus states present?
- Does the design hold up in dark mode, reduced motion, narrow widths, and high
  contrast needs?
