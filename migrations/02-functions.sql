CREATE OR REPLACE FUNCTION public.ride_routes(z integer, x integer, y integer)
RETURNS bytea AS $$
BEGIN
  
  RETURN ST_AsMVT(tile, 'routes', 4096, 'geometry')
  FROM (

with rides_per_year as 
  (select route.category, route.rusa_id, count(1), date_part('year', date)::int as year 
   from route join ride on ride.rusa_id = route.rusa_id and ride.category = route.category 
   group by route.rusa_id, route.category, date_part('year', date))
 , aggr_years as (select category, rusa_id, jsonb_object_agg(year, count) as rides_per_year from rides_per_year group by category, rusa_id)

    SELECT 
      route.rusa_id as "ID",
      any_value(route.name) as "Name",
      any_value(route.climbing) as "Climbing",
      any_value(round(st_length(st_transform(route.geometry, 5070)) / 1000.0)) as "Distance",
      COUNT(*) as "Distinct Rides",
      count(distinct rider_id) as "Distinct Riders",
      round(min(ride.duration) / 60.0, 1) as "Fastest Known Time",
      jsonb_agg(distinct date_part('year', date))::text as "Distinct Years",
      any_value(aggr_years.rides_per_year)::text as "Rides By Year",
      ST_AsMVTGeom(
        ST_Transform(geometry, 3857),
        ST_TileEnvelope(z, x, y),
        4096, 256, false
      ) AS geometry
    FROM route
    JOIN ride
	on  route.rusa_id = ride.rusa_id
	AND route.category = ride.category
    JOIN aggr_years
      ON route.rusa_id = aggr_years.rusa_id 
      AND route.category = aggr_years.category
    WHERE 1=1
      AND geometry && ST_Transform(ST_TileEnvelope(z, x, y), 4326)
    GROUP BY route.rusa_id, geometry
  ) AS tile;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;
