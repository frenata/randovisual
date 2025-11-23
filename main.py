from pydantic import BaseModel
import functools
import logging
import re
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class Member(BaseModel):
    id: int
    names: set[str]
    years: set[int]

    def __init__(self, id: int, name: str, year: int):
        super().__init__(id=id, names={name}, years={year})

    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other):
        return self.id == other.id

    def add_name(self, name):
        self.names.add(name)

    def add_year(self, year):
        self.years.add(year)

def find_rusa_members():
    rusa_members = dict()
    years = range(1999, 2025)

    for year in years:
        print(f"Requesting yearly data for {year} ...")
        response = requests.get(f"https://rusa.org/yearly{year}.html")
        response.raise_for_status()

        html = BeautifulSoup(response.text, features="html.parser")

        for row in html.find_all("tr"):
            cell = row.find("td")
            if cell:
                if (
                    parsed := re.search(r"([\w\, ]+) \((\d+)\)", cell.text)
                ) and parsed is not None:
                    id = parsed[2]
                    name = parsed[1]

                    member = Member(id, name, year)
                    if member.id not in rusa_members:
                        rusa_members[member.id] = member
                    else:
                        member = rusa_members[member.id]
                        member.add_name(name)
                        member.add_year(year)

    print(f"Found {len(rusa_members)} total RUSA members across {len(years)} years")
    return rusa_members
