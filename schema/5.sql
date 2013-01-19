# -- !Ups

ALTER TABLE Tax RENAME TO TaxOld;
ALTER TABLE TaxPaymentHistory RENAME TO TaxPaymentHistoryOld;

CREATE TABLE Tax (
  user_id INTEGER NOT NULL,
  year INTEGER NOT NULL,
  season INTEGER NOT NULL,
  PRIMARY KEY (user_id, year, season),
  FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE,
  CHECK (season > 0)
);

CREATE TABLE TaxPaymentHistory (
  user_id INTEGER NOT NULL,
  year INTEGER NOT NULL,
  season INTEGER NOT NULL,
  action INTEGER NOT NULL,
  updater_user_id INTEGER NOT NULL,
  when_ TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES User(id),
  FOREIGN KEY (updater_user_id) REFERENCES User(id),
  CHECK (season > 0),
  CHECK (action IN (1, 2)) /* 1: x -> o, 2: o -> x */
);

CREATE TABLE Months (month INTEGER NOT NULL);
INSERT INTO Months VALUES (1);
INSERT INTO Months VALUES (2);
INSERT INTO Months VALUES (3);
INSERT INTO Months VALUES (4);
INSERT INTO Months VALUES (5);
INSERT INTO Months VALUES (6);
INSERT INTO Months VALUES (7);
INSERT INTO Months VALUES (8);
INSERT INTO Months VALUES (9);
INSERT INTO Months VALUES (10);
INSERT INTO Months VALUES (11);
INSERT INTO Months VALUES (12);

INSERT INTO Tax
     SELECT TaxOld.user_id AS user_id,
            TaxOld.year AS year,
            Months.month AS season
       FROM TaxOld, Months
      WHERE TaxOld.paid_first = 1
        AND Months.month <= 6
     UNION 
     SELECT TaxOld.user_id AS user_id,
            TaxOld.year AS year,
            Months.month AS season
       FROM TaxOld, Months
      WHERE TaxOld.paid_second = 1
        AND Months.month > 6;

INSERT INTO TaxPaymentHistory
     SELECT TaxPaymentHistoryOld.user_id AS user_id,
            TaxPaymentHistoryOld.year AS year,
            Months.month AS season,
            TaxPaymentHistoryOld.action AS action,
            TaxPaymentHistoryOld.updater_user_id AS updater_user_id,
            TaxPaymentHistoryOld.when_ AS when_
       FROM TaxPaymentHistoryOld, Months
      WHERE TaxPaymentHistoryOld.season = 1
        AND Months.month <= 6
     UNION
     SELECT TaxPaymentHistoryOld.user_id AS user_id,
            TaxPaymentHistoryOld.year AS year,
            Months.month AS season,
            TaxPaymentHistoryOld.action AS action,
            TaxPaymentHistoryOld.updater_user_id AS updater_user_id,
            TaxPaymentHistoryOld.when_ AS when_
       FROM TaxPaymentHistoryOld, Months
      WHERE TaxPaymentHistoryOld.season = 2
        AND Months.month > 6;

DROP TABLE Months;
DROP TABLE TaxOld;
DROP TABLE TaxPaymentHistoryOld;

# -- !Downs

ALTER TABLE Tax RENAME TO TaxNew;
ALTER TABLE TaxPaymentHistory RENAME TO TaxPaymentHistoryNew;

CREATE TABLE Tax (
  user_id INTEGER NOT NULL,
  year INTEGER NOT NULL,
  paid_first BOOLEAN NOT NULL,
  paid_second BOOLEAN NOT NULL,
  PRIMARY KEY (user_id, year),
  FOREIGN KEY (user_id) REFERENCES User(id) ON DELETE CASCADE
);

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

CREATE TABLE Years (year INTEGER NOT NULL);
INSERT INTO Years VALUES (2012);
INSERT INTO Years VALUES (2013);

INSERT INTO Tax
     SELECT User.user_id AS user_id,
            Years.year AS year,
            (SELECT CASE WHEN COUNT(*) > 0 THEN 1
                    ELSE 0 END
               FROM TaxNew
              WHERE TaxNew.user_id = User.id
                AND TaxNew.year = Years.year
                AND season <= 6) AS paid_first,
            (SELECT CASE WHEN COUNT(*) > 0 THEN 1
                    ELSE 0 END
               FROM TaxNew
              WHERE TaxNew.user_id = User.id
                AND TaxNew.year = Years.year
                AND season > 6) AS paid_second
       FROM User, Years
      WHERE User.id <> -1;

INSERT INTO TaxPaymentHistory
     SELECT TaxPaymentHistoryNew.user_id AS user_id,
            TaxPaymentHistoryNew.year AS year,
            (CASE WHEN TaxPaymentHistoryNew.season <= 6 THEN 1
                  ELSE 2 END) AS season,
            TaxPaymentHistoryNew.action AS action,
            TaxPaymentHistoryNew.updater_user_id AS updater_user_id,
            TaxPaymentHistoryNew.when_ AS when_
       FROM TaxPaymentHistoryNew
   GROUP BY user_id, year, season;

DROP TABLE Years;
DROP TABLE TaxNew;
DROP TABLE TaxPaymentHistoryNew;
