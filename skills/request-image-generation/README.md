# Request Image Generation

Request Image Generation gives an AI product a way to ask an image-capable agent for an image. The requester writes a compact brief into the owner's Fulcra context. A producer can find that Request later, make one or more candidate images, and leave Contributions that the requester can retrieve by exact ID.

The requesting product needs no image model, shell, or Fulcra CLI. It needs an authenticated Fulcra MCP connection with read and write access.

## Install in Claude

1. Download [`request-image-generation.zip`](https://github.com/kubla/a-particular-set-of-skills/releases/download/request-image-generation-v0.1.0/request-image-generation.zip).
2. In Claude, open **Customize → Skills**.
3. Click **+**, choose **Create skill**, then **Upload a skill**.
4. Upload the ZIP and enable Request Image Generation.
5. Connect Claude to your Fulcra account if it is not already connected. [Fulcra's agent setup guide](https://docs.fulcradynamics.com/agent-get-started.txt) covers the current MCP connection flow.

Claude supports personal custom skills on Free, Pro, Max, Team, and Enterprise plans when code execution and file creation are enabled. Anthropic maintains the current [custom-skill installation instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

Then ask for the image you need in ordinary language:

```text
Design a custom blazer button and make an image request for it.
```

Claude returns a receipt containing the exact `request_id`. Request creation stops there. It does not claim that a producer has seen or accepted the Request.

When an image-capable agent has contributed, ask Claude to check that exact Request:

```text
Check Request <request_id> for image Contributions and show me every verified candidate.
```

## Install in another compatible agent

Copy the complete `skills/request-image-generation/` directory into the agent's skills location. Keep `SKILL.md`, `references/`, and `agents/` together. The runtime must expose authenticated Fulcra MCP read and write operations; the skill intentionally assumes no shell or CLI.

## Set up a producer

Requests become useful when an image-capable agent can run the sibling [Image Upgrader](../image-upgrader/). Installation order does not matter. Either skill can establish the shared Image Upgrade Configuration in Fulcra; the producer also verifies an HTTPS route for finished images.

Scheduling belongs to the producer's environment. Image Upgrader can run on demand, on a schedule, or as part of a larger agent workflow.

## What crosses the boundary

Fulcra stores the brief, exact Request identity, Contribution links, timestamps, and provenance. Finished image bytes live at HTTPS URLs with declared media types and SHA-256 digests. The requester authorizes each redirect host and accepts the image only when the retrieved bytes match the digest.

Version `0.1.0` coordinates agents connected to the same Fulcra owner. Cross-owner coordination is [planned separately](https://github.com/kubla/a-particular-set-of-skills/issues/4).

## License

Apache 2.0. See the repository [LICENSE](../../LICENSE).
