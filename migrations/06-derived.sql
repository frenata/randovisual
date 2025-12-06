alter table route 
add column distance numeric
generated always as (round(st_length(st_transform(geometry,5070)) / 1000.0)) stored
