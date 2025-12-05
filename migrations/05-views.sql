create or replace view records as (
with records as
 (select any_value(round(st_length(st_transform(route.geometry, 5070))/1000.0)) as dist
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
  'geometry', ST_AsGeoJSON(route.geometry)::jsonb,
  'properties', jsonb_build_object(
    'rusa_id', route.rusa_id,
    'name', route.name,
    'climbing', route.climbing,
    'distance', round(st_length(st_transform(route.geometry, 5070)) / 1000.0),
    'ride_count', COUNT(*),
    'rider_count', count(distinct rider_id),
    'fkt', round(min(ride.duration) / 60.0, 1),
    'years', jsonb_agg(distinct date_part('year', date))
  )
)
FROM route
JOIN ride ON route.rusa_id = ride.rusa_id 
  AND route.category = ride.category
GROUP BY route.rusa_id, route.geometry, route.name, route.climbing)
