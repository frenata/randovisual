import functools
import logging
import re
from collections import defaultdict

from bs4 import BeautifulSoup
from dlt.sources.helpers import requests

logger = logging.getLogger(__name__)

# pipeline = dlt.pipeline(
#     pipeline_name='rusa yearly results',
#     destination='duckdb',
#     dataset_name='rusa'
# )


def find_rusa_members():
    rusa_ids = defaultdict(set)
    years = range(1999, 2025)

    for year in years:
        response = requests.get(f"https://rusa.org/yearly{year}.html")
        response.raise_for_status()

        html = BeautifulSoup(response.text, features="html.parser")

        for row in html.find_all("tr"):
            cell = row.find("td")
            if cell:
                # rusa_id = groups[1] if (groups := ) else None
                if (
                    rusa_id := re.search(r"\((\d+)\)", cell.text)
                ) and rusa_id is not None:
                    rusa_ids[year].add(rusa_id[1])

    all_ids = functools.reduce(
        lambda total, year: total.union(year), rusa_ids.values(), set(),
    )
    print(f"Found {len(all_ids)} total RUSA members across {len(years)} years")

    return rusa_ids
