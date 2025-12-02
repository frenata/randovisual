import functools
from fastapi import Depends, APIRouter
import randovisual.extraction.rusa as rusa
from randovisual.db.member import Member, Ride, Route
from randovisual.api.db import get_db
import sqlalchemy as sql
import sqlalchemy.dialects.postgresql as psql
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/extract")

@router.get("/rusa/year/{year}")
async def extract_year(year: int, db=Depends(get_db)) -> int:
    members = rusa.find_rusa_members(year)
    stmt = psql.insert(Member).values(list(vars(member) for member in members.values()))
    stmt = stmt.on_conflict_do_update(
        index_elements=['id'],
        set_={
            'names': sql.text('ARRAY(SELECT DISTINCT UNNEST(array_cat(rusa_member.names, EXCLUDED.names)))'),
            'years': sql.text('ARRAY(SELECT DISTINCT UNNEST(array_cat(rusa_member.years, EXCLUDED.years)))')
        }
    )
    db.execute(stmt)
    return len(members)


@router.get("/rusa/rider/{rid}")
async def extract_rides(rid: int, db=Depends(get_db)) -> int:
    # TODO: handle gracefully whether the rider doesn't exist? 
    # should probably just go fetch them
    rider = rusa.Member(rid, "", 2000)
    # breakpoint()
    rides = rusa.find_rider_results(rider)
    # breakpoint()
    if rides:
        rides_no_category = [{k:v for k,v in vars(ride).items() if k not in ["category", "name"]} for ride in rides]
        stmt = psql.insert(Ride).values(rides_no_category)
        stmt = stmt.on_conflict_do_nothing( index_elements=['rusa_id', "date", "duration", "rider_id"])
        db.execute(stmt)

    count = 0
    for ride in rides:
        extracted = _extract_route(ride.rusa_id, ride.name, ride.category, force=False, db=db)
        if extracted:
            count += 1

    return count


def _extract_route(rid: int, name: str | None = None, category: str | None = None, *, force: bool, db):
    route_ = db.execute(sql.select(Route).where(Route.rusa_id == rid)).one_or_none()
    if route_ is not None and force is False:
        logger.warn("already have route, skipping")
        return False
    elif route_ is not None and force is True:
        logger.info("already have route, enriching")
        route = rusa.get_route_info(rid, name, category, route_)
        stmt = psql.insert(Route).values(route)
        route.pop("rusa_id")
        stmt = stmt.on_conflict_do_update( index_elements = ["rusa_id"], set_=route)
        db.execute(stmt)
        return True
    else:
        route = rusa.get_route_info(rid, name, category)
        if route is not None:
            stmt = psql.insert(Route).values(route)
            db.execute(stmt)
            return True


@router.get("/rusa/route/{rid}")
async def extract_route(rid: int, force: bool=False, db=Depends(get_db)):
    return _extract_route(rid, force=force, db=db)
