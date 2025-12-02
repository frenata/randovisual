alter table route drop constraint route_pkey;
alter table route add primary key (rusa_id, category);

alter table ride drop constraint ride_pkey;
alter table ride add column category text;
alter table ride add primary key (rusa_id, duration, date, rider_id, category);
