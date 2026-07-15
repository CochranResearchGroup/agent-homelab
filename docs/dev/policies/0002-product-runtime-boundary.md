# Policy | Product and runtime boundary

- Tracked code, schemas, templates, docs, tests, and skills are product behavior.
- Real inventories, rendered output, secrets, ACME state, OAuth state, backups, installed configuration, logs, and host discovery are runtime state.
- Never commit runtime state or make a generated file the only durable source of behavior.
- Keep one versioned inventory model and render every node from it.
- Convert reusable field repairs into generic code, tests, or skill guidance without copying private deployment values.
