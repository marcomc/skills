---
name: hd-riders-survey
description: Complete authorized surveys from H-D Riders and verify their visible completion. Use for any user-authorized H-D Riders survey link, not a particular questionnaire.
---

<!-- MARCOMC-SKILL: owner="MarcoMC <marco@marcomc.com>"; repository="marcomc/skills"; provenance="original" -->

# H-D Riders Survey

Complete any user-authorized survey published through H-D Riders end to end and verify its visible completion outcome.

## Workflow

1. Open the supplied H-D Riders survey link in the requested browser. The site may require authentication or redirect to a third-party survey provider. Do not handle passwords, MFA, or account recovery; ask the user to sign in when needed.
2. Work through each required question using responses the user explicitly supplies or authorizes. Do not infer details that are not available from the current survey or user authorization.
3. Treat question-answering as data transmission to the applicable survey provider. If the user has not clearly authorized the specific type of data and the destination, pause immediately before entering it and request confirmation. Do the same immediately before the final survey submission.
4. After submission, confirm a visible success, thank-you, completion, or points-awarded state. Do not infer completion merely because the final page was reached.
5. Report the destination used, whether completion was visibly verified, and any question, validation, login, or redirect blocker. Do not repeat personal values or parameterized survey URLs in the report.

## Scope boundary

Use this skill only for H-D Riders surveys the user says they are authorized to complete or test. It does not authorize account management, browser permission grants, CAPTCHA solving, or changing survey configuration.
