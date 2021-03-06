"""
Meher Vohra, Mathangi 
12/19/17
app.py
CS 304 Final Project

Main file that should be run to engage the Flask web app

"""

import os, sys, datetime, MySQLdb, dbconn2, bcrypt, helpFunc
from datetime import datetime
from flask import (Flask, render_template, request, redirect, url_for, flash, make_response,
                   session, send_from_directory, g)
from werkzeug import secure_filename

app = Flask(__name__)
app.secret_key = 'pompizza'

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'worksheets')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_conn():
  conn = getattr(g, '_database', None)
  if conn is None:
    conn = g._database = helpFunc.cursor()
  return conn


@app.route('/') #Renders homepage
def index():
  '''Home Page'''
  if 'username' in session:
    return redirect(url_for('user',username=session['username']))
  return render_template('home.html',
					  	pageTitle='Welcome to 800Club',
					  	subheading='SAT & K12 Math Tutoring',
              classes=helpFunc.getClassesByGrade(get_conn(), 12),
              hideContent=True)

@app.context_processor
def inject_notif():
	"""To store certain functions within the context and
	keep our code thread safe. We need these two functions for the
	notifications bar"""	
  	return dict(unverified=helpFunc.getUnverified(),
              allClasses = helpFunc.getAllClasses())

@app.route('/join/', methods=['POST'])
def join():
  '''Create new account'''
  if 'username' in session: #Checks if someone is already logged in
    return redirect(url_for('user',username=session['username']))

  #Post Request. Gets user input
  else:  
    try:
        username = request.form['username']
        passwd1 = request.form['password1']
        passwd2 = request.form['password2']

        if passwd1 != passwd2:
          flash('passwords do not match')
          return redirect( url_for('index'))

        #Checks for unique username
        if not helpFunc.uniqueUsername(get_conn(), username): 
          flash('That username is taken')
          return redirect( url_for('index') )

        session['username'] = username
        session['logged_in'] = True
        session['visits'] = 1

        name = request.form["name"]
        email = request.form["email"]
        grade = request.form["grade"]
        phone = request.form["phone"]
        cid = request.form["classChoice"]

        #insert new student into database as unverified, awaiting admin approval
        helpFunc.insertNewStudent(get_conn(), username, passwd1, name, email, phone, cid, grade)
        return redirect( url_for('user', username=username) )

    except Exception as err:
        flash('form submission error '+str(err))
        return redirect( url_for('index') ) 

@app.route('/approve/', methods=["POST"])
def approve():
  """The choices the admin has in approving/denying a new registrant
  Can either choose to:
  	1) approve:
  	- select the student's class
  	- mark as verified in the students db
  	- populate them in the schedule table for the rest of the month
  	2) deny:
  	- remove from all records """

  if 'username' in session and session['username']=='admin':
    sid = request.form["sid"]
    
    if request.form['submit']=="Deny":
      flash("Student successfully removed.")
      helpFunc.denyStudent(get_conn(), sid)
    
    if request.form['submit']=="Accept":
      flash("Student successfully added.")
      helpFunc.verifyStudent(get_conn(), sid,request.form['hour_rate'])
      helpFunc.insertSchedule(get_conn(), request.form["classChoice"],sid)
    
  return redirect(url_for('index'))
    
@app.route('/login/', methods=["POST"])
def login():
	'''Login page'''
	#Checks if user is already logged in
	if 'username' in session:
		return redirect(url_for('user',username=session['username']))

	#Post request. Gets user input
	try:
	    username = request.form['username']
	    password = request.form['password']

	    #Checks if login info is accurate
	    if helpFunc.checkLogin(get_conn(), username, password):
	        flash('Successfully logged in as '+username)
	        session['username'] = username
	        session['logged_in'] = True
	        session['visits'] = 1
	        return redirect( url_for('user', username=username) )
	    else:
	        flash('Login is incorrect. Please try again or join.')
	        return redirect( url_for('index'))
	except Exception as err:
	    flash('Form submission error '+str(err))
	    return redirect( url_for('index') )

@app.route('/user/<username>')
def user(username):
    try:
        '''Home page for logged in user'''

        if 'username' in session:
            username = session['username']
            student = helpFunc.getStudent(get_conn(), username)

            #Log in admin
            #hideContent is for html purposes (to hide the download div)
            if username=="admin":
            	return render_template('logAdmin.html',
                                      pageTitle='Welcome, Admin',
                                      hideContent=True)
            #Log in student
            name = student['name']
            return render_template('logUser.html',
					            	pageTitle='Aloha, ' + name.title(),
					                name=name,
					                sid=student['sid'],
					                hideContent=True)
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
      
      if keyword != "": #if nonempty, then fetch rows from database
        results = helpFunc.searchStudent(get_conn(), keyword)

        if len(results) > 0: 
          if len(results) == 1: #Automatically display matching profile if result is 1
            return redirect(url_for('oneStudent',sid=results[0]["sid"]))
          return render_template('multStudents.html',
					          	pageTitle="Results for '"+keyword+"'",
					          	allStudents=results)

        flash("Student does not exist.") #Flashes error if no such title

      flash ("Please enter a Student to search.") #Flashes error if empty search
    return render_template('searchBar.html',pageTitle='Search for a Student')

  return redirect(url_for('index'))

@app.route('/student/')
@app.route('/student/<sid>/', methods=['POST','GET'])
def oneStudent(sid=0):
  '''Student profile page'''

  if request.method== 'GET':
    if(sid==0): #logged in student tries to access their own profile
      sid = helpFunc.getStudent(get_conn(), session['username'])['sid'] #get their sid using logged in username

    student = helpFunc.getStudentByID(get_conn(), sid)

    #Give access only if logged in student is trying to access their own profile or admin
    if student['username'] == session['username'] or session['username'] == 'admin':
      classRow = helpFunc.getClassbyID(get_conn(), student["cid"])
      return render_template('oneStudent.html',
						      	pageTitle=student["name"],
						      	studentRow=student,
						      	classRow=classRow)

  return redirect(url_for('index'))

@app.route('/edit/classes/')
def editClasses():
	"""YET TO IMPLEMENT"""
	return render_template('editClasses.html',
  	pageTitle='Edit Classes')

@app.route('/class/<cid>/')
def oneClass(cid):
  '''Show details of a specific class slot'''

  #Only logged in individuals can access
  if 'username' in session and session['username']=="admin":
    classInfo=helpFunc.getClassbyID(get_conn(), cid)
    allStudents = helpFunc.getClassStudents(get_conn(), cid)

    #Only admin or student within this class slot can view information
    return render_template('oneClass.html',
					    	pageTitle=classInfo["day"].title()+", "+classInfo["startTime"],
					    	classInfo = classInfo,
					    	allStudents = allStudents)

  return redirect(url_for('index'))

@app.route('/allStudents')
def showStudents():
  '''Display all students'''

  #Admin acess only
  if 'username' in session and session['username']=="admin":
    return render_template('multStudents.html',
    						pageTitle='Students',
    						allStudents=helpFunc.getAllStudents())
  return redirect(url_for('index')) 


@app.route('/payment/', methods=['GET', 'POST'])
@app.route('/payment/<month>/<year>', methods=['GET', 'POST'])
def update_payment(month=None, year=None):
  '''Form for admin to update payment per month for each student'''

  if 'username' in session and session['username'] == 'admin':

    '''Get all students who have attended classes this month'''
    months = helpFunc.getPaymentMonths() #all months in payment table

    if month is None and year is None:
      month = datetime.now().strftime("%B")
      year = datetime.now().year

    if request.method=="POST":
      
      students = helpFunc.getAllPaymentByMonth(get_conn(), month, year) #all students in month
      try:
        '''Update payment records'''
        for i in students:
          status = request.form[i['sid']] 
          payDate = request.form["date_" + i['sid']]
          amount_due = request.form['amount_due_' + i['sid']]
          helpFunc.updatePayment(get_conn(), i['sid'], month, year, status, payDate, amount_due)

      except Exception as err:
        flash('form submission error '+str(err))
        return redirect( url_for('update_payment', month=month, year=year))

    
    students = helpFunc.getAllPaymentByMonth(get_conn(), month, year) #getting updated list
    return render_template('updatePayment.html', pageTitle='Payment Tracking', months=months,
                          students=students, month=month, year=year)

  flash ("You don't have permission to access this page.")
  return redirect(url_for('index'))

@app.route('/student/payment/')
@app.route('/student/payment/<username>')
def studentPayment(username=None):

  if 'username' in session:
    student = None

    if session['username'] != 'admin':
      if username is None or session['username'] == username:
        student = helpFunc.getStudent(get_conn(), session['username'])

      else:
        flash ("You don't have permission to access this page.")
        return redirect(url_for('index')) 

    elif session['username'] == 'admin':
      if username is not None:
        student = helpFunc.getStudent(get_conn(), username)

      else:
        flash ("Please choose a student to view information.")
        return redirect(url_for('showStudents'))

    if student is not None:
      paymentInfo = helpFunc.getStudentPayment(get_conn(), student['sid'])
      return render_template('studentPayment.html', pageTitle="Payment Records for " + student['name'], 
                      paymentInfo=paymentInfo, username=session['username'])
    
    else:
      flash ("Student's payment info does not exist.")
      return redirect(url_for('index')) 
  
  flash ("You don't have permission to access this page.")
  return redirect(url_for('index')) 
  
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
      student = helpFunc.getStudent(get_conn(), username)

      if username == 'admin' or (student is not None and student['username'] == username):

        if sid == 0: #No sid entered. Use sid of logged in student
          if username == 'admin':
            flash("Admin, please choose a student to view.")
            return redirect(url_for('showStudents')) 
          else:
            student = helpFunc.getStudent(get_conn(), username)
            sid = student['sid'] 

        classes = helpFunc.getMonthClasses(get_conn(), sid, month, year) #Get all classes corresponding to sid, month, and year
        dropdown = helpFunc.getMonths(get_conn(), sid) #Used to populate dropdown in template
        return render_template('schedule.html', classes=classes, sid=sid, totalMonths=dropdown, 
          pageTitle=helpFunc.getStudentByID(get_conn(), sid)['name'] + "'s Schedule")

    flash ("You don't have permission to access this page.")
    return redirect(url_for('index')) 

@app.route('/reschedule/cancel/<classDate>', methods=['GET','POST'])
@app.route('/reschedule/book/<cid>/<classDate>',methods=['GET','POST'])
def reschedule(classDate=None, cid=None):
  """Cancels user's existing class and books new class"""
  if 'username' in session and session['username']!="admin":
    username=session['username']
    dateSpecific = helpFunc.getClassbyDate(get_conn(), classDate,username)
    
    """CANCELLATION OF CLASS"""
    if cid is None:

      if dateSpecific is not None:
        cid=dateSpecific['cid']
         
        if request.method=='GET': #ask user to confirm they want to cancel
        	return render_template('cancelConfirm.html',
					        		pageTitle='Reschedule',
					          		dateSpecific=dateSpecific,
					          		classInfo=helpFunc.getClassbyID(get_conn(), cid))
          
        if request.form["submit"]=='Yes': #user confirms cancellation, display alt classes 	 
          grade = helpFunc.getStudent(get_conn(), username)['grade']
          return render_template('altClasses.html',
						          	pageTitle='Alternate Classes',
						          	allClasses=helpFunc.rescheduleOptions(get_conn(), grade,cid),
						          	deleted=helpFunc.cancelClass(get_conn(), dateSpecific))  

        #user decides not to cancel. 
        if request.form["submit"]=='No': flash('Ok. Your class has not been cancelled.')
      return redirect(url_for('schedule'))
    
    """BOOKING NEW CLASS""" 
    if dateSpecific is None: #new class doesn't already exist
    	return render_template('newClassConfirm.html',
					    		pageTitle='Your Booking',
					     	 	added=helpFunc.reschedule(get_conn(), cid,classDate,username))
    
  return redirect(url_for('index'))

@app.route('/attendance/<weeks>/<date>/<cid>', methods=['GET', 'POST'])
def attendance(weeks, date, cid):

  '''Show attendance form a given date'''

  students = helpFunc.attendanceDate(get_conn(), date, cid)

  if 'username' in session and session['username'] == 'admin':

    if request.method=="POST":

      try:
        for s in students: 
          #First students who were marked as attended
          if( str(s['sid']) in request.form.getlist('sid')):    
            helpFunc.changeStatus(get_conn(), s['sid'], cid, date, "attended")

          #Students who did not attend
          else:
            helpFunc.changeStatus(get_conn(), s['sid'], cid, date, "cancelled")
  
        return redirect( url_for('adminSchedule', weeks=weeks) )

      except Exception as err:
        flash('form submission error '+str(err))
        return redirect( url_for('adminSchedule', weeks=weeks) )

    else:
      return render_template('attendance.html', students=students, weeks=weeks, 
        date=datetime.strptime(date, '%Y-%m-%d').strftime('%m-%d-%Y'), cid=cid)

  flash ("You don't have permission to access this page.")
  return redirect(url_for('index'))


@app.route('/admin-schedule/')
@app.route('/admin-schedule/<weeks>')
@app.route('/admin-schedule/edit/')
def adminSchedule(weeks=0):
  '''Show admin's weekly schedule '''
  if 'username' in session and session['username']=="admin":
    '''first step: render this week's schedule'''
    #Get start date and end date of week to display for header
    startEndDates = helpFunc.getWeekStartEnd(get_conn(), int(weeks))
    classes = helpFunc.getWeekClasses(get_conn(), *startEndDates)

    days = []
    slots = {}
    for c in classes:
      if c['day'] not in days:
        days.append(c['day']) #get list of days that actually have classes
  
      if c['cid'] not in slots: #make the cid the keys in dict of slots
        slots[c['cid']] = []
        
    for c in classes:
      slots[c['cid']].append(c) #add class to corresponding slot based on cid
  
    return render_template('scheduleAdmin.html', classes=classes, days=days, pageTitle="Your Schedule", 
      slots=slots, weeks=int(weeks), startDate=startEndDates[0].strftime('%m-%d-%Y'), 
      endDate=datetime.strptime(startEndDates[1], '%Y-%m-%d').strftime('%m-%d-%Y'))

  flash ("You don't have permission to access this page.")
  return redirect(url_for('index'))

@app.route('/documents/')
@app.route('/documents/<username>/')
def documents(username=None):

  if 'username' in session:
    sid_name = None

    if session['username'] != 'admin':
      if username is None or session['username'] == username:
        sid_name = helpFunc.getNameSID(get_conn(), session['username'])

      else:
        flash ("You don't have permission to access this page.")
        return redirect(url_for('index')) 

    elif session['username'] == 'admin':
      if username is not None:
        sid_name = helpFunc.getNameSID(get_conn(), username)

      else:
        flash ("Please choose a student to view information.")
        return redirect(url_for('showStudents'))

    if sid_name is not None:
      files = helpFunc.getFiles(get_conn(), sid_name['sid'])
      return render_template('studentFiles.html', pageTitle="Files Uploaded for " + sid_name['name'], 
                        files=files, username=session['username'])

    else:
      flash ("No documents have been uploaded.")
      return redirect(url_for('index')) 
    
  flash ("You don't have permission to access this page.")
  return redirect(url_for('index')) 


def allowed_file(filename):
  '''Makes sure only files of certain extensions can be uploaded'''
  return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload/', methods=['GET', 'POST'])
def upload_documents():
  '''Allows admin to upload documents pertaining to a student'''
  
  if 'username' in session and session['username'] == 'admin':

    students = helpFunc.getAllStudents()

    if request.method == 'POST':
    # check if the post request has the file part
      if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

      file = request.files['file']
      # if user does not select file, browser also
      # submit a empty part without filename
      if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

      if request.form['name'] == '':
        flash('Please enter a description.')
        return redirect(request.url)

      if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        selected_sid = request.form['students']
        date = datetime.now()
        name = request.form['name']
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename)) #saves file
        helpFunc.uploadFiles(get_conn(), selected_sid, name, filename, date) #uploads file name to database
        flash('Upload Successful!')
        return render_template('upload.html', pageTitle="Upload Files", students=students)

    else:
      return render_template('upload.html', pageTitle="Upload Files", students=students)
  
  flash ("You don't have permission to access this page.")
  return redirect(url_for('index')) 


@app.route('/worksheets/<path:file>')
def send_file(file):
  '''Allows users to view files'''
  return send_from_directory('worksheets', file)


if __name__ == '__main__':
    app.debug = True
    port = os.getuid()
    # Flask will print the port anyhow, but let's do so too
    print('Running on port '+str(port))
    app.run('0.0.0.0',port)
