# Runtime and lifecycle boundaries

Select the relevant contract; use the real wrapper/entrypoint when source-only
tests can miss generated state, forwarding, target selection or cleanup.

- Validate mutually exclusive/required-together CLI flags before dispatch can
  pre-empt another mode. Tokenize forwarded arguments as data, never `eval` or
  shell expansion. Exercise malformed/injection-shaped input without side effects;
  reject unsupported quoting explicitly instead of corrupting it.
- Prove dry-run, preview, validate, list, disabled and read-only paths preserve
  their side-effect contract, including nested privileged/prompt-capable helpers.
  Defaults and examples must keep opt-in telemetry inert.
- Check repeated triggers and shared-resource ownership. Cancellation, timeouts,
  retries and terminal errors must stop sibling work without secondary tracebacks.
- Enumerate durable transitions and the next fallible action. Persist checkpoints
  before proceeding, including fallback journals; test recovery after ordinary
  failures and hard interruption at affected boundaries. Inspect live state after
  deliberate test drift; never rely on a stale pre-test cleanup assumption.
- Disable/teardown must clear obsolete units, policies, journals, cron entries,
  generated state and grants. Order Makefile side effects within a recipe or use
  an explicit non-parallel flow; prerequisite order alone does not survive `-j`.
- Trace workspace/CI wrappers through rendered config, environment forwarding and
  the target container. Validate service creation when interpolation is involved;
  a rendered config alone does not prove the running container received it.
  Keep host-only cache paths and symlinks out of container-backed checks.
- In Jenkins, inspect checkout/unstash at agent switches and workspace availability
  during `post` cleanup. Toolchains run in the intended container; credentials
  cross through environment rather than command arguments. Preserve documented
  operator controls for publication, live tests, cleanup and release versions.
- Distinguish dev/staging/prod wrappers, inventories and failover targets. For
  affected HA lifecycle, validate enable/bootstrap, canonical deploy and a narrow
  promotion/failover scenario. PRIMARY/SECONDARY instances must not collide over
  host ports, volumes, project names or singleton resources.
- Keep every probe on the selected adapter/host/device/credential. Verify vendor
  identifier translation, default-unhealthy/selected-healthy, missing-selected/
  other-present and already-normalized cases. Parse the intended field and test
  protocol acceptance/authentication, not merely transport reachability.
- Exercise skew, future/stale time markers, zero intervals and catch-up when
  scheduling changes. Bound loops on terminal failures as well as deadlines.
- Validate portability on supported developer hosts (including macOS/BSD); use
  real target package-manager admission for dependencies and minimal-package
  conflicts. Cover ignored/private runtime inputs in deploy and stale-check maps.

Required live checks remain subject to existing authorization and environment
availability. Report an unavailable required proof as a gap, not an execution
success or permission to perform an otherwise unauthorized operation.
