# Provider adapter contract

The start command receives `OAUTH_RELAY_PROVIDER`, `OAUTH_RELAY_TENANT`, `OAUTH_RELAY_REDIRECT_URI`, and `OAUTH_RELAY_STATE`. It writes one JSON object containing `authorization_url`.

The finish command additionally receives `OAUTH_RELAY_CALLBACK_URL`. It exchanges and stores credentials without printing tokens or callback data.

Authorization URLs must use HTTPS and an exact configured host. In `relay` state mode, the returned URL must contain the provided state. In `adapter` mode, the returned state must be at least 32 characters and is registered, bound, expired, and consumed by the relay.
