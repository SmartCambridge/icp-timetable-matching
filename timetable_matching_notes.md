SIRI <--> TNDS Timetable matching
=================================

**Version 1, 2017-11-10**

Looking at data for Friday 27 October 2017

Timetable
---------

Using TNDS data for the EA, EM and SE regions. Extracted 106505 timetabled journeys for
this day.

```
select count(*) from timetable_journeys;
```

There all have unique VehicleJourneyCodes.

Of these, there are 105901 distinct journeys (604 fewer) based on
DepartureTime and first and last StopPointRef, and 104232 journeys (a
further 1,669 fewer) based on DepartureTime and first StopPointRef only,
meaning there are a significant number of duplicated journeys (i.e. more
than  one timetabled journey over the same route at the same time) on
these bases.

```
select count(*) from (select distinct departure_time, origin,
destination from timetable_journeys) as x;

select count(*) from (select distinct departure_time, origin from
timetable_journeys) as x;
```

Many of these appear to be actually duplicated journeys, either within
Service/Line (and so TNDS file), or split across Service/Lines (files).

Journeys
--------

6362 distinct SIRI VM journeys based on VehicleRef, OriginAimedDepartureTime,
OriginRef and DestinationRef.

```
select count(*) from sirivm_journeys;
```

Of these, there are 6199 distinct SIRI VM journeys (163 fewer) based on
just OriginAimedDepartureTime, OriginRef and DestinationRef, and 6152 (a
further 47 fewer) based on OriginAimedDepartureTime and OriginRef
only, meaning that there are a significant number of duplicate journeys
(i.e. more than one vehicle apparently servicing the same timetable
journey) on these bases.


```
select count(*) from (select distinct departure_time, origin,
destination from sirivm_journeys) as x;

select count(*) from (select distinct departure_time, origin from
sirivm_journeys) as x;
```

Joining on departure time, origin and destination
-------------------------------------------------

Joining SIRI journeys on Timetable journeys by departure time, origin
and destination gives 6366 rows

```
select count(*) from sirivm_journeys as s left join
timetable_journeys as t on s.departure_time = t.departure_time and
s.origin = t.origin and s.destination = t.destination;
```

of which 451 (7%) didn't match, 5907 (83%) represented SIRI-VM journeys
matching a single Timetable journey, and 8 (0%) represent  SIRI-VM
journeys matching multiple timetable journeys.

```
select c, count(*) from (select count(distinct(t.serial)) as c from
sirivm_journeys as s left join timetable_journeys as t on
s.departure_time = t.departure_time and s.origin = t.origin and
s.destination = t.destination group by s.serial) as s group by c;
```

Further, of the 5907 + 8 = 5951 rows representing a match, 5601 represent
timetable journeys matching a single SIRI-VM journey and 314 represent
timetable journeys matching multiple SIRI-VM journeys.

```
select c, count(*) from (select count(distinct(s.serial)) as c from
sirivm_journeys as s left join timetable_journeys as t on
s.departure_time = t.departure_time and s.origin = t.origin and
s.destination = t.destination group by t.serial) as s group by c;
```

The following allow multiple matches to be investigated:

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

```
select s.*, no.description, nd.description from sirivm_journeys as s
left join timetable_journeys as t on s.departure_time = t.departure_time
and s.origin = t.origin and s.destination = t.destination left join
naptanplus as no on s.origin = no.atcocode left join naptanplus as nd on
s.destination = nd.atcocode where t.day is null order by
s.operator_code, s.line_name;
```

For rows representing matches there are 110 rows where the bounding box
of the SIRI-VM journey doesn't overlap the bounding box of the matched
timetable record at all. In all cases the SIRI-VM OperatorRef and
LineName match the timetable OperatorCode and LineName (in meaning, if
not exactly, see 'Misc Observations' below). This represents buses that
that are believed to be undertaking one timetable journey while actually
following some completely different path. It is entirely possible that
there are further examples of this effect that are going unnoticed
because the bounding boxes overlap even though the SIRI and timetable
paths are still distinct.

Joining on departure time and origin only
-----------------------------------------

Joining SIRI journeys on Timetable journeys by departure time and
origin (but NOT and destination) gives 6497 rows

```
select count(*) from sirivm_journeys as s left join
timetable_journeys as t on s.departure_time = t.departure_time and
s.origin = t.origin;
```

of which 211 (7%) didn't match, 6017 (83%) represented SIRI-VM journeys
matching a single Timetable journey, and 269 (0%) represent  SIRI-VM
journeys matching multiple timetable journeys.

```
select c, count(*) from (select count(distinct(t.serial)) as c from
sirivm_journeys as s left join timetable_journeys as t on
s.departure_time = t.departure_time and s.origin = t.origin group by
s.serial) as s group by c
```

The following allow multiple matches to be investigated:

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

We get all those above that didn't depend on details of the destination
stop, but nothing obviously new:

* One journey on SCCM/X13 from Drummer St to Haverhill Bus Station
15:50. Not in timetable, but there is a service departing 15:40.
* 11 (all) journeys SCCM/Tour. Service not in timetable.
* 5 journeys on WP/75 between Orwell/Wrestlingworth and City
Centre. All in timetable but with different City Centre stop
(0500CCITY121 Drummer Street Bay 5 not 0500CCITY490 Emmanuel Street E4).

```
select s.*, no.description, nd.description from sirivm_journeys as s
left join timetable_journeys as t on s.departure_time = t.departure_time
and s.origin = t.origin left join naptanplus as no on s.origin =
no.atcocode left join naptanplus as nd on s.destination = nd.atcocode
where t.day is null order by s.operator_code, s.line_name;
```

Misc observations
-----------------

Observed that Operator and Line in the SIRI data don't really match
Operator and Line in the  TNDS timetable data. The SIRI ones, while
apparently based on the TNDS ones, look to be largely made up.

Also observed that TNDS line name isn't unique - e.g. '1|City' used by
both SCCM and SCPB. Worst offender is '1' which is used by 34 different
operators.
