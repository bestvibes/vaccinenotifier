#!/usr/bin/env bash
source twilio.sh # add keys to env

set -xuo pipefail

. ./venv/bin/activate
while true; do
    python3 processlist.py list.csv
    while IFS=, read -r age ind zip num; do
        python3 scraper.py "$age" "$ind" "$zip" "$num"
    done < clean_list.csv
    sleep 900
done
