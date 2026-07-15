FROM python:3.12-slim@sha256:c3d81d25b3154142b0b42eb1e61300024426268edeb5b5a26dd7ddf64d9daf28

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir --upgrade pip==26.1.2 && pip install --no-cache-dir .

USER 65532:65532
ENTRYPOINT ["python", "-m", "agent_homelab.oauth_relay"]
CMD ["--config", "/config/oauth-relay.yaml"]
