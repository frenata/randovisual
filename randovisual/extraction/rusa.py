import os
import datetime
from pydantic import BaseModel
import functools
import logging
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

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
    rusa_id: int
    date: datetime.date
    duration: int
    rider_id: int
    category: str
    name: str

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
        category = tag.select_one("td:nth-child(2)").text
        date = datetime.date.strptime(tag.select_one("td:nth-child(4)").text, "%Y/%m/%d")
        time = re.search(r'(\d+):(\d+)', tag.select_one("td:nth-child(7)").text)
        duration = datetime.timedelta(hours=int(time.group(1)), minutes=int(time.group(2)))
        route_link = f"https://rusa.org{tag.select_one("td:nth-child(6) > a").attrs["href"]}"
        name = tag.select_one("td:nth-child(6)").text

        if "permid" in route_link:
            rusa_id = int(re.search(r'permid=(\d+)', route_link).group(1))
        elif "rtid" in route_link:
            rusa_id = int(re.search(r'rtid=(\d+)', route_link).group(1))
        else:
            raise ValueError(f"unknown route link type: {route_link} for rider: {rider_id}")

        ride = Ride(rusa_id=rusa_id, date=date, duration=duration.total_seconds() / 60, rider_id=rider_id, category=category, name=name)
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


def get_rwgps_info(rwgps_id):
    response = requests.get(f"https://ridewithgps.com/api/v1/routes/{rwgps_id}.json", headers={"x-rwgps-api-key": os.getenv("RWGPS_API_KEY"), "x-rwgps-auth-token": os.getenv("RWGPS_API_TOKEN")})
    response.raise_for_status()

    points = ','.join(f'{p["x"]} {p["y"]} {p["e"]}' for p in response.json().get("route").get("track_points"))
    geometry = f"LINESTRING Z({points})"
    return geometry


def _get_perm_info(route_id, existing_route = None):
    response = requests.get(f"https://rusa.org/cgi-bin/permview_GF.pl?permid={route_id}")
    response.raise_for_status()
    html = BeautifulSoup(response.text, features="html.parser")

    rwgps = html.find(lambda tag: tag.name == "a" and "ridewithgps" in tag.attrs.get("href", ""))
    name = html.select_one("table > tr:nth-child(2) > td").text
    climbing = int(html.select_one("table > tr:nth-child(6) > td").text)

    response = {"rusa_id": route_id, "name": name, "climbing": climbing, "category": category}

    if rwgps is None:
        return None
    if existing_route is None or existing_route.geometry is None:
        rwgps_id = rwgps.attrs["href"].split("/")[-1]
        try:
            geometry = get_rwgps_info(rwgps_id)
            response["geometry"] = geometry
            response["rwgps_id"] = rwgps_id
        except Exception:
            # NOTE: if rwgps fails, we'll capture the data we have
            logger.exception("failed to extract from rwgps")

    return response


def _get_brevet_info(route_id, name: str, category: str, existing_route = None):
    response = requests.get(f"https://rusa.org/cgi-bin/routesearch_PF.pl?rtid={route_id}")
    response.raise_for_status()
    html = BeautifulSoup(response.text, features="html.parser")

    response = {"rusa_id": route_id, "name": name, "category": category}
    try:
        climbing = int(html.select_one("td:nth-child(4)").text.strip())
        # NOTE: brevets only show climbing in ft, so we convert to m
        response["climbing"] = int(climbing / 3.281)
    except:
        logger.warn("no climbing data found")

    return response

def get_route_info(route_id, name: str, category: str, existing_route = None):
    if category in ["RUSAT", "ACPT-SR6"]:
        return _get_perm_info(route_id, existing_route)
    else:
        return _get_brevet_info(route_id, name, category, existing_route)
