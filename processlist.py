#!/usr/bin/env python3

import sys
from scraper import age_to_range, get_industries
import itertools

if len(sys.argv) == 1:
    print(f"Usage: {sys.argv[0]} filename...")
    sys.exit(1)

filename = sys.argv[1]
lines = []
for filename in sys.argv[1:]:
    with open(filename, 'r') as f:
        lines.extend(f.readlines())
lines = [l.replace('"',"").strip().split(',') for l in lines if '#' not in l and l.strip() != ""]
industries = get_industries()
for l in lines:
    assert len(l) == 5, l
    assert l[1].replace('"', "") in industries, l
    assert l[2][0].isupper(), l
    assert len(l[3]) == 5, l
    assert len(l[4]) >= 12, l
    for num in l[4].split('|'):
        assert num[0] == '+', num
        assert num[1] == '1', num
    l[0] = age_to_range(l[0])

grouped_lines = []
for k,g in itertools.groupby(sorted(lines), key=lambda l: l[:-1]):
    group = k
    numbers = set()
    for line in g:
        for n in line[-1].split('|'):
            numbers.add(n)
    group.append('|'.join(numbers))
    grouped_lines.append(group)
print(grouped_lines)
with open("clean_list.csv", 'w+') as f:
    f.write('\n'.join(map(lambda l: ','.join(map(str.strip, l)), grouped_lines)).replace('"', "")+'\n')
