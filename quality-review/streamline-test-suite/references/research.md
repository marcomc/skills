# Research and external skill assessment

Checked on 2026-11-05 through GitHub source/API and `skills@latest find` searches
for `test audit` and `test suite`. This is a bounded search, not a claim that no
other suitable skill exists. Source snapshots below identify what was assessed;
installation counts and repository stars are adoption signals, not safety proof.

## Relevant GitHub skills

| Candidate and assessed revision | Useful capability | Fit and limitation |
| --- | --- | --- |
| [dzhng/skills: audit-tests](https://github.com/dzhng/skills/blob/2fa832dcc42d4cca6497275b4aa4d4369662ceac/skills/engineering/audit-tests/SKILL.md) | Contract ownership, complete candidate evidence, regression falsification, no deletion quota | Closest general audit workflow; implementation and closure refer to companion skills. |
| [openclaw/openclaw: test-audit](https://github.com/openclaw/openclaw/blob/70bfdc2b58e42f02af5bdc4d345875a9e6ad3928/.agents/skills/test-audit/SKILL.md) | Authoring and pruning guidance, independent behavior, retention of operational contracts | Strong alternative; depends on OpenClaw-specific testing docs, review and companion skills. |
| [petrkindlmann/qa-skills: test-suite-curation](https://github.com/petrkindlmann/qa-skills/blob/9b08fa8417c87676105dfcc33e4d951a18a38493/skills/test-suite-curation/SKILL.md) | Coverage fingerprints, mutation comparisons, CI history and differentiated dispositions | Detailed whole-suite process; mandates human sign-off and a quarantine window, and expects companion QA skills. |
| [mblode/agent-skills: test-audit](https://github.com/mblode/agent-skills/blob/9fbd67776a92dc63912dce1efd73195945e97efb/skills/test-audit/SKILL.md) | Candidate evidence, per-file coverage and named survivors | Its default proposal removes 20% with a two-point coverage budget; retention rules mitigate this, but quotas and automatic loss budgets are unsuitable defaults here. Credits an OpenClaw adaptation. |
| [NeuraCerebra-AI/testprune](https://github.com/NeuraCerebra-AI/testprune/blob/5a1d68561d4d6c97e6955f20c05a78f85a88fe81/SKILL.md) | Production-path inventory, timing and explicit execution groups | Its rule to delete/archive permanently red tests needs stronger diagnosis; failure alone does not establish obsolete coverage. |

All five repositories reported MIT licensing at assessment time. This collection
does not vendor their code or instruction text. `streamline-test-suite` continues
an existing locally authored skill; these links document alternatives and trade-offs.
Repository policy requires an explicit personalization request before importing
a third-party adaptation.

## Established testing principles

[Yoo and Harman, *Regression testing minimization, selection and prioritization:
a survey*](https://coinse.github.io/publications/pdfs/Yoo2010fk.pdf), published
online in 2010 and in the 2012 journal volume, distinguishes:

| Technique | What changes | Operational implication |
| --- | --- | --- |
| Minimization / reduction | Membership of the maintained suite | Requires evidence that retained controls satisfy the required claims. |
| Regression test selection | The subset run for a particular change | Retains the larger suite; selection depends on changed code and dependencies. |
| Prioritization | Execution order | Gives earlier feedback without inherently deleting coverage. |

The implication column is this skill's operational interpretation, not a formal
guarantee supplied by the survey.

[Shi et al., *Evaluating Test-Suite Reduction in Real Software
Evolution*, ISSTA 2018](https://mir.cs.illinois.edu/gyori/pubs/issta18.pdf)
examines 1,478 failed builds from 32 projects. Some evaluated reductions missed
faults from builds the original suites detected; their failed-build detection
loss reached 52.2%. This is a result for the studied systems and reduction
criteria, not a predicted loss for an arbitrary cleanup. It supports checking
fault detection rather than inferring safety from suite size or coverage alone.

[PIT's mutation-testing documentation](https://pitest.org/) explains the
difference between executing code and detecting seeded defects. This skill uses
that distinction for bounded checks of disputed equivalence, while treating
mutation evidence as incomplete evidence about future faults.

## Chosen approach

Keep the existing self-contained skill and add explicit retirement decisions,
assertion/condition mapping and proportionate fault checks. Apply documented
project review requirements without imposing a universal waiting period. Require
real triggers for retained checks and state the detection delay of rescheduling.
Use runtime/resource savings as measured outcomes; a smaller test count is not
an objective that overrides required protection.
