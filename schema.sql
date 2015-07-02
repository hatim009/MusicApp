drop table if exists Songs;
drop table if exists Users;
drop table if exists voteTable1;
drop table if exists voteTable2;
drop table if exists voteTable3;

create table Users( 
	userId integer primary key autoincrement, 
	userName text null, 
	userEmail text null, 
	userPassword text null
);

create table Songs(	
	songId integer primary key autoincrement, 
	songName text null, 
	upvotes integer default '0', 
	downvotes integer default '0', 
	userId integer null, 
	dateAdded text, 
	foreign key (userId) references Users (userId) 
); 
