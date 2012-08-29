# -- !Ups

CREATE TABLE User (
  id INTEGER PRIMARY KEY,
  name VARCHAR(20) UNIQUE NOT NULL,
  password VARCHAR(10) UNIQUE NOT NULL,
  sex INTEGER NOT NULL,
  permission INTEGER NOT NULL DEFAULT 0,
  profile CLOB NOT NULL DEFAULT '{}', /* JSON */
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
  PRIMARY KEY (user_id, schedule_id),
  FOREIGN KEY (user_id) REFERENCES User(id),
  FOREIGN KEY (schedule_id) REFERENCES Schedule(id)
);


# -- !Downs

DROP TABLE User;
DROP TABLE Schedule;
DROP TABLE Entry;
DROP INDEX Schedule_when_index;
