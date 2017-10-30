-- Schema for the timetable_journies table


CREATE TABLE timetable_journies (
    day                 text,
    departure_time      text,
    origin              text,
    destination         text,
    service_code        text,
    service_description text,
    service_start       text,
    service_end         text,
    line_name           text,
    operator_code       text,
    journey_code        text
    );
