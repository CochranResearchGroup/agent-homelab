# Authelia authentication

Adding `auth.provider: authelia` renders both a Traefik forward-auth middleware and an Authelia access-control rule. The default policy remains `deny`.

Before apply, create the three secret files referenced by generated Compose config and populate `<state_root>/authelia/users_database.yml` with password hashes. The generated tree can be replaced atomically without replacing this persistent state root. Keep all state files untracked.

Expected unauthenticated behavior is a redirect to `https://auth.<site-domain>`. A hard `403` indicates policy mismatch; an unauthenticated backend `200` indicates missing protection.
