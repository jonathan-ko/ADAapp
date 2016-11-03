import os
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import pymongo
from pymongo import MongoClient
import json
	
from werkzeug import generate_password_hash, check_password_hash, secure_filename



app = Flask(__name__)
Client = MongoClient()
db = Client.WACDA
users = db.users
contacts = db.contacts
access = db.access
places = db.places

app.secret_key = 'why would I tell you my secret key?'

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'static/upload/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


@app.route("/")
def main():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')

@app.route('/signUp', methods=['POST'])
def signUp():
    # read the posted values from the UI
    email = request.form['inputEmail']
    password = request.form['inputPassword']
    # validate the received values
    if email and password:
        hashed_password = generate_password_hash(password)
        if users.count({"email": email}) == 0:
            users.insert_one({"email": email, "hashed_password": hashed_password})
            return json.dumps({'message':'User created successfully !'})
        else:
            return json.dumps({'error':'<span>Email exists!</span>'})
    else:
        return json.dumps({'html':'<span>Enter the required fields</span>'})

@app.route('/showSignin')
def showSignin():
    return render_template('signin.html')

@app.route('/validateLogin',methods=['POST'])
def validateLogin():
    try:
        username = request.form['inputEmail']
        password = request.form['inputPassword']
        data = users.find_one({"email":username})
        if check_password_hash(data['hashed_password'],password):
            session['user'] = data['email']
            return redirect('/dashboard')
        else:
            return render_template('error.html',error = 'Wrong Email address or Password.') 
    except Exception as e:
        return render_template('error.html',error = str(e))
        
# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# Route that will process the file upload
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
    # Get the name of the uploaded file
        file = request.files['file']
        # Check if the file is one of the allowed types/extensions
        if file and allowed_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to
            # the upload folder we setup
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Redirect the user to the uploaded_file route, which
            # will basicaly show on the browser the uploaded file
            return #redirect(url_for('uploaded_file', filename=filename))

# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be shown after the upload

@app.route('/static/upload/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)


@app.route('/showTestUpload')
def testUpload():
    return render_template('testUpload.html')

@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return render_template('error.html',error = 'Unauthorized Access')

@app.route('/addPlaces', methods=['POST'])
def addPlaces():
    if session.get('user'):
        email = session.get('user')
        user_obj=users.find_one({"email":email})
        user_id=user_obj['_id']
        # read the posted values from the UI
        dba = request.form['inputDBA']
        address = request.form['inputAddress']
        city = request.form['inputCity']
        zipcode = request.form['inputZipCode']
        notes = request.form['inputNotes']
        places.insert_one({"dba": dba, "address":address, "city":city, "zipcode":zipcode, "notes":notes, "case_info":[] "user_id":str(user_id)})
        return redirect('/dashboard.html')
    else:
        return redirect('signin.html')

@app.route('/getPlaces')
def getPlaces():
    return render_template('getPlace.html')

@app.route('/showClients')
def getClientList():
    return render_template('clients.html')

@app.route('/addContact', methods=['POST'])
def addContact():
    try:
        if session.get('user'):
            email = session.get('user')
            user_obj=users.find_one({"email":email})
            user_id=user_obj['_id']
            print user_id

            # read the posted values from the UI
            last_name = request.form['inputLastName']
            first_name = request.form['inputFirstName']
            address = request.form['inputAddress']
            city = request.form['inputCity']
            zipcode = request.form['inputZipCode']
            notes = request.form['inputNotes']
            contacts.insert_one({"last_name":last_name, "first_name":first_name, "address":address, "city":city, "zipcode":zipcode, "notes":notes, "case_info":[] "user_id":str(user_id)})
            return redirect('/showClients')
        else:
            return redirect('signin.html')
    except:
        return render_template('error.html', error = str(e))

@app.route('/getClients')
def getClient():
    if session.get('user'):
        email = session.get('user')
        user_obj=users.find_one({"email":email}) 
        user_id=user_obj['_id']
        user_contacts=contacts.find({"user_id":str(user_id)})
        return json.dumps({"data":user_contacts})
    else:
        return render_template('error.html', error = 'Unauthorized Access')


@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')


@app.route("/testDash")
def testDash():
    return render_template('testDash.html')


if __name__ == "__main__":
    app.run(host='0.0.0.0')
