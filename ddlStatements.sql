drop table students;
drop table classes;
drop table payment;
drop table userpass;
drop table schedule;

CREATE table students (
sid int not null primary key auto_increment,
username varchar(50) not null,
name varchar(50) not null,
email varchar(100) not null,
phone char(10) not null,
hour_rate char(10) not null,
grade char(2) not null,
cid char(10) not null,
joinDate date
);

insert into students values(
1, "Troy Bolton", "wildcats@easthigh.com",
123456789, 75, 12, 2, CURRENT_DATE);

insert into students values(2,
"Gabriella Montez", "decathalon@easthigh.com",
123456789, 75, 11, 1, CURRENT_DATE);

insert into students values(3,
"Sharpay Evans", "queen@easthigh.com",
123456789, 75, 11, 1, CURRENT_DATE);

insert into students values(4,
"Ryan Evans", "drama@easthigh.com",
123456789, 75, 11, 1, CURRENT_DATE);

CREATE table classes (
cid int not null primary key auto_increment,
day varchar(10) not null,
startTime varchar(10) not null,
endTime varchar(10) not null,
grade char(2) not null
);

insert into classes values (
	1, "Monday", "2:30pm", "3:30pm", 11
);

insert into classes values (
	2, "Tuesday", "2:00pm", "3:30pm", 12
);

CREATE table payment (
payDate date not null,
sid char(10) not null,
status varchar(10)  	
);

insert into payment values(
"2017-10-05", 1, NULL);

insert into payment values (
	"2017-09-01", 2, "paid");
insert into payment values (
	"2017-09-01", 1, "paid");

CREATE table schedule(
	classDate date not null,
	cid int not null,
	sid int not null,
	status char(10) not null,

	primary key(classDate, sid),

	foreign key(cid) references classes(cid) on delete restrict,
	foreign key(sid) references students(sid) on delete restrict
);

insert into schedule values(
"2017-10-17", 2, 1, "attended");

insert into schedule values(
"2017-10-17", 2, 2, "attended");

insert into schedule values(
"2017-10-24", 2, 1, "scheduled");

insert into schedule values(
"2017-10-31", 2, 1, "scheduled");

insert into schedule values(
"2017-11-07", 2, 1, "cancelled");

insert into schedule values(
"2017-11-14", 2, 1, "cancelled");

insert into schedule values(
"2017-11-21", 2, 1, "cancelled");

insert into schedule values(
"2017-11-28", 2, 1, "cancelled");

insert into schedule values(
"2017-12-05", 2, 1, "cancelled");




create table userpass (
	username varchar(20) not null,
	hashed char(60) not null
);

insert into userpass values(
"meher", "$2b$12$br59E7nQiHJ32JAIGma1z.SOAAL9CUY.Yvg2c1oZBb/.Pt14koQJK");

insert into userpass values(
"admin", "$2b$12$tMw4B/PPKzkqc3gHS7TdNejSOaY9OHT5B1mEOH5hDopa0meGDOJS2");