#!/usr/bin/env bash
source env.sh

set -uo pipefail

exit_script() {
    echo "exitting..."
    trap - SIGINT SIGTERM # clear the trap
    kill -- -$$ # Sends SIGTERM to child/sub processes
}

trap exit_script SIGINT SIGTERM

if [ $# -eq 0 ]; then
    echo "specify input data!"
    exit 1
fi

. ./venv/bin/activate
while true; do
    (set -x; python3 processlist.py $@)
    if [ $? != 0 ]; then
        ./textme.sh ERROR: processlist broken
    fi
    texted=0
    while IFS=, read -r age ind county undcond disability zip num; do
        T="$(date +%s)";
        (set -x; python3 scraper.py "$age" "$ind" "$county" "$undcond" "$disability" "$zip" "$num")
        if [ $? != 0 ] && [ $texted == 0 ]; then
            ./textme.sh ERROR: run broken for "$age" "$ind" "$county" "$undcond" "$zip" "$disability"
            texted=1
        fi
        T="$(($(date +%s)-T))";
        echo "Time in seconds: ${T}"
    done < clean_list.csv
    date
    (set -x; sleep 600)
done
