import datetime
import functools
import logging
import os
import re

import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
from pydantic import BaseModel

import randovisual.db.models as models

load_dotenv()

logger = logging.getLogger(__name__)


class Member(BaseModel):
    id: int
    names: set[str]
    years: set[int]

    def __init__(self, mid: str, name: str, year: int) -> None:
        super().__init__(id=mid, names={name}, years={year})

    def __hash__(self) -> int:
        return self.id.__hash__()

    def __eq__(self, other) -> bool:  # noqa: ANN001
        return self.id == other.id

    def add_name(self, name: str) -> None:
        self.names.add(name)

    def add_year(self, year: int) -> None:
        self.years.add(year)


class Ride(BaseModel):
    rusa_id: int
    date: datetime.date
    duration: int
    rider_id: int
    category: str
    name: str


def find_rusa_members(year: int) -> list[Member]:
    rusa_members: dict[int, Member] = {}

    logger.info(f"Requesting yearly data for {year} ...")
    response = requests.get(f"https://rusa.org/yearly{year}.html")
    response.raise_for_status()

    html = BeautifulSoup(response.text, features="html.parser")

    for row in html.find_all("tr"):
        cell = row.find("td")
        if cell and (parsed := re.search(r"([\w\, ]+) \((\d+)\)", cell.text)) and parsed is not None:
            mid = parsed[2]
            name = parsed[1]

            member = Member(mid, name, year)
            if member.id not in rusa_members:
                rusa_members[member.id] = member
            else:
                member = rusa_members[member.id]
                member.add_name(name)
                member.add_year(year)

    logger.info(f"Found {len(rusa_members)} total RUSA members in {year} ride data.")
    return list(rusa_members.values())


def parse_ride(rider_id: int, tag: Tag) -> Ride | None:
    """<tr class="individual-ride-result">
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
        name = tag.select_one("td:nth-child(6)").text  # ty: ignore[possibly-missing-attribute]
        category = tag.select_one("td:nth-child(2)").text  # ty: ignore[possibly-missing-attribute]
        date = datetime.datetime.strptime(
            tag.select_one("td:nth-child(4)").text,  # ty: ignore[possibly-missing-attribute]
            "%Y/%m/%d",
        )
        time = re.search(r"(\d+):(\d+)", tag.select_one("td:nth-child(7)").text)  # ty: ignore[possibly-missing-attribute]
        duration = datetime.timedelta(
            hours=int(time.group(1)),  # ty: ignore[possibly-missing-attribute]
            minutes=int(time.group(2)),  # ty: ignore[possibly-missing-attribute]
        )

        if name == "Paris-Brest-Paris":
            rusa_id = 999999
        else:
            route_link = f"https://rusa.org{tag.select_one('td:nth-child(6) > a').attrs['href']}"  # ty: ignore[possibly-missing-attribute]

            if "permid" in route_link:
                rusa_id = int(re.search(r"permid=(\d+)", route_link).group(1))  # ty: ignore[possibly-missing-attribute]
            elif "rtid" in route_link:
                rusa_id = int(re.search(r"rtid=(\d+)", route_link).group(1))  # ty: ignore[possibly-missing-attribute]
            else:
                raise ValueError(
                    f"unknown route link type: {route_link} for rider: {rider_id}",
                )

        return Ride(
            rusa_id=rusa_id,
            date=date,
            duration=duration.total_seconds() // 60,  # ty: ignore[invalid-argument-type]
            rider_id=rider_id,
            category=category,
            name=name,
        )
    except Exception:
        logger.exception("error parsing ride result")
        return None


def find_rider_results(member: Member) -> list[Ride]:
    logger.info(f"Requesting ride data for {member.id} ...")

    keys = [
        "mid",
        "sname",
        "club",
        "sortby",
        "regid",
        "type",
        "dist",
        "date",
        "rtid",
        "esortby",
        "permid",
        "permdate",
        "award",
        "year",
        "submit",
    ]
    payload = {
        **dict.fromkeys(keys, ""),
        "mid": str(member.id),
        "sortby": "date",
        "esortby": "name",
        "submit": "search",
    }
    response = requests.post(
        "https://rusa.org/cgi-bin/resultsearch_PF.pl",
        data=payload,
    )
    response.raise_for_status()

    html = BeautifulSoup(response.text, features="html.parser")
    results = html.select("tr.individual-ride-result")
    return list(filter(bool, map(functools.partial(parse_ride, member.id), results)))


def get_rwgps_info(rwgps_id: str) -> str:
    response = requests.get(
        f"https://ridewithgps.com/api/v1/routes/{rwgps_id}.json",
        headers={
            "x-rwgps-api-key": os.getenv("RWGPS_API_KEY"),
            "x-rwgps-auth-token": os.getenv("RWGPS_API_TOKEN"),
        },
    )
    response.raise_for_status()

    points = ",".join(f"{p['x']} {p['y']} {p['e']}" for p in response.json().get("route").get("track_points"))
    return f"LINESTRING Z({points})"


def _get_perm_info(route_id: int, category: str, existing_route: models.Route | None = None) -> dict | None:
    response = requests.get(
        f"https://rusa.org/cgi-bin/permview_GF.pl?permid={route_id}",
    )
    response.raise_for_status()
    html = BeautifulSoup(response.text, features="html.parser")

    rwgps = html.find(
        lambda tag: tag.name == "a" and "ridewithgps" in tag.attrs.get("href", ""),
    )
    try:
        name = html.select_one("table > tr:nth-child(2) > td").text  # ty: ignore[possibly-missing-attribute]
        climbing = int(html.select_one("table > tr:nth-child(6) > td").text)  # ty: ignore[possibly-missing-attribute]

        response = {
            "rusa_id": route_id,
            "name": name,
            "climbing": climbing,
            "category": category,
        }
    except Exception:
        return None

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


def _get_brevet_info(route_id: int, name: str | None, category: str, rwgps_id: str | None = None) -> dict:
    response = requests.get(
        f"https://rusa.org/cgi-bin/routesearch_PF.pl?rtid={route_id}",
    )
    response.raise_for_status()
    html = BeautifulSoup(response.text, features="html.parser")

    response = {"rusa_id": route_id, "name": name, "category": category}
    try:
        if (tag := html.select_one("td:nth-child(4)")) and tag is not None:
            climbing = int(tag.text.strip())
            # NOTE: brevets only show climbing in ft, so we convert to m
            response["climbing"] = int(climbing / 3.281)
    except Exception:
        logger.info("no climbing data found")

    if rwgps_id is not None:
        geometry = get_rwgps_info(rwgps_id)
        response["geometry"] = geometry
        response["rwgps_id"] = rwgps_id

    return response


def get_route_info(
    route_id: int,
    name: str | None,
    category: str,
    *,
    existing_route: models.Route | None = None,
    rwgps_id: str | None = None,
) -> dict | None:
    if category in ["RUSAT", "ACPT-SR6"]:
        return _get_perm_info(route_id, category, existing_route)
    return _get_brevet_info(route_id, name, category, rwgps_id)
