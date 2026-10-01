#!/usr/bin/env bash
# Mirrors fail transiently. Without retries, one flaky mirror would fail the
# whole run.
set -euo pipefail

attempt=1
until "$@"; do
  attempt=$((attempt + 1))
  if [ "$attempt" -gt 3 ]; then
    echo "::error::Command failed after three attempts: $*"
    exit 1
  fi
  echo "::warning::Command failed (attempt $((attempt - 1))/3), retrying in 10s: $*"
  sleep 10
done
