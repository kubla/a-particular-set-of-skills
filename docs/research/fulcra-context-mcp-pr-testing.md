# Pre-PR testing for the Fulcra MCP exact-type lookup fix

Researched 2026-08-31 against the official `fulcradynamics/fulcra-context-mcp` repository and its GitHub pull requests.

## Conclusion

The fix can be tested confidently before submission, but the upstream repository does not currently provide a complete automated test contract. The strongest submission is therefore a small layered proof:

1. Add one deterministic regression test that fails with `v1_catalog(data_type=base_type)` and passes with `v1_catalog(data_type=data_type)`.
2. Run that test plus targeted formatting, lint, MCP-startup, and package-build checks locally.
3. Run the candidate checkout as a real stdio MCP server against the same live Fulcra account and verify exact custom-type writes and cleanup.
4. Put the exact commands and red/green results in the PR body, then ask a maintainer to run the repository's external Cloud Build check if needed.

This is stronger than the repository's usual minimum and closely follows its best prior testing examples.

## What the repository currently establishes

At current `main` (`b339aab`):

- There is no `tests/` directory, GitHub Actions workflow, `CONTRIBUTING.md`, or PR template in the [repository tree](https://github.com/fulcradynamics/fulcra-context-mcp/tree/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2).
- [`pyproject.toml`](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/pyproject.toml#L1-L31) declares runtime dependencies but no test runner or lint configuration. Ruff is supplied by the [Nix development shell](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/flake.nix#L21-L45), not by `uv sync`.
- The README recommends local stdio operation, MCP Inspector or `mcp-remote`, and the tool-description simulator as developer aids ([README lines 30-41](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/README.md#L30-L41)).
- `AGENTS.md` requires the tool-definition size measurement when adding or editing tools ([AGENTS.md lines 107-120](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/AGENTS.md#L107-L120)). This fix changes neither the tool description nor its schema, so that measurement is not material to the bug. A smoke `tools/list` check is enough for the MCP surface.

Several PRs show an external `mcp-publish-pr (fulcra-artifacts)` Cloud Build check. Collaborators trigger it with a `/gcbrun` comment in [PR #14](https://github.com/fulcradynamics/fulcra-context-mcp/pull/14) and [PR #13](https://github.com/fulcradynamics/fulcra-context-mcp/pull/13). The [successful PR #14 build](https://console.cloud.google.com/cloud-build/builds;region=us-west1/6da99198-74a4-4a31-970f-113d006f59b0?project=188670681733) checks out the source, builds the Docker image, and pushes it; it does not run a behavioral regression suite. Nor is it a dependable contributor-side gate: [PR #17](https://github.com/fulcradynamics/fulcra-context-mcp/pull/17), [PR #18](https://github.com/fulcradynamics/fulcra-context-mcp/pull/18), and [PR #19](https://github.com/fulcradynamics/fulcra-context-mcp/pull/19) merged while GitHub reported that check as `ACTION_REQUIRED`.

Current `main` also has a pre-existing locked-build problem. Its [Dockerfile](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/Dockerfile#L27) runs `uv sync --locked`, but that command currently fails in a clean checkout because the lock needs updating: `pyproject.toml` declares package version 0.1.9 while `uv.lock` still records 0.1.7, and current uv also refreshes the relative `exclude-newer` metadata. The exact-type fix does not cause that drift. Keep it out of the behavior commit; flag it to the maintainer before requesting Cloud Build, and let them choose a separate lock-only refresh if the build gate requires one.

## Relevant PR precedents

### Best behavioral-test precedent: PR #2

[PR #2, “Tolerate stringified arguments and harden MCP tool schemas”](https://github.com/fulcradynamics/fulcra-context-mcp/pull/2), is open rather than merged, but a Fulcra maintainer approved it. It is the closest precedent for this bug because it:

- adds focused pytest regression tests;
- obtains the MCP tool surface and tests generated schemas;
- monkeypatches the Fulcra client with a dummy object to assert exact arguments and behavior; and
- reports end-to-end testing through Claude against a real Fulcra account.

Its [`tests/test_tool_input_schemas.py` at the reviewed commit](https://github.com/fulcradynamics/fulcra-context-mcp/blob/4183dd6286aa3a5f387edf66e7a51b59b2d27c3d/tests/test_tool_input_schemas.py) shows the dummy-client and monkeypatch style. The caveat is important: the PR predates the current `fulcra_mcp/tools.py` architecture, remains unmerged, and its `pytest` dependency is not on current `main`.

### Best PR-description precedent: PR #17

[PR #17](https://github.com/fulcradynamics/fulcra-context-mcp/pull/17) is the clearest model for an external contribution. Its body states the problem and source-level choice, enumerates affected behavior, gives exact verification output for both stdio and deployed environments, measures the relevant regression surface, and names what is out of scope. It was then approved and merged.

### The change that introduced `record_data`: PR #14

[PR #14](https://github.com/fulcradynamics/fulcra-context-mcp/pull/14) introduced `record_data`, including its stated support for user-defined `Type/UUID` IDs. The implementation parses the UUID for provenance but, on current `main`, searches the catalog with only `base_type` before demanding one result ([source lines 255-277](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/fulcra_mcp/tools.py#L255-L277)). PR #14 contains no durable regression test for exact custom-type addressing. That is the gap this PR should close.

The issue is also continuous with the original review. A reviewer [asked what could produce multiple catalog entries](https://github.com/fulcradynamics/fulcra-context-mcp/pull/14#discussion_r3604758410) and considered multiple API versions and shared types. The ordinary case of several user-defined annotations with the same base was not captured. Linking that discussion in the new PR will make clear that the change resolves an already-recognized uncertainty in the multiple-match branch.

Earlier merged fixes such as [PR #1](https://github.com/fulcradynamics/fulcra-context-mcp/pull/1), [PR #5](https://github.com/fulcradynamics/fulcra-context-mcp/pull/5), and [PR #6](https://github.com/fulcradynamics/fulcra-context-mcp/pull/6) have short descriptions, approvals, and no visible automated checks or regression tests. They establish that the project has historically accepted light-weight fixes, not that omitting a regression test is preferable.

## Recommended regression test

Add one focused test around the plain async `record_data` function with a fake Fulcra client:

- Use a composite ID such as `MomentAnnotation/00000000-0000-4000-8000-000000000001`.
- Make the fake `v1_catalog` return two entries when called with `MomentAnnotation`, but exactly one recordable `v1alpha1` entry when called with the composite ID.
- Assert that the old implementation returns the ambiguity message and does not write.
- Assert that the fixed implementation calls `v1_catalog(data_type=<full composite ID>)`, validates and records through the base ingestion type, and adds the annotation UUID source.
- Add a second small assertion that a bare base ID is still passed unchanged. This protects existing behavior without inventing new selection rules.

That test directly encodes the bug in [Issue #20](https://github.com/fulcradynamics/fulcra-context-mcp/issues/20). It does not need network access, credentials, or a real UUID. Using `unittest.IsolatedAsyncioTestCase` and `unittest.mock` would avoid adding a test dependency; using pytest would follow PR #2's style but would require introducing and locking a development dependency.

The proposed dependency-free test was exercised in a temporary checkout. With the original lookup line restored, the exact-type test failed on the reported ambiguity message while the bare-base control passed. With the one-line fix applied, both tests passed in 5 ms. The test also asserts that validation and ingestion continue using the base type and `v1alpha1`, so it protects the deliberate distinction between exact catalog selection and base ingestion.

## Pre-submission command set

From the upstream checkout, after adding the regression test:

```bash
uv sync --frozen
uv run --frozen python -m unittest discover -s tests -v
uv run --frozen python -m compileall -q fulcra_mcp
uvx ruff check tests/test_record_data.py
uvx ruff format --check tests/test_record_data.py
git diff --check
uv build
FULCRA_ENVIRONMENT=stdio uv run python scripts/simulate_tools.py \
  --command "uv run --frozen fulcra-context-mcp" --view directory
```

If pytest is deliberately adopted instead, replace the unittest command with the exact locked pytest invocation and document the new development dependency. The simulator command is a cheap MCP-startup and `tools/list` smoke test; no change in emitted tool definitions is expected.

These narrower commands are deliberate. On current `main`, repository-wide Ruff reports pre-existing import-order and broad-exception findings in `fulcra_mcp/tools.py`, Ruff format would reformat an unrelated decorator, and the simulator's `--lint` mode reports 18 pre-existing description-line findings. Record those baselines rather than expanding this one-line correctness PR to clean them up.

The working command set above was exercised locally: both unit tests, compilation, targeted Ruff checks, package build, and the stdio `tools/list` smoke passed. `uv sync --locked` and the broader pre-existing lint gates failed for the baseline reasons just described.

Then run the repository-independent live parity diagnostic from `a-particular-set-of-skills`:

```bash
uv run --script \
  tests/acceptance/request-image-generation/scripts/verify_custom_type_write_parity.py \
  --all-annotations \
  --mcp-project /path/to/fulcra-context-mcp
```

The [diagnostic source](../../tests/acceptance/request-image-generation/scripts/verify_custom_type_write_parity.py) launches the candidate checkout over stdio, compares it with the Fulcra CLI against the same owner and type semantics, observes each record independently, deletes test records, and verifies their absence. The completed red/green run already established:

- unpatched MCP: `0/23` exact custom-annotation writes, all rejected as base ambiguity;
- patched MCP: `23/23` writes across Boolean, Duration, Moment, Numeric, and Scale annotations;
- CLI control: `23/23`; and
- cleanup complete.

Before submission, rerun the patched command from the exact commit intended for the PR and preserve the redacted JSON output or its exact summary in the PR body.

## Suggested PR body contents

- `Closes #20`.
- One-sentence root cause: `record_data` parsed the custom UUID but discarded it for catalog lookup.
- The one-line fix and why the full composite address is the correct catalog key.
- The deterministic regression-test command and result.
- The live A/B result: unpatched `0/23`, patched `23/23`, CLI `23/23`, cleanup verified.
- Formatting, lint, build, and stdio smoke results.
- The pre-existing `uv sync --locked` failure and a request for maintainer direction on the separate lock refresh needed by the Docker build.
- Explicit scope: no tool schema, description, base-ingestion, validation, or provenance change.
- A note requesting the maintainer-run Cloud Build check, without presenting its container build-and-push result as behavioral coverage.
