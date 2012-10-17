# -- !Ups

CREATE TABLE User (
  id INTEGER PRIMARY KEY,
  name VARCHAR(20) UNIQUE NOT NULL,
  password VARCHAR(10) UNIQUE NOT NULL,
  sex INTEGER NOT NULL,
  permission INTEGER NOT NULL DEFAULT 0,
  profile CLOB NOT NULL DEFAULT '{"email": "", "home": "", "car": "", "comment": ""}', /* JSON */
  CHECK (sex in (1, 2)) /* 1: male, 2: female */
);

CREATE TABLE Schedule (
  id INTEGER PRIMARY KEY,
  type INTEGER NOT NULL,
  when_ TIMESTAMP NOT NULL,
  body CLOB NOT NULL DEFAULT '{}', /* JSON */
  CHECK (type IN (1, 2, 3, 9)) /* 1:renshu, 2:shiai, 3:event, 9:other */
);

CREATE INDEX Schedule_when_index ON Schedule(when_);

CREATE TABLE Entry (
  user_id INTEGER,
  schedule_id INTEGER,
  is_entry BOOLEAN NOT NULL,
  comment VARCHAR(512) NOT NULL,
  when_ TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id, schedule_id),
  FOREIGN KEY (user_id) REFERENCES User(id),
  FOREIGN KEY (schedule_id) REFERENCES Schedule(id)
);

CREATE INDEX Entry_when_index ON Entry(when_);

CREATE TABLE BBS (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  when_ TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  body CLOB NOT NULL,
  FOREIGN KEY (user_id) REFERENCES User(id)
);

CREATE INDEX BBS_when_index ON BBS(when_);

CREATE TABLE MobileSession(
  user_id INTEGER PRIMARY KEY,
  session_id CHAR(6) NOT NULL UNIQUE,
  expire TIMPSTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES User(id)
);

CREATE TABLE Notice (
  id INTEGER PRIMARY KEY,
  title VARCHAR(60) NOT NULL,
  body CLOB NOT NULL,
  begin_show DATE NOT NULL,
  end_show DATE NOT NULL,
  CHECK (begin_show <= end_show)
);

CREATE INDEX Notice_time_index ON Notice(begin_show, end_show);

CREATE TABLE JoinRequest (
  id INTEGER PRIMARY KEY,
  when_ TIMESTAMP NOT NULL,
  name VARCHAR(20) NOT NULL,
  home VARCHAR(50) NOT NULL,
  email VARCHAR(50) NOT NULL,
  sex VARCHAR(5) NOT NULL,
  age VARCHAR(10) NOT NULL,
  car VARCHAR(5) NOT NULL,
  has_racket VARCHAR(5) NOT NULL,
  holiday VARCHAR(10) NOT NULL,
  experience VARCHAR(10) NOT NULL,
  comment CLOB NOT NULL,
  handled BOOLEAN NOT NULL DEFAULT 0
);

CREATE TABLE Rule (
  id INTEGER PRIMARY KEY,
  body CLOB NOT NULL
);

CREATE TABLE Tax (
  user_id INTEGER NOT NULL,
  year INTEGER NOT NULL,
  paid_first BOOLEAN NOT NULL,
  paid_second BOOLEAN NOT NULL,
  PRIMARY KEY (user_id, year),
  FOREIGN KEY (user_id) REFERENCES User(id)
);

# -- !Downs

DROP INDEX Schedule_when_index;
DROP INDEX BBS_when_index;
DROP INDEX Entry_when_index;
DROP INDEX Notice_time_index;
DROP TABLE Tax;
DROP TABLE Rule;
DROP TABLE JoinRequest;
DROP TABLE Notice;
DROP TABLE MobileSession;
DROP TABLE BBS;
DROP TABLE Entry;
DROP TABLE Schedule;
DROP TABLE User;
