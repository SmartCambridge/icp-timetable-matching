#!/usr/bin/env python3

import psycopg2
import json
import re

conn = psycopg2.connect("dbname='icp' host='localhost'")
cur = conn.cursor()

query = '''
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
  t.stops,                 -- 10
  no.description,          -- 11
  nd.description           -- 12
  --s.points,                -- 10
  --t.points,                -- 11
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
order by t.departure_time;
'''

def parse_box(string):
  ''''
  Parse a Postgres box datatype in "(x1,y1),(x2,y2)" format into
  [[x1,y1]m[x2,y2]]
  '''

  m = re.match(r'\((.*?),(.*?)\),\((.*?),(.*?)\)', string)
  return [[float(m.group(1)), float(m.group(2))],[float(m.group(3)), float(m.group(4))]]


cur.execute(query)

rows = cur.fetchall()

results = []

for row in rows:

    item = {}
    item['name'] = ' '.join((row[0],row[1],row[2],row[3],row[11],row[4],row[12]))
    item['sbbox'] = parse_box(row[8])
    item['tbbox'] = parse_box(row[9])
    results.append(item)

print('var items =')
print(json.dumps(results, indent=4))
