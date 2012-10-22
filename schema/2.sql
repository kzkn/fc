# -- !Ups

CREATE TABLE Report (
  id INTEGER PRIMARY KEY,
  when_ TIMESTAMP NOT NULL,
  author_id INTEGER NOT NULL DEFAULT -1,
  title VARCHAR(50) NOT NULL,
  feature_image_url VARCHAR(3000) NOT NULL DEFAULT '',
  description CLOB NOT NULL,
  description_html CLOB NOT NULL,
  body CLOB NOT NULL,
  body_html CLOB NOT NULL,
  FOREIGN KEY (author_id) REFERENCES User(id) ON DELETE SET DEFAULT
);

CREATE INDEX Report_when_index ON Report(when_);

# -- !Downs

DROP INDEX Report_when_index;
DROP TABLE Report;
