from flask import Flask, render_template, request, redirect, session
from flask_pymongo import PyMongo
from pymongo import MongoClient
import json
	
from werkzeug import generate_password_hash, check_password_hash

app = Flask(__name__)
Client = MongoClient()
db = Client.WACDAdb
users = db.users

app.secret_key = 'why would I tell you my secret key?'


#mysql = MySQL()
	 
# MySQL configurations
#app.config['MYSQL_DATABASE_USER'] = 'oliver'
#app.config['MYSQL_DATABASE_PASSWORD'] = 'holmes'
#app.config['MYSQL_DATABASE_DB'] = 'contacts'
#app.config['MYSQL_DATABASE_HOST'] = 'localhost'
#mysql.init_app(app)


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
    Last_name = request.form['inputLastName']
    First_name = request.form['inputFirstName']
    email = request.form['inputEmail']
    password = request.form['inputPassword']
    # validate the received values
    if Last_name and First_name and email and password:
    	hashed_password = generate_password_hash(password)
        #conn = mysql.connect()
        #cursor = conn.cursor()
        #cursor.callproc('sp_createUser',(_name,_email,_hashed_password))
        #data = cursor.fetchall()
        #if len(data) is 0:
            #conn.commit()
        if users.count({"Email": email}) == 0:
            users.insert_one({"Last_name": Last_name, "First_name": First_name, "Email": email, "hashed_password": hashed_password})
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
        data = users.find_one({"Email":username})
        if check_password_hash(data['hashed_password'],password):
            session['user'] = data['Email']
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

@app.route('/clients')
def clients():
    return render_template('clients.html')

@app.route('/addClient', methods=['POST'])
def addClient():
    # read the posted values from the UI
    _LastName = request.form['inputLastName']
    _FirstName = request.form['inputFirstName']
    _Address = request.form['inputAddress']
    _City = request.form['inputCity']
    _ZipCode = request.form['inputZipCode']
    _Notes = request.form['inputNotes']
    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.callproc('sp_addClient',(_LastName,_FirstName,_Address,_City,_ZipCode,_Notes))
    data = cursor.fetchall()
    if len(data) is 0:
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/clients')
    else:
        cursor.close()
        conn.close()
        return render_template('error.html',error = 'An error occurred!')

@app.route('/getClient')
def getClient():
    try:
        if session.get('user'):
            _user = session.get('user')

            # Connect to MySQL and fetch data
            con = mysql.connect()
            cursor = con.cursor()
            cursor.callproc('sp_getClient')
            clients = cursor.fetchall()
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
                    'client_caseType': client[10]
                }
                clients_dict.append(client_dict)
            return json.dumps(clients_dict)
        else:
            return render_template('error.html', error = 'Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error = str(e))

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
        # Connect to MySQL and fetch data
        con = mysql.connect()
        cursor = con.cursor()
        cursor.callproc('sp_getClient')
        clients = cursor.fetchall()
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
