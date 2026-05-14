#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <feed_url> [--interval SECONDS] [--limit N]"
  exit 1
fi

python scripts/terminal_reader.py "$@"
