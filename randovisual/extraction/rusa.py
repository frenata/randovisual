import datetime
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


class Ride(BaseModel):
    id: int
    # link: str
    date: datetime.date
    duration: int
    rider_id: int

def find_rusa_members(year: int):
    rusa_members = dict()

    logger.info(f"Requesting yearly data for {year} ...")
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

    logger.info(f"Found {len(rusa_members)} total RUSA members in {year} ride data.")
    return rusa_members

def parse_ride(rider_id, tag):
    """
    <tr class="individual-ride-result">
    <td align="left">RUSA-T132670</td>
    <td align="left">RUSAT</td>
    <td align="right">101</td>
    <td align="left">2025/07/13</td>
    <td align="left"></td>
    <td align="left"><a href="/cgi-bin/permview_GF.pl?permid=3016">FL: Panhandle Populaire</a></td>
    <td align="left">04:12</td>
    <td align="center"></td>
    </tr>
    """

    try:
        date = datetime.date.strptime(tag.select_one("td:nth-child(4)").text, "%Y/%m/%d")
        time = re.search(r'(\d+):(\d+)', tag.select_one("td:nth-child(7)").text)
        duration = datetime.timedelta(hours=int(time.group(1)), minutes=int(time.group(2)))
        route_link = f"https://rusa.org{tag.select_one("td:nth-child(6) > a").attrs["href"]}"

        if "permid" not in route_link:
            logger.info("not a permanent, skipping")
            return None
        permid = int(re.search(r'permid=(\d+)', route_link).group(1))

        ride = Ride(id=permid, date=date, duration=duration.total_seconds() / 60, rider_id=rider_id )
        # breakpoint()
        pass
        return ride
    except:
        logger.exception("error parsing ride result")
        return None





def find_rider_results(member: Member):
    logger.info(f"Requesting ride data for {member.id} ...")

    keys = ["mid", "sname", "club", "sortby", "regid", "type", "dist", "date", "rtid", "esortby", "permid", "permdate", "award", "year", "submit"]
    payload = {**{key: "" for key in keys}, "mid": str(member.id), "sortby": "date", "esortby": "name", "submit": "search"}
    # mid=14039&sname=&club=&sortby=date&regid=&type=&dist=&date=2024&rtid=&esortby=name&permid=&permdate=&award=&year=&submit=search
    response = requests.post("https://rusa.org/cgi-bin/resultsearch_PF.pl", data=payload)
    response.raise_for_status()

    html = BeautifulSoup(response.text, features="html.parser")
    results = html.select("tr.individual-ride-result")
    rides = list(filter(bool, map(functools.partial(parse_ride, member.id), results)))
    return rides
