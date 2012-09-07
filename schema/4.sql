# -- !Ups

UPDATE User
   SET profile = '{"email": "", "home": "", "car": "", "comment": ""}';

# -- !Downs

UPDATE User
   SET profile = '';
