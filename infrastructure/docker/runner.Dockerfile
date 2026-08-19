# RepoProof Runner — minimal trusted base image
# Mission 006: Used for isolated target repository verification.

FROM alpine:3.21@sha256:a8560b36e8b8210634f77d9f7f9efd7ffa463e380b75e2e74aff4511df3ef88c

LABEL org.repoproof.runner.version="1.0.0"
LABEL org.repoproof.runner.purpose="isolated-verification"
LABEL org.repoproof.build.timestamp="2026-07-28"

# Non-root user
RUN addgroup -g 1000 repoproof && \
    adduser -D -u 1000 -G repoproof -h /home/repoproof repoproof

# Minimal utilities for health checks and evidence collection
RUN apk add --no-cache \
    curl \
    bash \
    findutils \
    git \
    python3 \
    py3-pip \
    py3-pytest \
    nodejs \
    npm \
    && rm -rf /var/cache/apk/*

# Health probe
COPY --chown=repoproof:repoproof healthcheck.sh /healthcheck.sh
RUN chmod +x /healthcheck.sh

# Trusted entrypoint
COPY --chown=repoproof:repoproof entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Evidence collector
COPY --chown=repoproof:repoproof collect-metadata.sh /usr/local/bin/collect-metadata
RUN chmod +x /usr/local/bin/collect-metadata

# Work directories
RUN mkdir -p /source /workspace /tmp && \
    chown repoproof:repoproof /workspace /tmp

USER repoproof
WORKDIR /workspace

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD /healthcheck.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "3600"]
