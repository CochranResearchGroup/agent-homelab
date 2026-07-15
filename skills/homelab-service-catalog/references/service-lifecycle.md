# Service lifecycle contract

Before startup, record the official deployment authority, pinned version, component list, upstream port, canonical URL settings, secret references, persistent inputs, and backup owner.

For `upstream-compose-release`, download the Compose and environment examples from the same tagged release. For `compose-from-official-documentation`, recreate only the documented topology and retain the documentation URL in the operator handoff.

State ownership categories:

- `bind mount`: archive the resolved host path.
- `named volume`: export it while the stack is stopped, then include the export in Borg.
- `application-native`: execute and verify the application's supported backup workflow.
- `application-native-plus-stop`: retain the application/database export and the stopped filesystem snapshot as one documented recovery set.

Completion evidence must identify the raw health result, ingress result, application URL/callback result, Borg archive name, repository check result, and staging restore destination. Values that reveal private topology or identity stay in ignored runtime logs, not Git or agent memory.
