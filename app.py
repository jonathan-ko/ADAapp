from flask import Flask, render_template, request, redirect, session
import pymongo
from pymongo import MongoClient
import json
	
from werkzeug import generate_password_hash, check_password_hash

app = Flask(__name__)
Client = MongoClient()
db = Client.WACDA
users = db.users
contacts = db.contacts
access = db.access
places = db.places

app.secret_key = 'why would I tell you my secret key?'

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

@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return render_template('error.html',error = 'Unauthorized Access')

@app.route('/showClients')
def getClientList():
    return render_template('clients.html')

@app.route('/addClient', methods=['POST'])
def addClient():
    try:
        if session.get('user'):
            email = session.get('user')
            user_obj=users.find_one({"email":email})
            user_id=user_obj._id
            print user_id

            # read the posted values from the UI
            last_name = request.form['inputLastName']
            first_name = request.form['inputFirstName']
            address = request.form['inputAddress']
            city = request.form['inputCity']
            zipcode = request.form['inputZipCode']
            notes = request.form['inputNotes']
            contacts.insert_one({"last_name":last_name, "first_name":first_name, "address":address, "city":city, "zipcode":zipcode, "notes":notes, "user_id":user_id})
            return redirect('/showClients')
        else:
            return redirect('signin.html')
    except:
        return render_template('error.html', error = str(e))

@app.route('/getClient')
def getClient():
    if session.get('user'):
        email = session.get('user')
        user_obj=users.find_one({"email":email})
        print user_obj        
        user_id=user_obj['_id']            
        print user_id
        return json.dumps({"data":str(user_id)})
    else:
        return render_template('error.html', error = 'Unauthorized Access')


@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/')


@app.route("/testDash")
def testDash():
    return render_template('testDash.html')

@app.route('/getClients')
def getClients():
    try:
        email = session['user']
        print clients
        clients_dict = []
        for client in clients:
            print client
            client_dict = {
                'client_id': client[0],
                'client_LastName': client[1],
                'client_FirstName': client[2],
                'client_Address': client[3],
                'client_City': client[4],
                'client_Zipcode': client[5],
                'client_Notes': client[6],
                'client_user_id': client[7],
                'client_email': client[8],
                'client_caseStatus': client[9],
                'client_casType': client[10]
            }
            clients_dict.append(client_dict)
        return json.dumps(clients_dict)
    except Exception as e:
        return render_template('error.html', error = str(e))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
