#!/usr/bin/env bash
source env.sh

set -uo pipefail

if [ $# -eq 0 ]; then
    echo "specify input data!"
    exit 1
fi

. ./venv/bin/activate
while true; do
    (set -x; python3 processlist.py $@)
    texted=0
    while IFS=, read -r age ind county zip num; do
        T="$(date +%s)";
        (set -x; python3 scraper.py "$age" "$ind" "$county" "$zip" "$num")
        T="$(($(date +%s)-T))";
        echo "Time in seconds: ${T}"
        if [ $? != 0 ] && [ $texted == 0 ]; then
            ./textme.sh ERROR: run broken for "$age" "$ind" "$county" "$zip"
            texted=1
        fi
    done < clean_list.csv
    date
    (set -x; sleep 900)
done
