# -- !Ups

CREATE TABLE Tax (
  user_id INTEGER NOT NULL,
  year INTEGER NOT NULL,
  paid_first BOOLEAN NOT NULL,
  paid_second BOOLEAN NOT NULL,
  PRIMARY KEY (user_id, year),
  FOREIGN KEY (user_id) REFERENCES User(id)
);

# -- !Downs

DROP TABLE Tax;
