#!/usr/bin/env python3

import psycopg2
import json
import re

import psycopg2.extensions

# Function to cast Postgres point representation to list
def cast_point(value, cur):
  if value is None:
    return None
  # Convert from (f1, f2) syntax using a regular expression.
  m = re.match(r"\(([^)]+),([^)]+)\)", value)
  if m:
    return (float(m.group(1)), float(m.group(2)))
  else:
    raise psycopg2.InterfaceError("bad point representation: %r" % value)

# Function to cast Postgres box representation to list
def cast_box(value, cur):
  if value is None:
    return None
  # Convert from Postgres box datatype in "(x1,y1),(x2,y2)" format into
  # [[x1,y1],[x2,y2]]
  m = re.match(r'\((.*?),(.*?)\),\((.*?),(.*?)\)', value)
  if m:
    return [[float(m.group(1)), float(m.group(2))],[float(m.group(3)), float(m.group(4))]]
  else:
    raise psycopg2.InterfaceError("bad box representation: %r" % value)

# Register function to process point and point[] columns
point = psycopg2.extensions.new_type(
      (600,), "POINT", cast_point)
points = psycopg2.extensions.new_array_type(
      (1017,), 'POINT[]', point)
psycopg2.extensions.register_type(point)
psycopg2.extensions.register_type(points)

# Dito box
box = psycopg2.extensions.new_type(
      (603,), "BOX", cast_box)
psycopg2.extensions.register_type(box)

conn = psycopg2.connect("dbname='icp' host='localhost'")
cur = conn.cursor()

query1 = '''
select
  t.operator_code,         --  0
  t.line_name,             --  1
  t.departure_time,        --  2
  t.origin,                --  3
  t.destination,           --  4
  t.journey_code,          --  5
  t.region,                --  6
  t.file,                  --  7
  s.bbox,                  --  8
  t.bbox,                  --  9
  no.description,          -- 10
  nd.description,          -- 11
  s.points,                -- 12
  t.points,                -- 13
  t.stops,                 -- 14
  t.direction,             -- 15
  s.vehicle_ref,           -- 16
  t.journey_code,          -- 17
  s.time                   -- 18
from sirivm_journeys as s
inner join timetable_journeys as t on
  s.departure_time = t.departure_time and
  s.origin = t.origin and
  s.destination = t.destination
left join naptanplus as no on
  t.origin = no.atcocode
left join naptanplus as nd on
  t.destination = nd.atcocode
where not s.bbox && t.bbox
order by t.operator_code, t.line_name, t.direction, t.departure_time;
'''

query2 = '''
select
  description
from naptanplus
where atcocode = %s;
'''

cur.execute(query1)

rows = cur.fetchall()

results = []

for row in rows:

    stoplist = []
    for stop in row[14]:
      cur.execute(query2, (stop,))
      r = cur.fetchone()
      if r:
        stoplist.append("%s: %s" % (stop, r[0]))
      else:
        stoplist.append(stop)

    item = {}
    item['operator_code'] = row[0]
    item['line_name'] = row[1]
    item['departure_time'] = row[2]
    item['origin_code'] = row[3]
    item['destination_code'] = row[4]
    item['journey_code'] = row[5]
    item['region'] = row[6]
    item['file'] = row[7]
    item['sbbox'] = row[8]
    item['tbbox'] = row[9]
    item['origin_description'] = row[10]
    item['destination_description'] = row[11]
    item['spoints'] = row[12]
    item['tpoints'] = row[13]
    item['tstops'] = stoplist
    item['direction'] = row[15]
    item['vehicle_ref'] = row[16]
    item['journey_code'] = row[17]
    item['times'] = row[18]
    results.append(item)

print('var items =')
print(json.dumps(results, indent=4))
