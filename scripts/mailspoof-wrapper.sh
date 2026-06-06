#!/bin/bash

PYTHON3="/usr/bin/python3"
if [[ ! -f "$PYTHON3" ]]; then
    PYTHON3=$(command -v python3 2>/dev/null || echo "")
fi
if [[ -z "$PYTHON3" ]]; then
    echo "[!] python3 not found. Install python3 first."
    exit 1
fi

exec "$PYTHON3" -m mailspoof "$@"
