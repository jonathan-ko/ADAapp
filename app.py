import os
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import pymongo
from pymongo import MongoClient
import json
from bson.json_util import dumps
	
from werkzeug import generate_password_hash, check_password_hash, secure_filename

import uuid

app = Flask(__name__)
Client = MongoClient()
db = Client.WACDA
users = db.users
contacts = db.contacts
access = db.access
places = db.places
types = db.types
checklists = db.checklists

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

@app.route('/showSignin')
def showSignin():
    return render_template('signin.html')

@app.route('/getPlaces')
def getPlaces():
    return render_template('addPlace.html')

@app.route('/showClients')
def getClientList():
    return render_template('clients.html')

@app.route('/showContacts')
def getContact():
    return render_template('addContact.html')

@app.route("/checklists")
def getChecklists():
    checklist_names=checklists.find()[1]
    return render_template('getChecklists.html', checklist_names)

@app.route("/testDash")
def testDash():
    return render_template('testDash.html')


@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return render_template('error.html',error = 'Unauthorized Access')

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')

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

@app.route('/validateLogin',methods=['POST'])
def validateLogin():
    try:
        username = request.form['inputEmail']
        password = request.form['inputPassword']
        data = users.find_one({"email":username})
        if check_password_hash(data['hashed_password'],password):
            session['user'] = data['email']
            return redirect('/testDash')
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

            extension = os.path.splitext(file.filename)[1]

            f_name = str(uuid.uuid4()) + extension


            # Move the file form the temporal folder to
            # the upload folder we setup
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], f_name))
            # Redirect the user to the uploaded_file route, which
            # will basicaly show on the browser the uploaded file
            return json.dumps({'filename':f_name})#redirect(url_for('uploaded_file', filename=filename))

# This route is expecting a parameter containing the name
# of a file. Then it will locate that file on the upload
# directory and show it on the browser, so if the user uploads
# an image, that image is going to be shown after the upload

@app.route('/static/upload/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)


@app.route('/addPlaces', methods=['POST'])
def addPlaces():
    if session.get('user'):
        email = session.get('user')
        user_obj=users.find_one({"email":email})
        user_id=user_obj['_id']
        # read the posted values from the UI
        dba = request.form['inputBusinessName']
        address = request.form['inputAddress']
        city = request.form['inputCity']
        zipcode = request.form['inputZipCode']
        notes = request.form['inputNotes']
        web_address = request.form['inputWebAddress']
        places.insert_one({"dba": dba, "address":address, "city":city, "zipcode":zipcode, "notes":notes, "web_address": web_address, "case_ids":[], "client_ids":[], "contact_ids":[], "user_id":str(user_id)})
        return redirect('/testDash')
    else:
        return redirect('signin.html')

@app.route('/addContact', methods=['POST'])
def addContact():
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
        try:
            gender = request.form['othergender']
        except:
            gender = request.form['inputGender']
        notes = request.form['inputNotes']
        contact_type = request.form['inputContactType']
        print ({"last_name":last_name, "first_name":first_name, "address":address, "city":city, "zipcode":zipcode, "gender":gender, "notes":notes, "contact_type":contact_type, "case_info":[], "user_id":str(user_id)})
        contacts.insert_one({"last_name":last_name, "first_name":first_name, "address":address, "city":city, "zipcode":zipcode, "gender":gender, "notes":notes, "contact_type":contact_type, "case_info":[], "user_id":str(user_id)})
        return redirect('/testDash')
    else:
        return redirect('signin.html')

@app.route('/getContacts',methods=['GET'])
def getClient():
    if session.get('user'):
        email = session.get('user')
        user_obj=users.find_one({"email":email}) 
        user_id=str(user_obj['_id'])
        user_contacts=dumps(contacts.find({"user_id":user_id}))
        print user_contacts
        return json.dumps({"data":user_contacts})
    else:
        return render_template('error.html', error = 'Unauthorized Access')

@app.route('/getTypes',methods=['GET', 'POST'])
def getTypes():
    return json.dumps(types.find()[0]['contact_types'])


if __name__ == "__main__":
    app.run(host='0.0.0.0')
