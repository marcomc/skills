# Test disposition record

Use an existing project report or a compact table rather than creating a new
tracking system. Record only the scoped cases and evidence needed to justify
their disposition.

| Test ID / parameters | Protected failure and context | Decision | Survivor + trigger, or retirement evidence | Validation | Cost / uncertainty |
| --- | --- | --- | --- | --- | --- |
| `test_rounding[half-cent]` | Wrong monetary rounding | Keep | Unique expected value at the public API | Targeted runner result | Same lines as another test; different assertion |
| `test_parse_copy` | Same invalid input and error as `test_parse_invalid` | Remove duplicate | `test_parse_invalid`, required PR job | Inspected inputs/assertions/helpers; survivor passes | Report measured marginal savings, if available |
| `test_old_writer` | Generates a discontinued storage format | Remove obsolete | Retirement decision plus no supported writer consumers | Current reader/migration suites pass | Keep old-format reading and rejection controls |
| `test_retry_race` | Duplicate side effect under a particular callback order | Consolidate | Survivor receives that order before removal; PR job | Inject duplicate completion; survivor fails | A happy-path retry test is insufficient |

Examples illustrate decisions, not permission to classify tests by their names.
For a whole-suite audit, account for cases in shared and specialized suites as
well as the obvious directory; report the unexamined remainder when incomplete.

## Evidence that changes the decision

- **Same lines, different assertions:** an acceptance test verifies HTTP status;
  another verifies authorization scope. Keep both controls even if their line
  fingerprints match. A single test may absorb both assertions if its setup and
  failure sensitivity remain valid.
- **An old incident:** a bug is fixed, but an off-by-one input, race ordering or
  rollback condition can recur. Preserve that discriminator. A general success
  case does not subsume it merely because both call the repaired function.
- **Retired implementation, supported data:** removing a legacy writer does not
  retire reading old records, migrating them, or refusing them without data loss.
  Verify each remaining promise at a current production entry point.
- **One-off investigation:** a test pins a temporary implementation detail that
  no longer expresses a requirement. Removal can be justified by that absence;
  no replacement is necessary for a contract that never existed or has ended.
- **Cheap boundary protection:** an unusual input is rare but is the only guard
  against data loss or unauthorized access. Low frequency alone does not justify
  deleting it or moving it out of the merge gate.
- **Flaky fixture:** eliminate unnecessary waits or isolate state while retaining
  retry, timeout and error assertions. Report remaining uncertainty separately
  from product failures; use project quarantine rules when needed.

## Bounded fault checks

Choose a defect relevant to the claim: alter a comparison boundary, omit an
authorization filter, suppress rollback, or replay a completion callback. Exercise
the same defect against the original test and the proposed survivors in an
isolated workspace. Confirm failure comes from the intended assertion, then
confirm the unmodified implementation passes.

Use a project's mutation tool when it gives useful evidence at reasonable cost;
compare individual killed/surviving fault identities with a stable configuration.
Do not treat a mutant killed only by unrelated setup failure as preserved proof.
Exact duplicates can often be established by inspection of their full setup,
inputs and assertions plus focused execution; mutation testing is not a compulsory
whole-repository exercise for every deletion.

## Frequency and cost

Record a moved test's old/new commands, selection rules and CI triggers. A tag
without a job that selects it creates a coverage gap. A skipped cohort cannot
reveal escaped faults during an observation window unless it is actually run
through another documented mechanism.

Measure with comparable revisions, build/cache state, concurrency and runner
configuration. Parameterization can reduce maintenance while executing the same
number of cases; sharding can shorten elapsed time while increasing compute use.
Name the resource that improved and include the audit/instrumentation cost when
it materially affects the expected benefit.
