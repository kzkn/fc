# -- !Ups

-- add column `when_'
ALTER TABLE Entry RENAME TO TEMP;
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
INSERT INTO Entry (user_id, schedule_id, is_entry, comment)
     SELECT user_id, schedule_id, is_entry, comment FROM TEMP;
DROP TABLE TEMP;

# -- !Downs

-- remove column `when_'
DROP INDEX IF EXISTS Entry_when_index;
ALTER TABLE Entry RENAME TO TEMP;
CREATE TABLE Entry (
  user_id INTEGER,
  schedule_id INTEGER,
  is_entry BOOLEAN NOT NULL,
  comment VARCHAR(512) NOT NULL,
  PRIMARY KEY (user_id, schedule_id),
  FOREIGN KEY (user_id) REFERENCES User(id),
  FOREIGN KEY (schedule_id) REFERENCES Schedule(id)
);
INSERT INTO Entry (user_id, schedule_id, is_entry, comment)
     SELECT user_id, schedule_id, is_entry, comment FROM TEMP;
DROP TABLE TEMP;
