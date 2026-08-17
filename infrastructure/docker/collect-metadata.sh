#!/bin/sh
# Evidence collector — gathers environment metadata
echo "{"
echo "  \"runner_version\": \"1.0.0\","
echo "  \"hostname\": \"$(hostname)\","
echo "  \"uid\": \"$(id -u)\","
echo "  \"gid\": \"$(id -g)\","
echo "  \"kernel\": \"$(uname -r)\","
echo "  \"source_mounted\": $([ -d /source ] && echo 'true' || echo 'false'),"
echo "  \"workspace_writable\": $([ -w /workspace ] && echo 'true' || echo 'false'),"
echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\""
echo "}"
