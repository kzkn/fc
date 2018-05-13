# -- !Ups

ALTER TABLE User RENAME TO UserOld;

-- logged_in を追加
CREATE TABLE User (
  id INTEGER PRIMARY KEY,
  name VARCHAR(20) UNIQUE NOT NULL,
  password VARCHAR(10) UNIQUE NOT NULL,
  sex INTEGER NOT NULL,
  permission INTEGER NOT NULL DEFAULT 0,
  joined TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  profile CLOB NOT NULL DEFAULT '{"email": "", "home": "", "car": "", "comment": ""}', /* JSON */
  logged_in TIMESTAMP,
  CHECK (sex in (1, 2)) /* 1: male, 2: female */
);

-- 既存ユーザの最終アクセス時刻はわからないので、Entry に登録した最後に日を joined とする
-- 一度も登録してない人は NULL とする
INSERT INTO User
     SELECT UserOld.id AS id,
            UserOld.name AS name,
            UserOld.password AS password,
            UserOld.sex AS sex,
            UserOld.permission AS permission,
            UserOld.joined AS joined,
            UserOld.profile AS profile,
            NULL as logged_in
       FROM UserOld
            LEFT OUTER JOIN Entry ON
              UserOld.id = Entry.user_id
   GROUP BY UserOld.id;

DROP TABLE UserOld;

# -- !Downs

ALTER TABLE User RENAME TO UserNew;

-- logged_in を削除
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

INSERT INTO User
     SELECT UserNew.id AS id,
            UserNew.name AS name,
            UserNew.password AS password,
            UserNew.sex AS sex,
            UserNew.permission AS permission,
            UserNew.joined AS joined,
            UserNew.profile AS profile
       FROM UserNew;

DROP TABLE UserNew;
