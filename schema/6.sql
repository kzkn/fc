# -- !Ups

CREATE TABLE GuestEntry (
  id INTEGER PRIMARY KEY,
  name VARCHAR(20) NOT NULL,
  schedule_id INTEGER NOT NULL,
  inviter_id INTEGER NOT NULL DEFAULT -1,
  comment VARCHAR(512) NOT NULL,
  when_ TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (inviter_id) REFERENCES User(id) ON DELETE SET DEFAULT,
  FOREIGN KEY (schedule_id) REFERENCES Schedule(id) ON DELETE CASCADE
);

# -- !Downs

DROP TABLE GuestEntry;
