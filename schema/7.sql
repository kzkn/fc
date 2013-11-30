# -- !Ups

CREATE VIEW ScheduleEntryCount AS
     SELECT Schedule.id AS schedule_id,
            ((SELECT COUNT(*) FROM Entry WHERE schedule_id =  Schedule.id AND is_entry)
             +
             (SELECT COUNT(*) FROM GuestEntry WHERE schedule_id =  Schedule.id)) AS entry_count,
            (SELECT COUNT(*) FROM Entry WHERE schedule_id =  Schedule.id AND NOT is_entry) AS not_entry_count
       FROM Schedule;

# -- !Downs

DROP VIEW ScheduleEntryCount;
