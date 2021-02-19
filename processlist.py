#!/usr/bin/env python3

import sys
from scraper import age_to_range, get_industries

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} filename")
    sys.exit(1)

filename = sys.argv[1]
with open(filename, 'r') as f:
    lines = f.readlines()
lines = [l.strip().split(',') for l in lines if '#' not in l]
industries = get_industries()
for l in lines:
    assert len(l) == 4, l
    assert l[1].replace('"', "") in industries, l
    assert len(l[2]) == 5, l
    assert len(l[3]) == 12, l
    assert l[3][0] == '+', l
    assert l[3][1] == '1', l
    l[0] = '"'+age_to_range(l[0])+'"'
print(lines)
with open("clean_"+filename, 'w+') as f:
    f.write('\n'.join(map(','.join, lines)).replace('"', "")+'\n')
