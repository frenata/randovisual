import datetime
import os
import random

from geoalchemy2.functions import ST_AsText, ST_Translate
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from randovisual.db.models import Member, Ride, Route

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL_LOAD")
MULTIPLIER = 10  # How many times to multiply the routes
PERTURBATION_DEGREES = 0.01  # ~1km at equator
PERTURB_VERTICES = True  # Set to False to only translate, not perturb individual points
MAX_ROUTES_TO_PROCESS = 500
SKIP_ROUTES_TO_PROCESS = 1000


def perturb_geometry(session, geometry, perturbation_scale, perturb_vertices=True):
    """Apply translation and optionally perturb individual vertices"""
    # Get geometry as WKT
    wkt = session.scalar(select(ST_AsText(geometry)))

    # Global translation offset
    offset_x = random.uniform(-perturbation_scale, perturbation_scale)
    offset_y = random.uniform(-perturbation_scale, perturbation_scale)

    # Parse and perturb coordinates
    if wkt.startswith("LINESTRINGZ"):
        coords = wkt.replace("LINESTRINGZ(", "").replace(")", "")
        points = coords.split(",")
        perturbed_points = []

        for point in points:
            parts = point.strip().split()
            lon, lat, z = map(float, parts)

            # Apply global translation
            new_lon = lon + offset_x
            new_lat = lat + offset_y

            # Optionally add per-vertex noise
            if perturb_vertices:
                new_lon += random.uniform(
                    -perturbation_scale * 0.3, perturbation_scale * 0.3
                )
                new_lat += random.uniform(
                    -perturbation_scale * 0.3, perturbation_scale * 0.3
                )

            perturbed_points.append(f"{new_lon} {new_lat} {z}")

        new_wkt = f"LINESTRINGZ({', '.join(perturbed_points)})"
        return new_wkt

    # Fallback for other geometry types
    return session.scalar(select(ST_AsText(ST_Translate(geometry, offset_x, offset_y))))


def generate_rides_for_route(session, route, member_ids, num_rides):
    """Generate synthetic ride records for a route"""
    rides = []
    used_combos = set()

    for _ in range(num_rides):
        # Random member
        rider_id = random.choice(member_ids)

        # Random date in last 5 years
        days_ago = random.randint(0, 1825)
        ride_date = datetime.date.today() - datetime.timedelta(days=days_ago)

        # Duration based on category (rough estimates in hours)
        base_durations = {
            "200K": random.randint(6, 12),
            "300K": random.randint(10, 18),
            "400K": random.randint(14, 24),
            "600K": random.randint(24, 40),
            "1000K": random.randint(40, 75),
            "1200K": random.randint(50, 90),
        }
        duration = base_durations.get(route.category, random.randint(6, 24))

        # Ensure unique combination (composite primary key)
        combo = (route.rusa_id, duration, ride_date, rider_id, route.category)
        if combo not in used_combos:
            used_combos.add(combo)
            rides.append(
                Ride(
                    rusa_id=route.rusa_id,
                    duration=duration,
                    date=ride_date,
                    rider_id=rider_id,
                    category=route.category,
                )
            )

    return rides


def load_test_data_generation(multiplier=MULTIPLIER):
    engine = create_engine(DATABASE_URL.replace("postgresql", "postgresql+psycopg"))

    with Session(engine) as session:
        # Get all existing routes
        existing_routes = (
            session.execute(
                select(Route)
                .where(Route.geometry.is_not(None))
                .limit(MAX_ROUTES_TO_PROCESS)
                .offset(SKIP_ROUTES_TO_PROCESS)
                .order_by(Route.rusa_id)
            )
            .scalars()
            .all()
        )
        print(f"Found {len(existing_routes)} existing routes")

        # Optionally limit how many source routes to process
        if MAX_ROUTES_TO_PROCESS is not None:
            existing_routes = existing_routes[:MAX_ROUTES_TO_PROCESS]
            print(f"Processing only {len(existing_routes)} routes")

        # Get all member IDs
        member_ids = session.execute(select(Member.id)).scalars().all()
        print(f"Found {len(member_ids)} members")

        if not existing_routes or not member_ids:
            print("Need existing routes and members to generate test data")
            return

        # Find the max existing rusa_id to avoid collisions
        max_rusa_id = session.scalar(select(func.max(Route.rusa_id)))
        next_rusa_id = max_rusa_id + 1

        new_routes = []
        new_rides = []

        # For each existing route, create multiple perturbed copies
        for i, original_route in enumerate(existing_routes):
            for copy_num in range(multiplier):
                # Create perturbed geometry
                perturbed_geom_wkt = perturb_geometry(
                    session,
                    original_route.geometry,
                    PERTURBATION_DEGREES,
                    PERTURB_VERTICES,
                )

                # Create new route
                new_route = Route(
                    rusa_id=next_rusa_id,
                    rwgps_id=original_route.rwgps_id + next_rusa_id,  # Keep unique
                    geometry=f"SRID=4326;{perturbed_geom_wkt}",
                    name=f"{original_route.name} (Copy {copy_num + 1})",
                    climbing=int(
                        original_route.climbing * random.uniform(0.9, 1.1)
                    ),  # Vary climbing slightly
                    category=original_route.category,
                )
                new_routes.append(new_route)

                # Generate random number of rides for this route (0-20 rides per route)
                num_rides = random.randint(0, 20)
                rides = generate_rides_for_route(
                    session, new_route, member_ids, num_rides
                )
                new_rides.extend(rides)

                next_rusa_id += 1

            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1}/{len(existing_routes)} original routes...")

        # Bulk insert
        print(f"\nInserting {len(new_routes)} new routes...")
        session.bulk_save_objects(new_routes)

        print(f"Inserting {len(new_rides)} new rides...")
        session.bulk_save_objects(new_rides)

        session.commit()
        print("\nLoad test data generation complete!")
        print(
            f"Total routes in DB: {session.scalar(select(func.count(Route.rusa_id)))}"
        )
        print(f"Total rides in DB: {session.scalar(select(func.count(Ride.rusa_id)))}")


if __name__ == "__main__":
    load_test_data_generation()
