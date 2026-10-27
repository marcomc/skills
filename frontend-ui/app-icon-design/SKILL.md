---
name: app-icon-design
description: Create, adapt, review, or integrate native app icons for macOS, iOS, and iPadOS projects, including distinct macOS Dock/Finder and menu bar assets.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# Apple App Icon Design

Create a recognizable icon system for the Apple platforms a project actually supports. Apply current Apple design and technical guidance, inspect the real artwork in context, and integrate only the assets the app needs. Treat the app icon, menu bar symbol, and any optional document icons as distinct deliverables.

## Establish the target

- Read repository instructions and inspect the existing app icon, source artwork, previews, asset catalog or Icon Composer document, build settings, and supported deployment targets before editing.
- Determine the target platforms and the current Apple OS and Xcode versions from the project and official Apple sources. Apple sources checked on 1 October 2026 identified macOS 27 and iOS/iPadOS 27 as the current generation. Verify current release names and requirements for every task rather than treating those versions as permanent.
- Reuse the project's existing identity and art direction. Infer the app's purpose and platform targets from the project where possible. Ask only for missing product meaning, visual direction, or deliverables that cannot be inferred and materially affect the design.
- Keep the deliverable bounded to requested platforms and surfaces. For a universal app, create platform-appropriate appearances from one coherent identity; do not assume one raster file is appropriate for every surface.

## Consult Apple sources

Use current first-party documentation and tie requirements to their source. Begin with the relevant pages, then follow their links to current Xcode, asset, and platform requirements:

- [Human Interface Guidelines: App icons](https://developer.apple.com/design/human-interface-guidelines/app-icons) for app icon purpose, composition, platform differences, and supported appearances.
- [Human Interface Guidelines: The menu bar](https://developer.apple.com/design/human-interface-guidelines/the-menu-bar) for the menu bar extra role and appearance. Apple currently lists menu bar extras for macOS and not iPadOS; verify platform support against the current guide.
- [Creating your app icon using Icon Composer](https://developer.apple.com/documentation/xcode/creating-your-app-icon-using-icon-composer) and [Icon Composer](https://developer.apple.com/icon-composer/) for layered icon authoring, platform modes, previews, and Xcode integration where supported.
- [Apple Design Resources](https://developer.apple.com/design/resources/) for current platform UI kits and icon templates.
- [SF Symbols](https://developer.apple.com/sf-symbols/) when a standard system symbol may suit a menu bar item or interface control.

Use a separate, versioned source note only when the user asks for research deliverables or the findings need to persist beyond the task. Do not copy Apple manuals into the project. In task results, link the pages that support non-obvious constraints and distinguish Apple requirements from design recommendations.

## Design by surface

| Surface | Design and implementation guidance |
| --- | --- |
| macOS app icon | The app's icon is used in Finder and the Dock, and can appear in other system surfaces. Design for recognition at small and large sizes and for Apple's current Mac icon shape and appearance system. Use the project's native Icon Composer or asset catalog workflow supported by its Xcode/deployment targets. |
| macOS menu bar | Create a separate compact symbol for the status item. Prefer a legible monochrome/template rendering that fits the menu bar's visual weight; verify Apple's current template-image and sizing guidance. Menu bar extras are a macOS surface; do not invent an iPad menu bar icon requirement when the app also targets iPadOS. Do not reuse the detailed Dock/Finder artwork as a miniature status symbol. Keep state communicated through supported, accessible cues and avoid relying on color alone. |
| iPhone app icon | Design for the current iOS app icon shape, rendering modes, and Home Screen/Spotlight contexts. Supply the source format and asset variants required by the project's Xcode version and deployment target. Do not bake system masking, gloss, or material effects into the artwork unless Apple's current guidance specifically calls for them. |
| iPad app icon | Follow current iPadOS requirements. Reuse the iPhone identity when the app is universal, while checking whether the platform's layout, variants, or rendering behavior require a tailored composition. |
| Document or file icons | Produce these only when the app registers document types or the user requests them. Follow Apple's current document-icon and file-type guidance; keep them visually related to, but distinct from, the app icon. |

## Create or adapt the artwork

- Preserve the app's recognizable identity while simplifying forms that fail at small display sizes. Use shape, contrast, and spacing before fine detail.
- Prefer editable source artwork and the project's established pipeline. Keep original source files and generated platform assets clearly distinguishable.
- For visual generation or image editing, inspect every target image first and use the available image-generation tool. Preserve transparency when present, unless the requested design requires a different background. Do not use scripts to paint, composite, or retouch raster artwork unless the user explicitly requests code-based image processing.
- For layered Icon Composer workflows, follow the current Apple guide for canvas, input formats, layer order, material effects, appearance annotations, and Xcode handoff. Do not assume a cross-platform template or one set of layers will render well on every platform.
- Keep menu bar artwork separate from the app icon. Prefer an existing SF Symbol if it communicates the function clearly and fits the app's platform behavior; create custom artwork only when it adds needed identity or meaning.
- Do not modify document type registrations, app behavior, bundle identifiers, or unrelated project configuration as a side effect of icon work.

## Inspect and integrate

- Preview the icon through the target platform's actual tooling where available, including every supported appearance mode and platform override. Inspect at realistic small sizes and in its intended system surface; a source PNG inspection alone is insufficient.
- For macOS, inspect both Finder/Dock rendering and the separate menu bar symbol. For iOS/iPadOS, inspect the app icon in the current platform preview and asset catalog/Xcode workflow.
- Check silhouette, margins, contrast, visual balance, legibility, crop/mask behavior, dark and monochrome rendering, and consistency across platforms. Correct visible defects rather than trusting that import or compilation implies a good result.
- Integrate generated files through the existing project configuration. Preserve backward compatibility according to the deployment target and Apple's current Xcode behavior.
- Run focused asset/build validation when available. Report which generated previews, modes, devices, and build checks were actually observed; do not claim physical-device or system-surface validation unless it occurred.
- Update project documentation only when existing icon instructions become inaccurate or the user asks for documentation. Follow repository lint requirements for modified Markdown.

## Report

Summarize the resulting surfaces and platform variants, link the Apple guidance used, list changed asset/integration paths, and state the visual and build checks completed. Call out any unverified rendering or device checks plainly.
