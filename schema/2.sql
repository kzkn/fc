# -- !Ups

CREATE TABLE MobileSession(
  user_id INTEGER PRIMARY KEY,
  session_id CHAR(6) NOT NULL UNIQUE,
  expire TIMPSTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES User(id)
);

# -- !Downs

DROP TABLE MobileSession;
