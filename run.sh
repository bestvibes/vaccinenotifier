#!/usr/bin/env bash
source env.sh

set -xuo pipefail

. ./venv/bin/activate
while true; do
    python3 processlist.py custom.csv sheets.csv
    texted=0
    while IFS=, read -r age ind county zip num; do
        python3 scraper.py "$age" "$ind" "$county" "$zip" "$num"
        if [ $? != 0 ] && [ $texted == 0 ]; then
            ./textme.sh ERROR: run broken for "$age" "$ind" "$county" "$zip"
            texted=1
        fi
    done < clean_list.csv
    date
    sleep 900
done
