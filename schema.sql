DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS Schedule;
DROP TABLE IF EXISTS Entry;

CREATE TABLE User (
  id INTEGER PRIMARY KEY,
  name VARCHAR(20) UNIQUE NOT NULL,
  password VARCHAR(10) UNIQUE NOT NULL,
  profile CLOB NOT NULL DEFAULT '{}' /* JSON */
);

CREATE TABLE Schedule (
  id INTEGER PRIMARY KEY,
  type INTEGER NOT NULL,
  when_ TIMESTAMP NOT NULL,
  body CLOB NOT NULL DEFAULT '{}', /* JSON */
  CHECK (type IN (1, 2, 3, 9)) /* 1:renshu, 2:shiai, 3:event, 9:other */
);

CREATE TABLE Entry (
  user_id INTEGER,
  schedule_id INTEGER,
  is_entry BOOLEAN NOT NULL,
  PRIMARY KEY (user_id, schedule_id)
);