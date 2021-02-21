#!/usr/bin/env bash
source env.sh

set -xuo pipefail

. ./venv/bin/activate
while true; do
    python3 importlist.py
    if [ $? != 0 ]; then
        ./textme.sh ERROR: importlist broken
    fi
    date
    sleep 900
done
