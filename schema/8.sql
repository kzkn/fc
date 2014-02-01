# -- !Ups

ALTER TABLE User RENAME TO UserOld;

-- joined を追加
CREATE TABLE User (
  id INTEGER PRIMARY KEY,
  name VARCHAR(20) UNIQUE NOT NULL,
  password VARCHAR(10) UNIQUE NOT NULL,
  sex INTEGER NOT NULL,
  permission INTEGER NOT NULL DEFAULT 0,
  joined TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  profile CLOB NOT NULL DEFAULT '{"email": "", "home": "", "car": "", "comment": ""}', /* JSON */
  CHECK (sex in (1, 2)) /* 1: male, 2: female */
);

-- 既存ユーザの登録日はわからないので、Entry に登録した最初の日を joined とする
-- 一度も登録してない人は現在日時を joined とする
INSERT INTO User
     SELECT UserOld.id AS id,
            UserOld.name AS name,
            UserOld.password AS password,
            UserOld.sex AS sex,
            UserOld.permission AS permission,
            COALESCE(MIN(Entry.when_), CURRENT_TIMESTAMP) AS joined,
            UserOld.profile AS profile
       FROM UserOld
            LEFT OUTER JOIN Entry ON
              UserOld.id = Entry.user_id
   GROUP BY UserOld.id;

DROP TABLE UserOld;

# -- !Downs

ALTER TABLE User RENAME TO UserNew;

-- joined を削除
CREATE TABLE User (
  id INTEGER PRIMARY KEY,
  name VARCHAR(20) UNIQUE NOT NULL,
  password VARCHAR(10) UNIQUE NOT NULL,
  sex INTEGER NOT NULL,
  permission INTEGER NOT NULL DEFAULT 0,
  profile CLOB NOT NULL DEFAULT '{"email": "", "home": "", "car": "", "comment": ""}', /* JSON */
  CHECK (sex in (1, 2)) /* 1: male, 2: female */
);

INSERT INTO User
     SELECT UserNew.id AS id,
            UserNew.name AS name,
            UserNew.password AS password,
            UserNew.sex AS sex,
            UserNew.permission AS permission,
            UserNew.profile AS profile
       FROM UserNew;

DROP TABLE UserNew;
