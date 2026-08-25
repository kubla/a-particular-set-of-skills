# Computer History Collector

If you already use Codex Computer History, Codex is writing compact summaries of your work. The Computer History Collector copies each completed summary into your Fulcra context lake. Agents you authorize can then read the same work history and put it to use in more ways than one.

> **Agents can't volunteer for work they can't see.**

This skill grew out of simple curiosity about what Computer History was saving. It's more than a simple log; for instance, at the time I'm writing this (2026-August-28), each file has a section delightfully named `### Important non-obvious context about the user`

In my corpus of Codex Computer History memory files, this is where Codex records inferences about me that might matter later.

One six-hour summary included this observation:

> A key design gap surfaced during review: the guide may need an explicit maintenance or curation pattern and a worked composition example combining several patterns.

And that's when I thought: I gotta get this in the hands of my other agents. I want my agents to see the gaps! I want them to offer to draft the missing pattern or example. I do not want to have to notice the opportunity, decide it was delegable, and formulate the task first.

## Be aware: this context is personal

I wrote this Collector for people who have already decided to turn Computer History on. I am not here to talk you into it. I just think, if you do turn it on, its output should belong to you, it should persist even if you uninstall Codex, and you should be able to do whatever you want with it.

Computer History records *behavior*, not just project names. In my summaries, it noticed occasions when I switched focus during Zoom calls to Slack, web search, and other applications. Of course you *should* be checking Slack and doing web searches during Zoom calls when that's relevant to what you're working on. I just want you to know that if you play Wordle while you are supposedly paying attention to a status meeting, you should assume Computer History will notice *and it will write it down*. You are giving a lot of trust to Codex when you flip this feature on.

Saving that context in Fulcra does not make it less sensitive. It changes where it lives, and you can potentially change who gets access. Data in a Fulcra account belongs to the account owner, who decides which people and tools can read it. If you let Claude, Hermes, OpenClaw, or another agent read it, you are trusting that agent with it.

I work on Fulcra. I built this because I want the context my agents learn about me to belong to me and to be available to the other agents I choose.

Read more about [Fulcra's principles of Data Sovereignty and Safety](https://www.fulcradynamics.com/legal/data-safety), [privacy policy](https://www.fulcradynamics.com/legal/privacy-policy), [terms of use](https://www.fulcradynamics.com/legal/terms-of-use), and [how to connect your Fulcra account to anything](https://www.fulcradynamics.com/developers).

## What the Collector does

The Collector projects completed Computer History Markdown summaries (not the raw activity event stream that Codex collects and inspects to create these summaries). Codex writes these to disk in two forms: a file covering 10 minutes and a file covering 6 hours.

For each completed summary, the Collector maintains:

- the original Markdown as a Fulcra file snapshot;
- one duration annotation in either `Computer History (10-minute)` or `Computer History (6-hour)`;
- the summary Markdown as the annotation note, with its terminal local-file citations omitted;
- provenance identifying Codex, Computer History, and the computer that produced it; and
- human-readable tags for the computer and applications listed in the summary.

A per-user macOS LaunchAgent sweeps for new completed summaries about every ten minutes. Revisions advance the existing projection rather than leaving overlapping records. A local file disappearing does not instruct the Collector to delete context already retained in Fulcra.

The detailed contract lives in [references/behavior.md](references/behavior.md).

## Install in Codex

This skill assumes Computer History is already enabled on a Mac. It requires `uv` and network access. Setup will ask you to sign in to Fulcra or create a free account if needed.

Ask Codex:

```text
Use $skill-installer to install the computer-history-collector skill from:
https://github.com/kubla/a-particular-set-of-skills/tree/main/skills/computer-history-collector
```

The skill becomes available on the next turn. Before setup, ask it to show you one real projection without making any changes:

```text
Use $computer-history-collector to preview one real annotation for me before setting anything up.
```

Preview reads one completed local summary and shows the note, interval, tags, provenance, data type, and destination path. It does not authenticate or write to Fulcra. Setup begins only after you ask to continue.

## Install in another compatible agent

Copy the complete `skills/computer-history-collector/` directory into the agent's skills location. Keep `SKILL.md`, `scripts/`, `references/`, and `agents/` together. See the [Agent Skills specification](https://agentskills.io/specification) for client-specific discovery rules.

## Operate or remove it

The agent-facing [SKILL.md](SKILL.md) documents setup, status, diagnosis, manual sweeps, and uninstall. Uninstall removes the local runtime and scheduler, but retains the context and source snapshots already stored in Fulcra.

## License

Apache 2.0. See the repository [LICENSE](../../LICENSE).
