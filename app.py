import os
from flask import Flask, render_template, request, redirect, session, url_for, send_from_directory
import pymongo
from pymongo import MongoClient
import json
from bson.json_util import dumps
from bson.objectid import ObjectId
	
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
ADA_items = db.ADA_items


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

@app.route('/showClients')
def getClientList():
    return render_template('clients.html')

@app.route('/showContacts')
def getContact():
    return render_template('addContact.html')

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

        # read the posted values from the UI
        last_name = request.form['inputLastName']
        first_name = request.form['inputFirstName']
        email_address = request.form['inputEmailAddress']
        address = request.form['inputAddress']
        city = request.form['inputCity']
        zipcode = request.form['inputZipCode']
        try:
            gender = request.form['othergender']
        except:
            gender = request.form['inputGender']
        notes = request.form['inputNotes']
        contact_type = request.form['inputContactType']
        contacts.insert_one({"last_name":last_name, "first_name":first_name, "email_address":email_address, "address":address, "city":city, "zipcode":zipcode, "gender":gender, "notes":notes, "contact_type":contact_type, "case_info":[], "user_id":str(user_id)})
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
        #print user_contacts
        return json.dumps({"data":user_contacts})
    else:
        return render_template('error.html', error = 'Unauthorized Access')

@app.route('/getPlaces',methods=['GET'])
def getPlaces():
    if session.get('user'):
        email = session.get('user')
        user_obj=users.find_one({"email":email}) 
        user_id=str(user_obj['_id'])
        user_places = dumps(places.find({"user_id":user_id}))
        return json.dumps({"data":user_places})
    else:
        return render_template('error.html', error = 'Unauthorized Access')

@app.route('/getTypes',methods=['GET', 'POST'])
def getTypes():
    return json.dumps(types.find()[0]['contact_types'])

@app.route('/addChecklist',methods=['POST'])
def addChecklist():
    if session.get('user'):
        email = session.get('user')
        user_obj=users.find_one({"email":email}) 
        user_id=str(user_obj['_id'])
        checklist_name = request.form['inputChecklistName']
        checklist_id=checklists.insert_one({"user_id":user_id, "case_id":"", "place_id":"", "checklist_name":checklist_name, "checklist_items":[]})
        return render_template('checklist_template.html', checklist_name = checklist_name)
    else:
        return render_template('error.html', error = 'Unauthorized Access')

@app.route('/addItem',methods=['POST'])
def addItem():
    if session.get('user'):
        email = session.get('user')
        user_obj=users.find_one({"email":email}) 
        user_id=str(user_obj['_id'])
        checklist_name = request.form['checklist_name']
        ADA_standard = request.form['standardNum']
        Title = request.form['inputCategoryName']
        Description = request.form['inputDescription']
        filePath = request.form['filePath']
        inserted_item_id = ADA_items.insert_one({"ADA_standard":ADA_standard, "Title":Title, "Description":Description, "filePath":filePath}).inserted_id
        checklists.find_one_and_update({"checklist_name":checklist_name}, {'$push': {"checklist_items": {"inserted_item_id":str(inserted_item_id), "conforms":True, "measurements":"", "notes":""}}})
        data=[]
        c = checklists.find_one({"checklist_name":checklist_name})       
        for i in c["checklist_items"]:
            print i['inserted_item_id']
            ADA_id = i['inserted_item_id']
            ADA_item=ADA_items.find_one({'_id':ObjectId(ADA_id)})
            print ADA_item
            item_stats={"conforms":i["conforms"], "measurements":i["measurements"], "notes":i["notes"]}
            data.append({"ADA_item":ADA_item,"item_stats":item_stats})
        return render_template('checklist_template.html', checklist_name = checklist_name, data=data)
    else:
        return render_template('error.html', error = 'Unauthorized Access')

@app.route('/delItem',methods=['POST'])
def delItem():
    inserted_item_id_uncut=request.json['inserted_item_id']
    checklist_name = request.json['checklist_name']
    #print inserted_item_id_uncut
    inserted_item_id = inserted_item_id_uncut.split('_')[1]
    print inserted_item_id
    itemToRemove =  checklists.find_one_and_update({"checklist_name":checklist_name}, {'$pull': {"checklist_items": {"inserted_item_id":inserted_item_id}}})
    print itemToRemove
    return json.dumps({"data":"item deleted"})#render_template('checklist_template.html', checklist_name = checklist_name, data=data)

@app.route('/updateItem',methods=['POST'])
def updateItem():
    checklist_name=request.json['checklist_name']
    if request.json['conforms']=="true":
        conforms=True
    else:
        conforms=False
    measurements=request.json['measurements']
    notes=request.json['notes']
    inserted_item_id_uncut=request.json['inserted_item_id']
    inserted_item_id = inserted_item_id_uncut.split('_')[1]
    pulled=checklists.find_one_and_update({"checklist_name":checklist_name}, {'$pull': {"checklist_items": {"inserted_item_id":inserted_item_id}}})
    print pulled
    pushed=checklists.find_one_and_update({"checklist_name":checklist_name}, {'$push': {"checklist_items": {"inserted_item_id":inserted_item_id, "conforms":conforms, "measurements":measurements, "notes":notes}}}) 
    print pushed   
    return json.dumps({'data': {'checklist_name':checklist_name, 'conforms':conforms, 'measurements':measurements, 'notes':notes, "inserted_item_id":inserted_item_id}})

@app.route('/showTest',methods=['GET','POST'])
def showTest():
    d = request.form.getlist('chklst').pop()
    c = checklists.find_one({"checklist_name":d})
    data = []
    for i in c["checklist_items"]:
        ADA_id=i['inserted_item_id']
        ADA_item=ADA_items.find_one({'_id': ObjectId(ADA_id)})
        conforms=i["conforms"]
        measurements=i["measurements"]
        notes=i["notes"]
        item_stats={"conforms":conforms, "measurements":measurements, "notes":notes}
        print ADA_item
        print item_stats
        data.append({"ADA_item":ADA_item,"item_stats":item_stats})
    session['checklist_name'] = d
    return render_template('checklist_template.html',checklist_name=d,data=data)

@app.route('/showChecklist',methods=['GET','POST'])
def showChecklist():
    return render_template('checklist_template.html')


@app.route('/getChecklists')
def getChecklists():
    checklist_names=[]
    checklist_cursor = checklists.find({})
    for c in checklist_cursor:
        checklist_names.append({c['checklist_name']:c['checklist_items']})
    print checklist_names
    return json.dumps(checklist_names)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
