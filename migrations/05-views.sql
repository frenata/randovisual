create or replace view records as (
with records as
 (select any_value(distance) as dist
       , round(min(ride.duration)/ 60.0,1) as fkt
       , count(1) as num_rides
       , count(distinct rider_id) as num_riders
       , route.rusa_id
       , route.category
       , any_value(name) as name
       , any_value(climbing) as climbing
  from route join ride on ride.rusa_id = route.rusa_id and ride.category = route.category
  group by route.rusa_id, route.category)
  select * from records
  order by num_riders desc, num_rides desc
);

create or replace view rides_geojson as (
SELECT jsonb_build_object(
  'type', 'Feature',
  'id', route.rusa_id,
  'geometry', ST_AsGeoJSON(route.geometry)::jsonb,
  'properties', jsonb_build_object(
    'ID', route.rusa_id,
    'Name', route.name,
    'Climbing', route.climbing || ' m',
    'Distance', route.distance || ' km',
    'Distinct Rides', COUNT(*),
    'Distinct Riders', count(distinct rider_id),
    'Fastest Known Time', round(min(ride.duration) / 60.0, 1) || ' hours',
    'Distinct Years', jsonb_agg(distinct date_part('year', date))
  )
) as route
FROM route
JOIN ride ON route.rusa_id = ride.rusa_id 
  AND route.category = ride.category
GROUP BY route.rusa_id, route.geometry, route.name, route.climbing)
