#!/usr/bin/env python3

'''
Given one or more directories containing SIRI-VM data in Json, spit out
all unique vehicle journies (based on Origin, Destination, and
departure time) in CSV
'''

import json
import sys
import os
import csv

'''
   "request_data": [
        {
            "Bearing": "300",
            "DataFrameRef": "1",
            "DatedVehicleJourneyRef": "119",
            "Delay": "-PT33S",
            "DestinationName": "Emmanuel St Stop E1",
            "DestinationRef": "0500CCITY487",
            "DirectionRef": "OUTBOUND",
            "InPanic": "0",
            "Latitude": "52.2051239",
            "LineRef": "7",
            "Longitude": "0.1242290",
            "Monitored": "true",
            "OperatorRef": "SCCM",
            "OriginAimedDepartureTime": "2017-10-25T23:14:00+01:00",
            "OriginName": "Park Road",
            "OriginRef": "0500SSAWS023",
            "PublishedLineName": "7",
            "RecordedAtTime": "2017-10-25T23:59:48+01:00",
            "ValidUntilTime": "2017-10-25T23:59:48+01:00",
            "VehicleMonitoringRef": "SCCM-19597",
            "VehicleRef": "SCCM-19597",
            "acp_id": "SCCM-19597",
            "acp_lat": 52.2051239,
            "acp_lng": 0.124229,
            "acp_ts": 1508972388
        },
'''

def update_bbox(box, lat, lng):
    if lat < box[0]:
        box[0] = lat
    if lng < box[1]:
        box[1] = lng
    if lat > box[2]:
        box[2] = lat
    if lng > box[3]:
        box[3] = lng


results = {}

csvwriter = csv.writer(sys.stdout)

for directory in sys.argv[1:]:

    for file in os.listdir(os.fsencode(directory)):
        filename = os.path.join(directory, os.fsdecode(file))
        if not filename.endswith(".json"):
            continue

        #print("Processing %s" % filename)

        with open(filename) as data_file:
            data = json.load(data_file)

        for record in data["request_data"]:

           time = record["OriginAimedDepartureTime"][11:19]
           key = ( record['VehicleRef'], record["OriginRef"], record["DestinationRef"], time )

           if not key in results:
               results[key] = record
               results[key]['points'] = [[record['acp_lat'], record['acp_lng']]]
               results[key]['times'] = [record['RecordedAtTime']]
               results[key]['bbox'] = [record['acp_lat'], record['acp_lng'],
                                       record['acp_lat'], record['acp_lng']]
           else:
               results[key]['points'].append([record['acp_lat'], record['acp_lng']])
               results[key]['times'].append(record['RecordedAtTime'])
               update_bbox(results[key]['bbox'], record['acp_lat'], record['acp_lng'])



for result in results.values():
    csvwriter.writerow((
        result['OriginAimedDepartureTime'][0:10],
        result['OriginAimedDepartureTime'][11:19],
        result['OriginRef'],
        result['DestinationRef'],
        result['LineRef'],
        result['OperatorRef'],
        result['VehicleRef'],
        '( %f, %f ), ( %f, %f )' % tuple(result['bbox']),
        '{ ' + ', '.join([ ' "(%f, %f)" ' % tuple(point) for point in result['points']]) + ' }',
        '{ ' + ', '.join([ ' "%s" ' % (time) for time in result['times']]) + ' }',
        ))
