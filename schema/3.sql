# -- !Ups

CREATE TABLE Saying (
  id INTEGER PRIMARY KEY,
  who VARCHAR(100) NOT NULL,
  body CLOB NOT NULL,
  private BOOLEAN NOT NULL
);

# -- !Downs

DROP TABLE Saying;
