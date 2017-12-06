import os, sys, datetime, MySQLdb, dbconn2, bcrypt, final
from datetime import datetime
from flask import (Flask, render_template, request, redirect, url_for, flash, make_response,
                   session, send_from_directory)
from werkzeug import secure_filename
app = Flask(__name__)
app.secret_key = 'pompizza'

@app.route('/') #Renders homepage
def index():
  '''Home Page'''
  if 'username' in session:
    return redirect(url_for('user',username=session['username']))
  return render_template('home.html',pageTitle='Welcome to 800Club', subheading='SAT & K12 Math Tutoring')

@app.route('/join/', methods=['POST', 'GET'])
def join():
  '''Create new account'''

  if 'username' in session: #Checks if someone is already logged in
    return redirect(url_for('user',username=session['username']))
  if request.method=="GET":
    return render_template('signup.html',pageTitle="Sign Up")

  #Post Request. Gets user input
  else:  
    try:
        username = request.form['username']
        passwd1 = request.form['password1']
        passwd2 = request.form['password2']

        if passwd1 != passwd2:
            flash('passwords do not match')
            return redirect( url_for('join'))

        hashed = bcrypt.hashpw(passwd1.encode('utf-8'), bcrypt.gensalt())

        #Checks for unique username
        if not final.uniqueUsername(username): 
            flash('That username is taken')
            return redirect( url_for('join') )

        session['username'] = username
        session['logged_in'] = True
        session['visits'] = 1

        name = request.form["name"]
        email = request.form["email"]
        grade = request.form["grade"]
        phone = request.form["phone"]

        #insert new student into database
        final.insertNewStudent(username, hashed, name, email, phone, 75, 2, grade)
        return redirect( url_for('user', username=username) )

    except Exception as err:
        flash('form submission error '+str(err))
        return redirect( url_for('join') ) 

@app.route('/login/', methods=["POST", "GET"])
def login():
  '''Login page'''
  #Checks if user is already logged in
  if 'username' in session:
    return redirect(url_for('user',username=session['username']))
  if request.method=="GET":
    return render_template('login.html', pageTitle="Sign in")

  #Post request. Gets user input
  if request.method=="POST":
    try:
        username = request.form['username']
        password = request.form['password']
   
        #Checks if login info is accurate
        if final.checkLogin(username, password):
            flash('Successfully logged in as '+username.title())
            session['username'] = username
            session['logged_in'] = True
            session['visits'] = 1
            return redirect( url_for('user', username=username) )
        else:
            flash('Login is incorrect. Please try again or join.')
            return redirect( url_for('login'))
    except Exception as err:
        flash('Form submission error '+str(err))
        return redirect( url_for('login') )

@app.route('/user/<username>')
def user(username):
    try:
        '''Home page for logged in user'''

        if 'username' in session:
            username = session['username']
            student = final.getStudent(username)
            session['visits'] = 1+int(session['visits'])

            #Log in admin
            if username=="admin":
              return render_template('logAdmin.html',pageTitle='Welcome, Admin') 
            #Log in student
            name = student['name']
            return render_template('logUser.html', pageTitle='Aloha, '+ name.title(),
                                   name=name, sid=student['sid'])
        else:
            flash('You are not logged in. Please login or join.')
            return redirect( url_for('index') )
    except Exception as err:
        flash('Some kind of error '+str(err))
        return redirect( url_for('index') )

@app.route('/logout/')
def logout():
  '''Log out user'''
  try:
        if 'username' in session:
            username = session['username']
            session.pop('username')
            session.pop('logged_in')
            flash('You are logged out.')
            return redirect(url_for('index'))
        else:
            flash('You are not logged in. Please login or join.')
            return redirect( url_for('index') )
  except Exception as err:
    flash('Some kind of error '+str(err))
    return redirect( url_for('index') )

@app.route('/search/', methods=['POST','GET'])
def searchBar():
  '''Search through students in database'''

  #Only give this functionality to admin
  if 'username' in session and session['username']=="admin":
    if request.method == 'POST': 
      keyword = request.form['search-name']
      
      if keyword != "": #if nonempty, then fetch row from database
        results = final.searchStudent(keyword)

        if len(results) > 0: 
          if len(results) == 1: #Automatically display matching profile if result is 1
            return redirect(url_for('oneStudent',sid=results[0]["sid"]))
          return render_template('multStudents.html',pageTitle="Results for '"+keyword+"'", allStudents=results)

        flash("Student does not exist.") #Flashes error if no such title

      flash ("Please enter a Student to search.") #Flashes error if empty search
    return render_template('searchBar.html',pageTitle='Search for a Student')

  flash("You do not have permission to access this page.")
  return redirect(url_for('index'))

@app.route('/student/')
@app.route('/student/<sid>/', methods=['POST','GET'])
def oneStudent(sid=0):
  '''Student profile page'''

  if request.method== 'GET':
    if(sid==0): #logged in student tries to access their own profile
      sid = final.getStudent(session['username'])['sid'] #get their sid using logged in username

    student = final.getStudentByID(sid) 

    #Give access only if logged in student is trying to access their own profile or admin
    if student['username'] == session['username'] or session['username'] == 'admin':
      classRow = final.getClassbyID(student["cid"])
      return render_template('oneStudent.html',pageTitle=student["name"],
        grade=student["grade"],email=student["email"],
      	phone=student["phone"],rate=student["hour_rate"],joinDate=student["joinDate"],day=classRow["day"].title(),
        startTime=classRow["startTime"], endTime=classRow["endTime"], cid=classRow["cid"], sid=sid)  

  flash ("You do not have permission to access this page.")
  return redirect(url_for('index'))

@app.route('/class/<cid>/')
def oneClass(cid):
  '''Show details of a specific class slot'''

  #Only logged in individuals can access
  if 'username' in session:
    classRow=final.getClassbyID(cid)
    classStudents = final.getClassStudents(cid)
    student = final.getStudent(session['username'])

    #Only admin or student within this class slot can view information
    if session['username'] == 'admin' or student['cid'] == cid:
      return render_template('oneClass.html', username = session['username'], pageTitle=classRow["day"].title()+", "+classRow["startTime"],
        grade=classRow["grade"],allStudents=classStudents, startTime=classRow["startTime"], endTime=classRow["endTime"],
        day=classRow["day"].title())

  flash ("You do not have permission to access this page.")
  return redirect(url_for('index'))

@app.route('/allStudents')
def showStudents():
  '''Display all students'''

  #Admin acess only
  if 'username' in session and session['username']=="admin":
    students = final.getAllStudents()
    return render_template('multStudents.html',pageTitle='Students',allStudents = students)
  flash ("You do not have permission to access this page.")
  return redirect(url_for('index')) 

@app.route('/allClasses')
def showClasses():
  '''Display all class slots'''

  #Admin access only
  if 'username' in session and session['username']=="admin":
    classes = final.getAllClasses()
    return render_template('multClasses.html',pageTitle='Classes',allClasses = classes) 

  flash("You do not have permisson to access this page.")
  return redirect(url_for('index')) 


@app.route('/payment/', methods=['POST','GET']) 
def payment():
  return render_template('base.html',pageTitle='Payment Tracking')

@app.route('/schedule/')
@app.route('/schedule/<sid>')
@app.route('/schedule/<sid>/<month>/<year>', methods= ['GET','POST']) 
def schedule(sid=0, month=None, year=None):
    ''' Show all classes that student is scheduled for '''

    #No month/year passed in. Use current month and year
    if month is None and year is None:
      month = datetime.now().strftime("%B")
      year = datetime.now().year

    if 'username' in session:
       username = session['username']
       student = final.getStudent(username)

       if username == 'admin' or student['username'] == username:
        if sid == 0: #No sid entered. Use sid of logged in student
          sid = student['sid'] 

        classes = final.getMonthClasses(sid, month, year) #Get all classes corresponding to sid, month, and year
        dropdown = final.getMonths(sid) #Used to populate dropdown in template
        return render_template('schedule.html', classes=classes, sid=sid, totalMonths = dropdown, pageTitle=final.getStudentByID(sid)['name'] + "'s Schedule")

    flash ("You don't have permission to access this page.")
    return redirect(url_for('index')) 

@app.route('/reschedule/view/<grade>', methods=['GET'])
@app.route('/reschedule/cancel/<classDate>', methods=['GET','POST'])
@app.route('/reschedule/book/<cid>/<classDate>',methods=['GET'])
def reschedule(classDate=None, cid=None, grade=None):
  if 'username' in session and session['username']!="admin":
    username=session['username']
    try:
      if grade is not None and final.getStudent(username)['grade']==grade:
        return render_template('newClass.html', pageTitle='Alternate Classes',
        allClasses=final.rescheduleOptions(grade), grade=grade)

      if cid is None:
        dateSpecific = final.getClassbyDate(classDate,session['username'])
        if dateSpecific is not None:
          classInfo = final.getClassbyID(dateSpecific['cid'])
          if request.method=='GET':	return render_template('rescheduleConfirm.html',pageTitle='Reschedule',
            dateSpecific=dateSpecific, classInfo=classInfo)
          if request.form["submit"]=='No': flash('Ok. Your class has not been cancelled.')
          if request.form["submit"]=='Yes':
            final.cancelClass(dateSpecific)
            return redirect(url_for('reschedule',grade=classInfo['grade']))
        else: flash("You do not have permission to access this page")
        return redirect(url_for('schedule'))
      
      elif cid is not None and classDate is not None:
        added = final.reschedule(cid,classDate,username)
        return render_template('newClassConfirm.html', pageTitle='Your Booking',added=added)
    
    except Exception as err:
      flash('Some kind of error '+str(err))
  return redirect(url_for('index'))

@app.route('/admin-schedule')
def adminSchedule():
  '''Show admin's weekly schedule '''
  if 'username' in session and session['username']=="admin":

    classes = final.getAllClasses() #Get all class slots
    days = final.getClassDays() #Get just class days

    return render_template('scheduleAdmin.html',pageTitle='All Classes', classes=classes, days=days) 


if __name__ == '__main__':
    app.debug = True
    port = os.getuid()
    # Flask will print the port anyhow, but let's do so too
    print('Running on port '+str(port))
    app.run('0.0.0.0',port)
