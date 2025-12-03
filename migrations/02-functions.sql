CREATE OR REPLACE FUNCTION public.ride_routes(z integer, x integer, y integer, year integer)
RETURNS bytea AS $$
-- DECLARE
--   year_filter integer;
BEGIN
  -- year_filter := (query_params->>'year')::integer;
  
  RETURN ST_AsMVT(tile, 'routes', 4096, 'geometry')
  FROM (
    SELECT 
      route.rusa_id,
      any_value(route.name) as name,
      any_value(route.climbing) as climbing,
      any_value(round(st_length(st_transform(route.geometry, 5070)) / 1000.0)) as distance,
      COUNT(*) as ride_count,
      count(distinct rider_id) as rider_count,
      round(min(ride.duration) / 60.0, 1) as fkt,
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
      AND CASE
        WHEN year = '9999' THEN true
        ELSE date_part('year', date)::integer = year
      END
      AND geometry && ST_Transform(ST_TileEnvelope(z, x, y), 4326)
    GROUP BY route.rusa_id, geometry
  ) AS tile;
END;
$$ LANGUAGE plpgsql STABLE PARALLEL SAFE;
