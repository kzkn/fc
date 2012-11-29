# -- !Ups

CREATE TABLE TaxPaymentHistory (
  user_id INTEGER NOT NULL,
  year INTEGER NOT NULL,
  season INTEGER NOT NULL,
  action INTEGER NOT NULL,
  updater_user_id INTEGER NOT NULL,
  when_ TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id, year) REFERENCES Tax(user_id, year),
  FOREIGN KEY (updater_user_id) REFERENCES User(id),
  CHECK (season IN (1, 2)), /* 1: first, 2: second */
  CHECK (action IN (1, 2)) /* 1: x -> o, 2: o -> x */
);

CREATE INDEX TaxPaymentHistory_year_index ON TaxPaymentHistory(year);
CREATE INDEX TaxPaymentHistory_when_index ON TaxPaymentHistory(when_);

INSERT INTO TaxPaymentHistory
     SELECT Tax.user_id AS user_id,
            Tax.year AS year,
            1 AS season,
            1 AS action,
            (SELECT id FROM User WHERE permission = 15 ORDER BY id LIMIT 1) AS updater_user_id,
            CURRENT_TIMESTAMP AS when_
       FROM Tax
      WHERE Tax.paid_first = 1
     UNION
     SELECT Tax.user_id AS user_id,
            Tax.year AS year,
            2 AS season,
            1 AS action,
            (SELECT id FROM User WHERE permission = 15 ORDER BY id LIMIT 1) AS updater_user_id,
            CURRENT_TIMESTAMP AS when_
       FROM Tax
      WHERE Tax.paid_second = 1;

# -- !Downs

DROP TABLE TaxPaymentHistory;
