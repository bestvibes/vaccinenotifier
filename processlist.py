#!/usr/bin/env python3

import sys
import itertools
import collections
import csv

from scraper import age_to_range, get_industries, Params

if len(sys.argv) == 1:
    print(f"Usage: {sys.argv[0]} filename...")
    sys.exit(1)

filename = sys.argv[1]
lines = []
for filename in sys.argv[1:]:
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        lines = [row for row in reader]
lines = [l for l in lines if not any(['#' in e for e in l])]
lines = [[d.strip() for d in l] for l in lines]
industries = get_industries()
for l in lines:
    assert len(l) == Params.SCRAPER_NUM_ARGS, l
    l[Params.SCRAPER_AGE_INDEX] = age_to_range(l[Params.SCRAPER_AGE_INDEX])
    assert l[Params.SCRAPER_INDUSTRY_INDEX].replace('"', "") in industries, l
    assert l[Params.SCRAPER_COUNTY_INDEX][0].isupper(), l
    if (l[Params.SCRAPER_UNDCONDITION_INDEX] == ""):
        l[Params.SCRAPER_UNDCONDITION_INDEX] = "No"
    assert l[Params.SCRAPER_UNDCONDITION_INDEX] in ["Yes", "No"], l
    if (l[Params.SCRAPER_DISABILITY_INDEX] == ""):
        l[Params.SCRAPER_DISABILITY_INDEX] = "No"
    assert l[Params.SCRAPER_DISABILITY_INDEX] in ["Yes", "No"], l
    assert len(l[Params.SCRAPER_ZIPCODE_INDEX]) == 5, l
    assert len(l[Params.SCRAPER_PHONE_INDEX]) >= 12, l
    for num in l[Params.SCRAPER_PHONE_INDEX].split('|'):
        assert num[0] == '+', num
        assert num[1] == '1', num

grouped_lines = []
for k,g in itertools.groupby(sorted(lines), key=lambda l: l[:-2]):
    group = k
    # numbers = set()
    numbers = collections.defaultdict(set)
    for line in g:
        for n in line[Params.SCRAPER_PHONE_INDEX].split('|'):
            numbers[line[Params.SCRAPER_ZIPCODE_INDEX]].add(n)
    zips = ""
    phones = ""
    for i, (zipcode,nums) in enumerate(numbers.items()):
        zips += ("|" if i > 0 else "") + zipcode
        phones += ("||" if i > 0 else "")
        for j, num in enumerate(nums):
            phones +=  ("|" if j > 0 else "") + num
    group.append(zips)
    group.append(phones)
    grouped_lines.append(group)
print(grouped_lines)
with open("clean_list.csv", 'w+') as f:
    f.write('\n'.join(map(','.join, grouped_lines)).replace('"', "")+'\n')
