# vaccinenotifier
A super hacky web scraper I put together during the COVID-19 pandemic to help people find vaccine
appointments that were sparsely available by sending real-time texts. 100+ people found vaccines through this tool, with 20K+ texts sent!

## Architecture

For the tech-savvy, this tool has three main scripts: the importer, the grouper, and the scraper. The pipeline is as follows:
1) The [importer](importlist.py) pulls data from the [Google Form](https://bestvibes.me/vaccines/notify), and is run by [import.sh](import.sh).
It calculates the subscriptions/unsubscriptions, and outputs a csv, one row per subscription.
2) The [grouper](processlist.py) takes the importer's csv, and groups all subscriptions based on their form parameters, to amortize scraping. It then
outputs another csv, one row per group.
3) The [run script](run.sh) invokes the grouper, and for each row in its output csv, calls the scraper.
3) The [scraper](scraper.py), which operates on one group at a time, fills out the appointment website with the group's parameters, and if appointments
are available on the calender, sends texts to all the subscriptions in the group.

This full pipeline is run periodically in a stateless fashion for security, reliability and consistency.

## Disclaimer
Many tricks were used to bypass bot detection for the vaccine appointment website, all of which
are not present in this codebase and I will not go into. I made the best effort I could to ensure all users receiving texts were truly eligible for the
appointments. All user data was kept safely on hardware not publicly accessible by the Internet. I am not responsible for any deployments of this software
that are not my own.
