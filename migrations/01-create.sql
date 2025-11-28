create table if not exists rusa_member 
(id int primary key, names text[], years int[]);

create table if not exists ride (
	rusa_id int,
	date date,
	duration int,
	rider_id int references rusa_member (id),
	primary key (rusa_id, date, duration, rider_id)
);

create table if not exists route (
	rusa_id int primary key,
	rwgps_id int,
	geometry Geometry(LinestringZ, 4326)
);
