#Mathangi Ganesh and Meher Vohra
#Final Project
import dbconn2
import MySQLdb
import os
import sys
import bcrypt
from flask import (Flask, render_template, make_response,
                    url_for, request, flash, redirect)


DATABASE = 'tutor_db'

#Establish the connection with the database
def cursor(database=DATABASE):
    DSN = dbconn2.read_cnf()
    DSN['db'] = database
    conn = dbconn2.connect(DSN)
    return conn.cursor(MySQLdb.cursors.DictCursor)

#Check if username already exists in db
def uniqueUsername(username):
    curs = cursor()
    curs.execute('SELECT username FROM userpass WHERE username = %s',(username,))
    row = curs.fetchone()
    return row is None

#Check if login credentials are valid
def checkLogin(username, password):
    curs = cursor()
    curs.execute('SELECT hashed FROM userpass WHERE username = %s',[username])
    row = curs.fetchone()
    if row is None:
        return False

    hashed = row['hashed']
    if bcrypt.hashpw(password.encode('utf-8'),hashed.encode('utf-8')) == hashed:
        return True

    return False

#Insert new student into database. Insert into userpass table and student table
def insertNewStudent(username, hashed, name, email, phone, hour_rate, cid, grade):
    curs = cursor()
    curs.execute('INSERT into userpass(username,hashed) VALUES(%s,%s)',
                     [username, hashed])
    curs.execute('INSERT into students VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_DATE, %s)',
          [None, name, email, phone, hour_rate, grade, cid, username])


#Search student table for matching students
def searchStudent(keyword):
    curs = cursor()
    curs.execute('select sid,name,grade from students where name like %s', ('%'+keyword+'%',))
    rows = curs.fetchall()
    return rows

#Get all classes for a specific month/year for a given student
def getMonthClasses(sid, month, year):
    curs = cursor()
    curs.execute('select * from schedule inner join classes using (cid) where sid=%s and monthname(classDate)=%s and year(classDate)=%s group by classDate', (sid, month, year))
    rows = curs.fetchall()
    return rows

#Get only months where student attended/scheduled/cancelled classes
def getMonths(sid):
    curs = cursor()
    curs.execute('select distinct monthname(classDate) as month, year(classDate) as year from schedule where sid=%s', (sid, ))
    rows = curs.fetchall()
    return rows

#Get all class slots
def getAllClasses():
    ''' Returns all classes and all students'''
    curs = cursor()
    curs.execute("select * from classes")
    rows = curs.fetchall()
    return rows

#Get all days of the week with class slots
def getClassDays():
    curs = cursor()
    curs.execute('select distinct day from classes');
    rows = curs.fetchall()
    return rows

#Get student given a username
def getStudent(username):
    curs = cursor()
    curs.execute('select * from students where username=%s', (username, ));
    student = curs.fetchone();
    return student;

#Get student given student id
def getStudentByID(sid):
    curs = cursor()
    curs.execute('select * from students where sid=%s', (sid, ))
    student = curs.fetchone()
    return student

#Get class slot given class id
def getClassbyID(cid):
  curs = cursor() # results as Dictionaries
  curs.execute('select * from classes where cid=%s', (cid,))
  return curs.fetchone()

#Get class slot given date and student
def getClassbyDate(classDate,username):
  curs = cursor() # results as Dictionaries
  sid = getStudent(username)['sid']
  curs.execute('select * from schedule where classDate=%s and sid=%s', (classDate,sid,))
  return curs.fetchone()

#Get students in a class given class id
def getClassStudents(cid):
    curs = cursor()
    curs.execute('select * from students where cid=%s',(cid,))
    rows = curs.fetchall()
    return rows

#Get all students in tutoring center
def getAllStudents():
    curs = cursor()
    curs.execute('select * from students')
    rows = curs.fetchall()
    return rows

#Get all classes in the next two weeks with spots open at the same grade level as the student rescheduling
def rescheduleOptions(grade,cid):
    curs = cursor() # results as Dictionaries
    curs.execute('select * from (select classes.cid, day,startTime,endTime,grade,classDate,classCount from classes,(select * from (select cid, classDate, count(cid) as classCount from schedule group by cid,classDate) as counting where counting.classCount<=3) as minCount where classes.cid=minCount.cid) as finalShortlist where grade=%s and classDate>=NOW() and classDate<=NOW()+INTERVAL 2 WEEK and finalShortlist.cid!=%s order by classDate',(grade,cid,))
    """
    written in MUCH more readable way:
    select * from (
      select classes.cid,day,startTime,endTime,grade,classDate,classCount from classes,(
        select * from (
            select cid, classDate, count(cid) as classCount
            from schedule
            group by cid,classDate
        ) as counting
        where counting.classCount<=3
      ) as minCount
      where classes.cid=minCount.cid
     ) as finalShortlist
     where grade=12
     and classDate>=NOW()
     and classDate<=NOW()+INTERVAL 2 WEEK
     and finalShortlist.cid!=2
     order by classDate;
    """
    rows=curs.fetchall()
    return rows

def reschedule(cid,classDate,username):
    curs = cursor() # results as Dictionaries
    sid = getStudent(username)['sid']
    curs.execute('insert into schedule values(%s, %s, %s, "rescheduled")', (classDate, cid, sid, ))    
    curs.execute('select classDate,startTime,endTime from schedule,classes where classDate=%s and schedule.sid=%s and schedule.cid=classes.cid',(classDate, sid, ))
    return curs.fetchone()

def cancelClass(classDetails):
    curs = cursor() # results as Dictionaries
    curs.execute('select classDate,startTime,endTime from schedule,classes where classDate=%s and schedule.sid=%s and schedule.cid=classes.cid',(classDetails['classDate'],classDetails['sid'], ))
    row = curs.fetchone()
    curs.execute('update schedule set status="cancelled" where classDate=%s and sid=%s',(classDetails['classDate'],classDetails['sid']))
    return row
