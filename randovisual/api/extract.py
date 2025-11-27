from fastapi import Depends, APIRouter
import randovisual.extraction.rusa as rusa
from randovisual.db.member import Member, Ride, Route
from randovisual.api.db import get_db
import sqlalchemy as sql
import sqlalchemy.dialects.postgresql as psql

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
    rider = rusa.Member(rid, "", 2000)
    # breakpoint()
    rides = rusa.find_rider_results(rider)
    if rides is not None:
        stmt = psql.insert(Ride).values(list(vars(ride) for ride in rides))
        stmt = stmt.on_conflict_do_nothing( index_elements=['rusa_id', "date", "duration", "rider_id"])
        db.execute(stmt)

    for ride in rides:
        route = rusa.get_route_info(ride.rusa_id)
        stmt = psql.insert(Route).values(route)
        stmt = stmt.on_conflict_do_nothing( index_elements=['rusa_id'])
        db.execute(stmt)

    return len(rides)


@router.get("/rusa/route/{rid}")
async def extract_route(rid: int, db=Depends(get_db)):
    # breakpoint()
    route = rusa.get_route_info(rid)
    if route is not None:
        stmt = psql.insert(Route).values(route)
        # stmt = stmt.on_conflict_do_nothing( index_elements=['rusa_id', "date", "duration", "rider_id"])
        db.execute(stmt)
        return True
