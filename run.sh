#!/usr/bin/env bash
source twilio.sh # add keys to env

set -xuo pipefail

. ./venv/bin/activate
while true; do
    python3 scraper.py 22 "Financial services" 94539 +11234567890
    sleep 900
done

