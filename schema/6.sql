# -- !Ups

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

# -- !Downs

DROP TABLE JoinRequest;

