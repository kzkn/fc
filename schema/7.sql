# -- !Ups

CREATE TABLE Rule (
  id INTEGER PRIMARY KEY,
  body CLOB NOT NULL
);

# -- !Downs

DROP TABLE Rule;
