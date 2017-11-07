SIRI <--> TNDS Timetable matching
================================

2017-11-07

Import the timetable for a particular day (encoded in the source,
currently 2017-10-27):

```
PYTHONPATH=../operating_profile/ ./timetable_journey_extractor.py
../TNDS_bus_data/sections/ | pgloader timetable_journeys.load
```

(script currently extracts EA+EM+SE regions only)

Load siri-vm.json data for 2017-10-27:

```
./sirivm_journey_extractor.py
../siri/sirivm_json/data_bin/2017/10/27/ | pgloader sirivm_journeys.load
```

Looking at data for Friday 27 October 2017

Timetable
---------

Using TNDS data for EA+EM+SE Extracted 106505 timetabled journeys.

```
select count(*) from timetable_journeys;
```

Of these there are 564 groups of journeys with the same departure time,
origin and destination, and 2097 groups with the same departure time and
origin.

```
select count(*) from (select 1 from timetable_journeys group by
departure_time, origin, destination having count(*) > 1) as x;

select count(*) from (select 1 from timetable_journeys group by
departure_time, origin having count(*) > 1) as x;
```

Many of these appear to be actually duplicated journeys, either within
Service/Line (and so TNDS file), or split across Service/Lines (files).

Journeys
--------

6199 distinct SIRI VM journeys based on departure time, origin and
destination.

```
select count(*) from sirivm_journeys;
```

These contains 6152 distinct SIRI VM journeys based on departure time
and origin only, meaning there are 47 duplicate journeys on this basis.

```
select count(*) from (select distinct departure_time, origin from
sirivm_journeys) as x; 
```

Joining on departure time, origin and destination
-------------------------------------------------

Joining SIRI journeys on Timetable journeys by departure time, origin
and destination gives 6202 rows 

```
select count(*) from sirivm_journeys as s left join
timetable_journeys as t on s.departure_time = t.departure_time and
s.origin = t.origin and s.destination = t.destination; 
```

of which 5758 (93%) matched a timetable entry and 444 (7%) didn't.

``` 
select count(*) from sirivm_journeys as s left join
timetable_journeys as t on s.departure_time = t.departure_time and
s.origin = t.origin and s.destination = t.destination where t.day is not
null;

select count(*) from sirivm_journeys as s left join timetable_journeys
as t on s.departure_time = t.departure_time and s.origin = t.origin and
s.destination = t.destination where t.day is null; 
```

6199 journeys of which 444 didn't match leaves 5755 that did. 5758
matched rows for 5755 journeys means we got three extra records as a
result of duplication. In this case this was as a result of three
records each of which were duplicated once, presumably as a result of
matching duplicate timetable records.

``` 
select s.departure_time, s.origin, s.destination, count(*) from
sirivm_journeys as s left join timetable_journeys as t on
s.departure_time = t.departure_time and s.origin = t.origin and
s.destination = t.destination group by s.departure_time, s.origin,
s.destination having count(*) > 1;

select t.*, no.description, nd.description from sirivm_journeys as s
left join timetable_journeys as t on s.departure_time = t.departure_time
and s.origin = t.origin and s.destination = t.destination inner join
(select s.departure_time, s.origin, s.destination from sirivm_journeys
as s left join timetable_journeys as t on s.departure_time =
t.departure_time and s.origin = t.origin and s.destination =
t.destination group by s.departure_time, s.origin, s.destination having
count(*) > 1) as x on s.departure_time = x.departure_time and s.origin =
x.origin and s.destination = x.destination left join naptanplus as no on
s.origin = no.atcocode left join naptanplus as nd on s.destination =
nd.atcocode; 
```

Investigating the ones that didn't match:

``` 
select s.*, no.description, nd.description from sirivm_journeys as s
left join timetable_journeys as t on s.departure_time = t.departure_time
and s.origin = t.origin and s.destination = t.destination left join
naptanplus as no on s.origin = no.atcocode left join naptanplus as nd on
s.destination = nd.atcocode where t.day is null order by
s.operator_code, s.line_name; 
```

* Three journeys on SCCM/A|The Busway from St Ives Bus Station to
Somersham 17:30, 18:21 and 18:46. Exist in the timetable, but with a
different destination stop.
* Four journeys on SCCM/5|City from Bar Hill to Drummer Street 21:43,
22:43, 19:43, 20:43. 20:43. Exist in the timetable, but with a
different destination stop (0500CCITY484 Stop D3, not 0500CCITY490
Stop E4)
* One journey on SCCM/X13 from Drummer St to Haverhill Bus Station
15:50. Not in timetable, but there is a service departing 15:40.
* 11 (all) journeys SCCM/Tour. Service not in timetable.
* 10 (all) journeys on WP/75 between Orwell/Wrestlingworth and City
Centre. All in timetable but a) with different City Centre stop
(0500CCITY121 Drummer Street Bay 5 not 0500CCITY490 Emmanuel Street E4),
and b) slightly different departure times for the journeys into
Cambridge.

Joining on departure time and origin only
-----------------------------------------

Joining SIRI journeys on Timetable journeys by departure time and
origin (but NOT and destination) gives 6331 rows

``` 
select count(*) from sirivm_journeys as s left join
timetable_journeys as t on s.departure_time = t.departure_time and
s.origin = t.origin; 
```

of which 6122 (97%) matched a timetable entry and 209 (3%) didn't.

``` 
select count(*) from sirivm_journeys as s left join
timetable_journeys as t on s.departure_time = t.departure_time and
s.origin = t.origin where t.day is not null;

select count(*) from sirivm_journeys as s left join timetable_journeys
as t on s.departure_time = t.departure_time and s.origin = t.origin
where t.day is null; 
```

6199 journeys of which 209 didn't match leaves 5990 that did. 6122
matched rows for 5990 journeys means we got 132 extra records as a
result of duplication (36 duplicates, 1 triple, 47 quad). These are the
result of a combination of duplicated vehicle journeys and duplicated
timetabled journeys (and in some cases their cross product).

``` 
select s.departure_time, s.origin, count(*) from sirivm_journeys as
s left join timetable_journeys as t on s.departure_time =
t.departure_time and s.origin = t.origin group by s.departure_time,
s.origin having count(*) > 1;

select t.*, no.description, nd.description from sirivm_journeys as s
left join timetable_journeys as t on s.departure_time = t.departure_time
and s.origin = t.origin inner join (select s.departure_time, s.origin
from sirivm_journeys as s left join timetable_journeys as t on
s.departure_time = t.departure_time and s.origin = t.origin group by
s.departure_time, s.origin having count(*) > 1) as x on s.departure_time
= x.departure_time and s.origin = x.origin left join naptanplus as no on
s.origin = no.atcocode left join naptanplus as nd on s.destination =
nd.atcocode order by t.departure_time, t.origin;
```

Investigating those that didn't match:

``` 
select s.*, no.description, nd.description from sirivm_journeys as s
left join timetable_journeys as t on s.departure_time = t.departure_time
and s.origin = t.origin left join naptanplus as no on s.origin =
no.atcocode left join naptanplus as nd on s.destination = nd.atcocode
where t.day is null order by s.operator_code, s.line_name; 
```

We get all those above that didn't depend on details of the destination
stop:

* One journey on SCCM/X13 from Drummer St to Haverhill Bus Station
15:50. Not in timetable, but there is a service departing 15:40.
* 11 (all) journeys SCCM/Tour. Service not in timetable.
* 5 journeys on WP/75 between Orwell/Wrestlingworth and City
Centre. All in timetable but with different City Centre stop
(0500CCITY121 Drummer Street Bay 5 not 0500CCITY490 Emmanuel Street E4).

Misc observations
-----------------

Observed that Operator and Line in the SIRI data don't really match
Operator and Line in the  TNDS timetable data. The SIRI ones, while
apparently based on the TNDS ones, look to be largely made up.

Also observed that TNDS line name isn't unique - e.g. '1|City' used by
both SCCM and SCPB. Worst offender is '1' which is used by 34 different
operators.
