select * from (
  select classes.cid, day,startTime,endTime,grade,classDate,dups from classes,(
    select * from (
        select cid, classDate, count(cid) as dups
        from schedule
        group by cid,classDate
    ) as counting
    where counting.dups=2
  ) as minCount
  where classes.cid=minCount.cid
 ) as finalShortlist
 where grade=12;

 select * from (select classes.cid, day,startTime,endTime,grade,classDate,dups from classes,(select * from (select cid, classDate, count(cid) as dups from schedule group by cid,classDate) as counting where counting.dups=2) as minCount where classes.cid=minCount.cid) as finalShortlist where grade=12;