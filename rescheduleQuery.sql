select * from (
  select classes.cid, day,startTime,endTime,grade,classDate,dups from classes,(
    select * from (
        select cid, classDate, count(cid) as dups
        from schedule
        group by cid,classDate
    ) as counting
    where counting.dups<=3
  ) as minCount
  where classes.cid=minCount.cid
 ) as finalShortlist
 where grade=12 and classDate>=NOW()-INTERVAL 1 WEEK
 and classDate<=NOW()+INTERVAL 1 WEEK
 order by classDate;

 select * from (select classes.cid, day,startTime,endTime,grade,classDate,dups from classes,(select * from (select cid, classDate, count(cid) as dups from schedule group by cid,classDate) as counting where counting.dups=2) as minCount where classes.cid=minCount.cid) as finalShortlist where grade=12;

