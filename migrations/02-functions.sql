CREATE OR REPLACE FUNCTION public.ride_routes(z integer, x integer, y integer)
RETURNS bytea AS $$
BEGIN
  
  RETURN ST_AsMVT(tile, 'routes', 4096, 'geometry')
  FROM (
    SELECT 
      route.rusa_id as "ID",
      any_value(route.name) as "Name",
      any_value(route.climbing) as "Climbing",
      any_value(round(st_length(st_transform(route.geometry, 5070)) / 1000.0)) as "Distance",
      COUNT(*) as "Distinct Rides",
      count(distinct rider_id) as "Distinct Riders",
      round(min(ride.duration) / 60.0, 1) as "Fastest Known Time",
      ST_AsMVTGeom(
        ST_Transform(geometry, 3857),
        ST_TileEnvelope(z, x, y),
        4096, 256, false
      ) AS geometry
    FROM route
    JOIN ride
	on  route.rusa_id = ride.rusa_id
	AND route.category = ride.category
    WHERE 1=1
      AND geometry && ST_Transform(ST_TileEnvelope(z, x, y), 4326)
    GROUP BY route.rusa_id, geometry
  ) AS tile;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;
