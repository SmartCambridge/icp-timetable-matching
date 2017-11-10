#!/usr/bin/env python3

import psycopg2
import psycopg2.extensions
import re


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


# Run the query

conn = psycopg2.connect("dbname='icp' host='localhost'")
cur = conn.cursor()

query = 'select boxes from psycopg2_test'
cur.execute(query)

for row in cur.fetchall():
    print(repr(row))
