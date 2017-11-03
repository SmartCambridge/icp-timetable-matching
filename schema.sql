-- Schema for the timetable_journies table


CREATE TABLE IF NOT EXISTS timetable_journeys (
    region              text,
    file                text,
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

CREATE TABLE IF NOT EXISTS sirivm_journeys (
    day                 text,
    departure_time      text,
    origin              text,
    destination         text,
    line_name           text,
    operator_code       text,
    vehicle_ref         text
    );
