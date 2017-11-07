#!/usr/bin/env python3

"""
Walk one or more TNDS timetable files and emit all its
VehicleJourneys as CSV
"""
import os
import sys
import xml.etree.ElementTree as ET
import csv
import txc_helper
import csv
import psycopg2
import datetime


day = datetime.date(2017, 10, 27)

ns = {'n': 'http://www.transxchange.org.uk/'}

csv_writer = csv.writer(sys.stdout)

conn = psycopg2.connect("dbname='icp' host='localhost'")
cur = conn.cursor()
query = "select Latitude, Longitude from naptan where ATCOCode = %s"

def update_bbox(box, lat, lng):
    if box[0] is None or lat < box[0]:
        box[0] = lat
    if box[1] is None or lng < box[1]:
        box[1] = lng
    if box[2] is None or lat > box[2]:
        box[2] = lat
    if box[3] is None or lng > box[3]:
        box[3] = lng

def process(filename, region, file):
  """ Process one TNDS data file """

  tree = ET.parse(filename).getroot()

  basename = os.path.splitext(os.path.basename(filename))[0]

  # Counting on there being only one Service, Line and Operator
  # in each file...
  service = tree.find('n:Services/n:Service', ns)

  # Check the service start/end dates; bail out if out of range
  service_start = service.find('n:OperatingPeriod/n:StartDate', ns).text
  service_start_date = datetime.datetime.strptime(service_start, "%Y-%m-%d").date()
  service_end_element = service.find('n:OperatingPeriod/n:EndDate', ns)
  if service_end_element is not None:
    service_end = service_end_element.text
    service_end_date = datetime.datetime.strptime(service_end, "%Y-%m-%d").date()
  else:
    service_end = ''
    service_end_date = None

  if day >= service_start_date and (service_end_date is None or day <= service_end_date):

    service_code = service.find('n:ServiceCode', ns).text
    service_description = service.find('n:Description', ns).text
    line_name = service.find('n:Lines/n:Line/n:LineName', ns).text

    service_op_element = service.find('n:OperatingProfile', ns)
    service_op = txc_helper.OperatingProfile.from_et(service_op_element)

    operator = tree.find('n:Operators/n:Operator', ns)
    operator_code = operator.find('n:OperatorCode', ns).text

    # For each vehicle journey...
    for journey in tree.findall('n:VehicleJourneys/n:VehicleJourney', ns):

      journey_op_element = journey.find('n:OperatingProfile', ns)
      journey_op = txc_helper.OperatingProfile.from_et(journey_op_element)
      journey_op.defaults_from(service_op)

      # If this VehicleJourney applies...
      if journey_op.should_show(day):
 
        journey_code = journey.find('n:VehicleJourneyCode', ns).text
        departure_time = journey.find('n:DepartureTime', ns).text
        journey_pattern_ref = journey.find('n:JourneyPatternRef', ns).text

        # Find corresponding JoureyPattern and JourneyPatternSection
        journey_pattern_section_ref = tree.find("n:Services/n:Service/n:StandardService/n:JourneyPattern[@id='%s']/n:JourneyPatternSectionRefs" % journey_pattern_ref, ns).text
        journey_pattern_section = tree.find("n:JourneyPatternSections/n:JourneyPatternSection[@id='%s']" % journey_pattern_section_ref, ns)

        # Get first and last stop
        fr = journey_pattern_section.find("n:JourneyPatternTimingLink[1]/n:From/n:StopPointRef", ns).text
        to = journey_pattern_section.find("n:JourneyPatternTimingLink[last()]/n:To/n:StopPointRef", ns).text

        # Find the bounding box for the journey - all the from references first
        bbox = [None, None, None, None]
        for stop_point_ref in journey_pattern_section.findall("n:JourneyPatternTimingLink/n:From/n:StopPointRef", ns):
            stop_point = stop_point_ref.text
            cur.execute(query, (stop_point,))
            row = cur.fetchone()
            if row:
                update_bbox(bbox, row[0], row[1])
            else:
                print('Failed to locate %s' % stop_point, file=sys.stderr)
        # And then the 'To' of the last one
        cur.execute(query, (to,))
        row = cur.fetchone()
        if row:
            update_bbox(bbox, row[0], row[1])
        else:
            print('Failed to locate %s' % to, file=sys.stderr)


        csv_writer.writerow((
          region,
          file,
          day,
          departure_time,
          fr,
          to,
          service_code,
          service_description,
          service_start,
          service_end,
          line_name,
          operator_code,
          journey_code,
          '( %f, %f ), ( %f, %f )' % tuple(bbox)
          ))


if __name__ == '__main__':
  directory = sys.argv[1]
  for region in 'EA', 'EM', 'SE':
    directory = os.path.join(sys.argv[1], region)
    for file in os.listdir(os.fsencode(directory)):
      filename = os.path.join(directory, os.fsdecode(file))
      print('Processing %s' % filename, file=sys.stderr)
      process(filename, region, os.fsdecode(file))
