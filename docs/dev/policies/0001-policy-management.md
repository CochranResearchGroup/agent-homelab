# Policy | Policy management

- Keep durable repo-local policy under `docs/dev/policies/` and wire it through `AGENTS.md`.
- Treat `AGENTS.md` as a routing surface that agents re-read when scope changes.
- Preserve product-specific commands and safety rules locally rather than copying unrelated generic policy.
- Review shared policy updates intentionally; never overwrite local operational nuance blindly.
