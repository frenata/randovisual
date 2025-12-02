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
