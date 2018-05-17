"""
Mathangi Ganesh and Meher  ***P5 MEHER'S VERSION****
Final Project CS304
helpFunc.py
20/12/17

This contains all the helper functions separated by 6 sections:
1) Login/Verification
2) Scheduling
3) Indexing Students
4) Indexing Classes
5) Rescheduling
6) Payment

It will likely be divided into further sub-files later on...
"""

import dbconn2, MySQLdb, os, sys, bcrypt
from flask import (Flask, render_template, make_response, url_for, request, flash, redirect)
DATABASE = 'tutor_db'

def cursor(database=DATABASE):
    """Establish the connection with the database. 
    Will change in beta version so that only one connection is used throughout app."""
    DSN = dbconn2.read_cnf()
    DSN['db'] = database
    conn = dbconn2.connect(DSN) 
    return conn.cursor(MySQLdb.cursors.DictCursor)


"""Login/Verification of User Identity"""

def uniqueUsername(curs, username):
    """Check if username already exists in db.
    Returns True if username is unique, false if already exists."""
    curs.execute('SELECT username FROM userpass WHERE username = %s',(username,))
    #Returns none if username is unique, meaning curs.fetchone() is None
    return curs.fetchone() is None

def checkLogin(curs, username, password):
    """Check if login credentials are valid.
    Returns true if valid, false if invalid"""
    curs.execute('SELECT hashed FROM userpass WHERE username = %s',[username])
    row = curs.fetchone()
    if row is None: return False
    hashed = row['hashed']
    return bcrypt.hashpw(password.encode('utf-8'),hashed.encode('utf-8')) == hashed

def insertNewStudent(curs, username, passwd1, name, email, phone, cid, grade):
    """Insert new student into database. Hashes password. 
    Insert into userpass table and student table"""
    hashed = bcrypt.hashpw(passwd1.encode('utf-8'), bcrypt.gensalt())
    curs.execute('INSERT into userpass(username,hashed) VALUES(%s,%s)', [username, hashed])
    curs.execute('INSERT into students (name, email, phone, grade, cid, joinDate, username, verified) '+
                  'VALUES (%s, %s, %s, %s, %s, CURRENT_DATE, %s, 0)', #0 boolean for is unverified student
                [name, email, phone, grade, cid, username])

def getUnverified():
  """Retrieves all Unverified students from the students db.
  Students are unverified till the admin verifies them from notifications"""
  conn=cursor()
  conn.execute('SELECT name,email,phone,students.grade,students.cid,sid, ' + 
               'DATE_FORMAT(joinDate, "%m/%d/%Y") as joinDate,username,day,startTime,endTime,classes.grade as classGrade ' +
               'FROM students,classes ' +
               'WHERE verified=0 and students.cid=classes.cid')
  return conn.fetchall()

def verifyStudent(curs, sid,hour_rate):
  """Admin sets the student as verified and enters their hourly payable rate
  Only done if the admin accepts the student from notifications"""
  curs.execute('UPDATE students set verified=1, hour_rate=%s WHERE sid=%s',(hour_rate,sid,))

def denyStudent(curs, sid):
  """Admin removes the student entirely from all db
  Only done if the admin denies the student from notifications"""
  username = getStudentByID(sid)['username']
  curs.execute('DELETE FROM students where sid=%s',(sid,))
  curs.execute('DELETE FROM userpass where username=%s',(username,))

def insertSchedule(curs, cid,sid):
    """If a student is accepted, this auto-populates the schedule table with
    classes for the rest of the month for the student. """
    day = getClassbyID(cid)['day'] 
    curs.execute('insert into schedule (classDate,cid,sid,status)'+ 
                 #inserting the below data into schedule table
                 'SELECT DATE,%s,%s,"scheduled"'+ 
                    'FROM ('+
                        #calculate all dates up to 30 days from now
                        'SELECT DATE_ADD(now(), ' 
                            'INTERVAL n1.num DAY) AS DATE '+
                          'FROM  ('
                             'SELECT 0 AS num ' +
                              'UNION ALL SELECT 1 ' +
                              'UNION ALL SELECT 2 ' +
                              'UNION ALL SELECT 3 ' +
                              'UNION ALL SELECT 4 ' +
                              'UNION ALL SELECT 5 ' +
                              'UNION ALL SELECT 6 ' +
                              'UNION ALL SELECT 7 ' +
                              'UNION ALL SELECT 8 ' +
                              'UNION ALL SELECT 9 ' +
                              'UNION ALL SELECT 10 ' +
                              'UNION ALL SELECT 11 ' +
                              'UNION ALL SELECT 12 ' +
                              'UNION ALL SELECT 13 ' +
                              'UNION ALL SELECT 14 ' +
                              'UNION ALL SELECT 15 ' +
                              'UNION ALL SELECT 16 ' +
                              'UNION ALL SELECT 17 ' +
                              'UNION ALL SELECT 18 ' +
                              'UNION ALL SELECT 19 ' +
                              'UNION ALL SELECT 20 ' +
                              'UNION ALL SELECT 21 ' +
                              'UNION ALL SELECT 22 ' +
                              'UNION ALL SELECT 23 ' +
                              'UNION ALL SELECT 24 ' +
                              'UNION ALL SELECT 25 ' +
                              'UNION ALL SELECT 26 ' +
                              'UNION ALL SELECT 27 ' +
                              'UNION ALL SELECT 28 ' +
                              'UNION ALL SELECT 29 ' +
                              'UNION ALL SELECT 30 ' +
                         ') AS n1' +
                    ') AS a ' +
                #such that the 30 days are between now and the end of the month
                'WHERE DATE >= now() AND DATE < last_day(now()) ' +
                  #and the date is when the student has class
                  'AND DAYNAME(DATE) = %s ' +
                'ORDER BY DATE;', (cid,sid,day.title(),))

"""Displaying scheduling functionality"""

def getMonthClasses(curs, sid, month, year):
    """Get all classes a student attended for a specific month/year for a given student"""
    curs.execute('select * from schedule ' + 
        'inner join classes using (cid) ' + 
        'where sid=%s and monthname(classDate)=%s and year(classDate)=%s group by classDate', (sid, month, year))
    return curs.fetchall()

def getMonths(curs, sid):
    """Get only months where student attended/scheduled/cancelled classes"""
    curs.execute('select distinct monthname(classDate) as month, '+ 
        'year(classDate) as year from schedule where sid=%s', (sid, ))
    return curs.fetchall()

def getClassDays():
    """Get all days of the week with class slots"""
    conn = cursor()
    conn.execute('select distinct day from classes')
    return conn.fetchall()

def getWeekStartEnd(curs, weeks):
    """Return dates of the Monday and Sunday of specified week. Parameter indicates number of 
    weeks before or after the current week."""
    weeks = weeks*7

    if weeks < 0: #Indicates previous weeks
        weeks = (-1)*weeks
        curs.execute('select DATE_SUB(DATE_ADD(CURDATE(), INTERVAL - WEEKDAY(CURDATE()) DAY), INTERVAL %s DAY) as monday', (weeks, ))

    else: #Indicates current or later weeks
        curs.execute('select DATE_ADD(DATE_ADD(CURDATE(), INTERVAL - WEEKDAY(CURDATE()) DAY), INTERVAL %s DAY) as monday', (weeks, ))
    
    monday = curs.fetchone()['monday']
    curs.execute('select DATE_ADD(%s, INTERVAL 6 DAY) as sunday', (monday, ))
    sunday = curs.fetchone()['sunday']

    #return tuple
    return (monday, sunday)

def getWeekClasses(curs, monday, sunday):
    """Return the classes that occur between given dates of a Monday and Sunday"""
    curs.execute('select * from schedule inner join classes using (cid) inner join (select name, sid, cid as class_id from students) as names' + 
        ' using (sid) where classDate between %s and %s' + 
        ' order by FIELD(day, "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")', (monday, sunday))
    return curs.fetchall()

def attendanceDate(curs, classDate, cid):
    """Get all students that attended a class on a certain date"""
    curs.execute('select sid, name from '+
                    '(select sid '+
                    'from schedule '+
                    'where classDate=%s '+
                    'and cid=%s '+
                    'and (status="scheduled" '+
                    'or status="rescheduled")'+
                ') as sch '+ 
                'inner join students '+
                'using (sid)', (classDate, cid))
    return curs.fetchall()

def changeStatus(curs, sid, cid, date, status):
    """Upddate status of a class for a student to either attended or cancelled. 
    Mainly used to take attendance"""
    curs.execute('update schedule ' +
                 ' set status=%s ' + 
                 ' where sid=%s ' + 
                 ' and classDate=%s ' + 
                 ' and cid=%s', 
                 (status, sid, date, cid))
    return None


"""Indexing students / displaying student information """

def searchStudent(curs, keyword):
    """Search student table for matching students to keyword and returns them.
    Returns None if no students found"""
    curs.execute('select sid,name,grade from students where name like %s', ('%'+keyword+'%',))
    return curs.fetchall()

def getStudent(curs, username):
    """Get student row given a username. We want to return all columns as this is a multiuse function."""
    curs.execute('select * from students where username=%s', (username, ));
    return curs.fetchone()

def getStudentByID(curs, sid):
    """Get student given student id. We want to return all columns as this is a multiuse function."""
    curs.execute('select * from students where sid=%s', (sid, ))
    return curs.fetchone()

def getAllStudents():
    """Get all students in tutoring center"""
    conn = cursor()
    conn.execute('select name,grade,sid from students')
    return conn.fetchall()


"""Indexing classes / displaying class information""" 

def getClassbyID(curs, cid):
  """Get class slot given class id. We want to return all columns as this is a multiuse function."""
  curs.execute('select * from classes where cid=%s', (cid,))
  return curs.fetchone()

def getClassbyDate(curs, classDate,username):
  """Get class slot given date and student username. We want to return all columns as this is a multiuse function."""
  sid = getStudent(curs, username)['sid']
  curs.execute('select * from schedule where classDate=%s and sid=%s',(classDate,sid,))
  return curs.fetchone()

def getClassStudents(curs, cid):
    """Get students in a class given class id"""
    curs.execute('select * from students where cid=%s',(cid,))
    return curs.fetchall()

def getClassesByGrade(curs, grade):
    """Get all classes at a certain grade level"""
    curs.execute('select cid,day,startTime,endTime from classes where grade=%s', (grade,))
    return curs.fetchall()

def getAllClasses():
    """Get all classes fixed per week"""
    conn = cursor()
    conn.execute('select cid,day,startTime,endTime from classes')
    return conn.fetchall()

"""Rescheduling"""

def rescheduleOptions(curs, grade,cid):
    """Get all plausible classes that can be rescheduled with open spots"""

    curs.execute(#filtering further: grade is the same as the student, class isn't same as the class
                 #the student is cancelling, & class is within next two weeks
                'select * from ('+
                    
                    #gathering class information for these filtered classes by joining with the classes table
                    'select classes.cid, day,startTime,endTime,grade,classDate,classCount from classes,('+
                        
                        #filtering only the classes with spots open
                        'select * from ('+ 
                            
                            #selecting the number of students in each class slot
                            'select cid, classDate, count(cid) as classCount '+
                            'from schedule '+
                            'group by cid,classDate'+
                        
                        ') as counting '+
                        'where counting.classCount<=3'+
                    
                    ') as minCount '+
                    'where classes.cid=minCount.cid'+
                
                ') as finalShortlist '+
                'where grade=%s '+
                'and classDate>=NOW() '+
                'and classDate<=NOW()+INTERVAL 2 WEEK '+
                'and finalShortlist.cid!=%s '+
                'order by classDate',(grade,cid,))
    
    return curs.fetchall()

def cancelClass(curs, classDetails):
    """Update old class to be cancelled within db. Returns this deleted class"""
    curs.execute('select classDate,startTime,endTime from schedule,classes where classDate=%s and schedule.sid=%s and schedule.cid=classes.cid',(classDetails['classDate'],classDetails['sid'], ))
    row = curs.fetchone()
    curs.execute('update schedule set status="cancelled" where classDate=%s and sid=%s',(classDetails['classDate'],classDetails['sid']))
    return row

def reschedule(curs, classDate,username):
    """Insert information ab out newly rescheduled class into db. Returns this newly scheduled class"""
    sid = getStudent(curs, username)['sid']
    curs.execute('insert into schedule values(%s, %s, %s, "rescheduled")', (classDate, cid, sid, ))    
    curs.execute('select classDate,startTime,endTime from schedule,classes where classDate=%s and schedule.sid=%s and schedule.cid=classes.cid',(classDate, sid, ))
    return curs.fetchone()


'''Payment Helper Functions'''

def getPaymentMonths():
    '''Get months for payment template from schedule table'''
    conn = cursor()
    conn.execute('select distinct month, year from payment');
    
    return conn.fetchall()

def getAllPaymentByMonth(curs, month, year):
    '''Gets payment info for all students based on month, year'''
    curs.execute('select distinct sid, name, payDate, status, ' + 
        ' amount_due from payment ' + 
        'inner join students using (sid) ' + 
        'where month=%s and year=%s', (month, year))
    return curs.fetchall()

def updatePayment(curs, sid, month, year, status, payDate, amount_due):
    '''Update payment info info for student for a given month and year'''
    curs.execute('update payment set status=%s, payDate=%s, amount_due=%s where sid=%s ' + 
        ' and month=%s and year=%s', (status, payDate, amount_due, sid, month, year))

    return None

def getStudentPayment(curs, sid):
    '''Return student payment info for a given student'''
    curs.execute('select month, year, amount_due, status,' + 
        ' DATE_FORMAT(payDate, "%%m-%%d-%%Y") as payDate' + 
        ' from payment where sid=%s', 
                (sid, ))
    return curs.fetchall()

def getNameSID(curs, username):
    '''Return just student sid and name for a given username'''
    curs.execute('select sid, name from students where username=%s', 
        (username,))
    return curs.fetchone()


'''Functions for File Upload'''
def getFiles(curs, sid):
    '''Return all files uploaded for student'''
    curs.execute('select DATE_FORMAT(uploadDate, "%%m-%%d-%%Y") as uploadDate, file_path, name from documents where sid=%s', (sid, ))
    return curs.fetchall()


def uploadFiles(curs, sid, name, file_path, date):
    curs.execute('insert into documents values(%s, %s, %s, %s)', 
        (sid, name, file_path, date))
    return None

