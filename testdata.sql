INSERT INTO User (name, password) VALUES ('foo', '123456');

INSERT INTO Schedule (type, when_, body) VALUES (
  1, '2013-07-29 01:00:00',
  '{"loc": "ほげほげ", "court": "5", "end": "03:00",
    "no": "123456789", "price": "2400", "note": ""}');

INSERT INTO Schedule (type, when_, body) VALUES (
  2, '2013-07-29 08:15:00',
  '{"name": "ぴよぴよ杯", "loc": "ふがふが", "genre": "男ダブルス A",
    "deadline": "2012/07/28", "price": "2500", "begin_acceptance": "08:15",
    "begin_game": "09:00", "note": ""}');

INSERT INTO Schedule (type, when_, body) VALUES (
  2, '2013-08-15 08:15:00',
  '{"name": "ぶよぶよ杯", "loc": "どっか", "genre": "男ダブルス A",
    "deadline": "2012/07/28", "price": "2500", "begin_acceptance": "08:15",
    "begin_game": "09:00", "note": "90kg 以上限定"}');

INSERT INTO Schedule (type, when_, body) VALUES (
  3, '2013-07-30 19:00:00',
  '{"name": "はなきん", "loc": "飲み屋", "description": "飲むぜぇー",
    "deadline": "2012/07/28", "price": "2500"}');

