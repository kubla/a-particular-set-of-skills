# Image Upgrader

Image Upgrader is the producer side of a Fulcra image-generation handoff. An image-capable agent finds Image Upgrade Requests left by another AI product, makes a useful candidate, publishes the image through an HTTPS route already available in its environment, and records a Contribution linked by the exact `request_id`.

Requests are open invitations. They may receive zero, one, or many Contributions. Image Upgrader adds another candidate only when it offers a distinct interpretation, useful variant, or requested revision.

## Install in Codex

Ask Codex:

```text
Use $skill-installer to install the image-upgrader skill from:
https://github.com/kubla/a-particular-set-of-skills/tree/main/skills/image-upgrader
```

The skill becomes available on the next turn. It requires:

- image-generation capability;
- `uv` and network access;
- an authenticated Fulcra account; and
- an authorized way to publish the finished bytes at an HTTPS URL.

Ask the installed skill to set up coordination:

```text
Use $image-upgrader to set up Image Upgrade coordination in my Fulcra account.
```

Setup verifies the authenticated owner, creates or adopts one unambiguous Request/Contribution type pair, and writes the owner-scoped Image Upgrade Configuration. Producer setup also proves the publication route with known canary bytes before trusting it for Contributions.

## Install in another compatible agent

Copy the complete `skills/image-upgrader/` directory into the agent's skills location. Keep `SKILL.md`, `scripts/`, `references/`, and `agents/` together. The host must provide image generation and the declared CLI, network, authentication, and publishing capabilities.

## Contribute to a Request

Invoke Image Upgrader with an exact Request ID when you have one:

```text
Use $image-upgrader to handle Image Upgrade Request <request_id>.
```

It can also discover recent Requests, prioritizing those without Contributions. The skill inspects the brief and existing candidates, retrieves authorized inputs, generates an image, verifies the published bytes, and records the Contribution with `com.fulcradynamics.agent-skills.image-upgrader` provenance.

The skill does not install a scheduler or polling service. Run it on demand or invoke it through whatever scheduling system the agent host already provides.

## Request from Claude or another MCP-only product

Install the sibling [Request Image Generation](../request-image-generation/) skill in the requesting product. The two skills share a versioned `image-upgrade/v1` contract through Fulcra; they do not need a shared process, chat, filesystem, or model provider.

Version `0.1.0` coordinates agents connected to the same Fulcra owner. Cross-owner coordination is [planned separately](https://github.com/kubla/a-particular-set-of-skills/issues/4).

## License

Apache 2.0. See the repository [LICENSE](../../LICENSE).
