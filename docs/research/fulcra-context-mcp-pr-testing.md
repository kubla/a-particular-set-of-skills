# Pre-PR testing for the Fulcra MCP exact-type lookup fix

Researched 2026-08-31 against the official `fulcradynamics/fulcra-context-mcp` repository and its GitHub pull requests.

## Conclusion

Do not add a fake-client unit test for this fix. The useful regression proof is a red/green acceptance run through the actual local stdio MCP server, authenticated to a real Fulcra account containing multiple user-defined annotations with the same base type.

The proposed PR should remain a one-line behavior change in `fulcra_mcp/tools.py`. Before submitting it:

1. Run the unpatched and patched checkouts as local stdio MCP servers against the same Fulcra owner.
2. Prove the strict red/green A/B with one representative `MomentAnnotation/UUID` whose base has multiple peers.
3. On the patched checkout, repeat the real write-read-delete check for one representative each of Boolean, Duration, Moment, Numeric, and Scale. Each selected base must have more than one custom annotation, so the old lookup would necessarily take the ambiguity branch.
4. Keep a CLI write to the same exact type as the control, so an MCP failure cannot be misattributed to the type, payload, owner, or Fulcra backend.
5. Run source hygiene, package build, MCP startup, and the maintainer-triggered container build as separate checks. None substitutes for the live behavior proof.
6. Put the redacted exact results in the PR body and use `Closes #20`.

The already-completed exhaustive run is strong exploratory evidence: unpatched MCP `0/23`, patched MCP `23/23`, CLI control `23/23`, and cleanup verified. The PR need not make that exhaustive sweep its continuing acceptance contract. One strict Moment A/B plus one patched case per supported base family is the smaller sufficient proof.

## Why a fake client is the wrong regression boundary

This defect is a mismatch among three real interfaces:

- the exact composite ID returned by Fulcra's catalog;
- the ID accepted by the MCP `record_data` tool over stdio; and
- the base-type plus annotation-source representation ultimately accepted and persisted by Fulcra.

A fake that returns two entries for `MomentAnnotation` and one for `MomentAnnotation/UUID` would encode our understanding of `v1_catalog` in the test. It could prove which string this function passes to the fake, but it could not prove that the real catalog resolves that string, that real validation and ingestion accept the resulting record, that the record is attached to the intended custom annotation, or that it can be read and deleted afterward. Those are precisely the facts that distinguish the fix from a tautological assertion about its implementation.

The current repository has no established behavioral-test harness, `tests/` directory, test dependency, GitHub Actions workflow, `CONTRIBUTING.md`, or PR template in the [current repository tree](https://github.com/fulcradynamics/fulcra-context-mcp/tree/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2). Adding a mocked unit-test architecture to a one-line correctness PR would therefore be both broader than the fix and weaker than the acceptance evidence already available.

## What PR #14 establishes as house style

[PR #14, “Tool / description refresh”](https://github.com/fulcradynamics/fulcra-context-mcp/pull/14) introduced `record_data` and the repository's present developer tooling. It is the relevant precedent, with some precise limits:

- It explicitly advertised writes to user-defined `Type/UUID` IDs in the [PR body](https://github.com/fulcradynamics/fulcra-context-mcp/pull/14).
- Its developer tools inspect the actual FastMCP tool surface. [`scripts/simulate_tools.py`](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/scripts/simulate_tools.py) launches a real stdio or HTTP MCP server and calls `tools/list`; [`scripts/measure_tools.py`](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/scripts/measure_tools.py) uses a real FastMCP client against the tool server. The PR commit titled [“add a test”](https://github.com/fulcradynamics/fulcra-context-mcp/commit/e5f07b01abdd35940c4f2b39dc079e63c2e9bc4e) added that tool-surface measurement, not a fake behavioral client.
- The README recommends local stdio operation, MCP Inspector or `mcp-remote`, and the tool simulator as [developer/debugging paths](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/README.md#L30-L41).
- The merged PR received a successful maintainer-triggered [`mcp-publish-pr (fulcra-artifacts)` container build](https://github.com/fulcradynamics/fulcra-context-mcp/pull/14/checks). That establishes package/container viability, not behavioral correctness against Fulcra.
- Review discussion reasoned from real catalog behavior. A reviewer [asked what could produce multiple catalog entries](https://github.com/fulcradynamics/fulcra-context-mcp/pull/14#discussion_r3604758410), considering API versions and shares. Multiple same-base user annotations were the ordinary live case that the review did not capture.

PR #14 does not establish a conventional unit-test style. It establishes a preference for small developer scripts that inspect the real MCP surface, manual review grounded in actual Fulcra behavior, formatting passes, and a deployable container build. For this bug, the corresponding behavioral instrument is a real stdio `tools/call` acceptance run, not `tools/list` and not a fake Fulcra object.

## Real-system acceptance strategy

The repository-independent diagnostic in `a-particular-set-of-skills` is the durable test artifact:

```bash
uv run --script \
  tests/acceptance/request-image-generation/scripts/verify_custom_type_write_parity.py \
  --mcp-project /path/to/fulcra-context-mcp
```

The [diagnostic source](../../tests/acceptance/request-image-generation/scripts/verify_custom_type_write_parity.py) launches the candidate checkout as an actual stdio MCP server and uses MCP `initialize` and `tools/call`. Against the same authenticated owner, it:

1. Resolves the selected recordable user-defined annotation with the Fulcra CLI.
2. Confirms MCP and CLI report the same owner without printing that owner.
3. Confirms MCP `get_data_catalog` resolves each exact composite ID.
4. Writes an independently marked control record through the CLI.
5. Calls MCP `record_data` for the same exact type with a valid base-specific fixture.
6. Reads both outcomes independently through the CLI.
7. Deletes every marked test record and verifies its absence.
8. Redacts owner and annotation UUIDs from the report and exits nonzero on any write or cleanup failure.

For a clean red/green proof, run that command from two checkouts at the same source revision:

```text
main checkout:   entries = fulcra.v1_catalog(data_type=base_type)
patch checkout:  entries = fulcra.v1_catalog(data_type=data_type)
```

Use one configured Moment type for the strict red/green A/B. Then use one representative of each supported base on the patched checkout. Before selecting a representative, enumerate the catalog and confirm that its base has more than one custom annotation; otherwise that case would not demonstrate escape from the old ambiguity branch.

The compact pre-PR evidence should be:

| Check | Expected evidence | Cleanup |
|---|---|---|
| Unpatched local MCP, representative Moment | ambiguity failure | complete |
| Patched local MCP, same Moment | exact write observed | complete |
| CLI control, same Moment | exact write observed | complete |
| Patched local MCP, one each of 5 base families | 5/5 exact writes observed | complete |

The already-completed 23-type sweep established that the defect and fix behave uniformly across the account, but repeating all 23 before submission adds cost without testing another branch. The five-type sweep retains coverage of every supported fixture and ingestion shape; the strict Moment A/B proves that the one-line change, rather than some environmental difference, causes the result.

Before submission, rerun the representative cases from the exact commit intended for the PR. Preserve the redacted output as a local artifact and copy the compact A/B and five-family totals into the PR body. The test mutates the account only by creating uniquely marked records and is not complete unless its deletion and absence checks pass.

## Source, package, and MCP-surface checks

These checks answer different questions from the behavioral acceptance:

```bash
git diff --check
uv run python -m compileall -q fulcra_mcp
uv build
FULCRA_ENVIRONMENT=stdio uv run python scripts/simulate_tools.py \
  --command "uv run fulcra-context-mcp" --view directory
```

- `git diff --check` and compilation catch source mistakes.
- `uv build` proves the Python package can be built.
- `simulate_tools.py` proves the candidate starts over stdio and serves the expected MCP tool directory. It does not call `record_data`, so it is a smoke check, not the regression test.
- PR #14 includes dedicated `ruff format` and `ruff` commits, so formatting and lint should be checked. Current `main` has pre-existing whole-file Ruff findings; compare the base and patch outputs and require no new findings rather than mixing unrelated cleanup into this PR.

The repository's [Dockerfile](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/Dockerfile#L24) runs `uv sync --locked`. Current `main` has a pre-existing lock mismatch: `pyproject.toml` declares 0.1.9 while `uv.lock` records the package as 0.1.7, and a clean `uv sync --locked` fails. The one-line behavior fix does not cause that drift. Keep lock repair out of the correctness commit, disclose the baseline failure, and ask a maintainer whether they want a separate lock-only refresh before triggering `/gcbrun`.

Because the code change does not alter a tool name, description, parameter, input schema, or annotation, PR #14's [tool-context measurement requirement](https://github.com/fulcradynamics/fulcra-context-mcp/blob/b339aab9fff3bd70efa58b8589bcb2ff7a8d04a2/AGENTS.md#L107-L120) is not a material regression gate here. The stdio directory smoke confirms that the surface still loads.

## Should the upstream PR add a test artifact?

No additional test file is warranted for this one-line PR.

- Do not add the fake-client test.
- Do not copy the live-account harness into the MCP repository: it depends on a configured Fulcra account, invokes both the external CLI and MCP server, and intentionally creates and removes user data. It belongs in the acceptance repository where those mutation, owner, redaction, and cleanup contracts are already explicit.
- Do not modify `simulate_tools.py`; it is correctly scoped to tool-definition presentation and `tools/list`, not authenticated behavioral calls.

The upstream artifact should be the minimal source fix. The durable regression artifact remains the versioned acceptance harness, and the PR body should make its exact command and results reviewable. If Fulcra later establishes credentialed integration-test infrastructure with an isolated canary owner, this scenario is a strong candidate to move into that system; inventing a fake-client suite now would not approximate it.

## Suggested PR body contents

- `Closes #20`.
- Root cause: `record_data` parsed the custom UUID but discarded the full composite address for catalog lookup.
- Fix: pass `data_type` to `v1_catalog`; continue validating and ingesting with `base_type`, preserving the existing `v1alpha1` annotation record path and provenance behavior.
- Red/green real-system result: the unpatched representative Moment failed as ambiguous; the same patched Moment and CLI control passed; one patched representative from each of the five supported base families passed; cleanup complete.
- Exact acceptance command and a note that it launched each checkout as a local stdio MCP server against the same authenticated Fulcra owner.
- Source hygiene, package-build, stdio-startup, and no-new-Ruff-findings results.
- Explicit scope: no tool schema, tool description, API-version selection, base ingestion, validation, or provenance change.
- The pre-existing `uv sync --locked` failure, if it remains, plus a request for maintainer direction before `/gcbrun`.
- A request for the maintainer-triggered Cloud Build, while clearly describing it as a build/deployment check rather than behavioral coverage.
