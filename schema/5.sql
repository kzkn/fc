# -- !Ups

CREATE TABLE Notice (
  id INTEGER PRIMARY KEY,
  title VARCHAR(60) NOT NULL,
  body CLOB NOT NULL,
  begin_show DATE NOT NULL,
  end_show DATE NOT NULL,
  CHECK (begin_show <= end_show)
);

CREATE INDEX Notice_time_index ON Notice(begin_show, end_show);

# -- !Downs

DROP INDEX Notice_time_index;
DROP TABLE Notice;
