create table if not exists rusa_member 
(id int primary key, names text[], years int[]);

create table if not exists ride (
	id int,
	date date,
	duration int,
	rider_id int,
	primary key (id, date, duration)
);
