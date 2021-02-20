#!/usr/bin/env bash
source env.sh

set -xuo pipefail

. ./venv/bin/activate
while true; do
    python3 importlist.py
    sleep 900
done
