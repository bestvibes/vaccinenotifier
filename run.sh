#!/usr/bin/env bash
source env.sh

set -xuo pipefail

. ./venv/bin/activate
while true; do
    python3 processlist.py custom.csv sheets.csv
    while IFS=, read -r age ind county zip num; do
        python3 scraper.py "$age" "$ind" "$county" "$zip" "$num"
    done < clean_list.csv
    sleep 900
done
