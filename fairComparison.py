#Fair Comparison
#Programmer : Yohann A Abittan 
#NetID : yaa243

from flask import Flask,render_template,request, redirect, url_for , session
import pymysql.cursors
import hashlib
import requests
import string
import json

app = Flask(__name__)

app.secret_key = 'A key that is oh so secret'

conn = pymysql.connect(host='127.0.0.1', user='root', password='root', db='FairComparison', charset='utf8mb4', port=3306, cursorclass=pymysql.cursors.DictCursor)

@app.route("/")

def home():
	return render_template("login.html", title="Welcome to the home page")

@app.route("/login", methods=['GET'])

def login():
	return render_template("login.html", title="Login")

@app.route("/register", methods=['GET'])

def register():
	return render_template("register.html", title="Sign up")

@app.route('/registerAuth', methods=['GET','POST'])

def registerAuth():
	username = request.form['username']
	password = request.form['password']

	password = hashlib.md5(password).hexdigest()

	cursor = conn.cursor()

	query = 'SELECT * FROM user WHERE username = %s'
	cursor.execute(query,(username))

	data = cursor.fetchone()

	if (data): 
		error = "This username is already in use"
		cursor.close()
		return render_template('register.html', error = error)
	else:
		ins = 'INSERT INTO user VALUES(NULL,%s,%s,NULL)'
		cursor.execute(ins,(username,password))
		conn.commit()
		cursor.close()
		return render_template('login.html', title="Sign up succeeded")

@app.route('/loginAuth', methods = ['GET','POST'])

def loginAuth():
	username = request.form['username']
	password = request.form['password']

	password = hashlib.md5(password).hexdigest()

	cursor = conn.cursor()

	query = 'SELECT * FROM user WHERE username =%s  and password =%s '
	cursor.execute(query, (username, password))
	
	data = cursor.fetchone()
	cursor.close()
	
	if(data):
		session['username'] = username 
		return redirect(url_for('homePage',title="successful login"))
	else:
		error = "The username and password combination is incorrect"
		return render_template('login.html',error = error)

@app.route('/homePage', methods=['GET'])

def homePage():

	username = session['username']

	return render_template('index.html')

@app.route('/getFares', methods = ['POST'])

def getFares():

	class Fare():
		typeOfCar = "none"
		fareE = "free"
		timeE = -1
		closeE = -1
		distance = -1


		def __init__(self, typeOfC, farE, timE, closE, distanc):
			self.typeOfCar = typeOfC
			self.fareE = farE 
			self.timeE = timE
			self.closeE = closE
			self.distance = distanc

	orig = request.values.get('start', None)#TEST
	dest = request.values.get('end', None)#TEST
	
	orig.replace(" ", "+")
	dest.replace(" ", "+")

	origJson=requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=AIzaSyClO36EMkegjq_u6jjE_xKqXCBvmJura3M' %orig)
	destJson=requests.get('https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=AIzaSyClO36EMkegjq_u6jjE_xKqXCBvmJura3M' %dest)

	origLngLat = origJson.json() #json.load(origJson)
	destLngLat = destJson.json() #json.load(destJson)

	print(origLngLat)

	origLng = origLngLat['results'][0]['geometry']['location']['lng']
	origLat = origLngLat['results'][0]['geometry']['location']['lat']

	destLng = destLngLat['results'][0]['geometry']['location']['lng']
	destLat = destLngLat['results'][0]['geometry']['location']['lat']


	print("origLng :")
	print(origLng)
	print("origLat :")
	print(origLat)
	print("destLng :")
	print(destLng)
	print("destLat :")
	print(destLat)

	headers = {
    'Authorization': 'Token KydIKwsREM-DO99fWQYGJswKBhvSK3D0gDQoBcDL',
    'Accept-Language': 'en_US',
    'Content-Type': 'application/json',
	}

	params = (
    ('start_latitude', '%s'%(origLat)), #('start_latitude', 'origLat')
    ('start_longitude', '%s'%(origLng)), #('start_longitude', 'origLng')
    ('end_latitude', '%s'%(destLat)), #('end_latitude', 'destLat')
    ('end_longitude', '%s'%(destLng)), #('end_longitude', 'destLng')
	)

	fareJson = requests.get('https://api.uber.com/v1.2/estimates/price', headers=headers, params=params)
	closestCarJson = requests.get('https://api.uber.com/v1.2/estimates/time', headers=headers, params=params)

	fare = fareJson.json()
	closestCar = closestCarJson.json()

	fareArray = []

	for i in range(0,len(fare["prices"])): #cycle through the types of ride and save their info in a new fare object
		
		typeOfRide = fare['prices'][i]['display_name']
		distance = fare['prices'][i]['distance']
		fareEstimate = fare['prices'][i]['estimate']
		timeEstimateSeconds = fare['prices'][i]['duration']
		timeEstimate = timeEstimateSeconds/60

		if i<len(closestCar["times"]):
			closestTimeSeconds = closestCar['times'][i]['estimate']
			closestTime = closestTimeSeconds/60

		fareArray.append(Fare(typeOfRide,fareEstimate,timeEstimate,closestTime,distance)) #add fare to array

	headers = {
    'Authorization': 'bearer +/AVw+e9uA3+cOlD2nGHgGvhTX5gOEilI8QB5oc0Lvc0YvsvuV5W2oE2M3uRmXLcR3Lm+ZMokYdSu6kgUctCzWaoIK0EYjJI7zpuB2Ois+wB0xBr+H0l77E=',
}

	params = (
    ('start_lat', '%s'%(origLat)),
    ('start_lng', '%s'%(origLng)),
    ('end_lat', '%s'%(destLat)),
    ('end_lng', '%s'%(destLng)),
)

	lyftJson = requests.get('https://api.lyft.com/v1/cost', headers=headers, params=params)
	lyft = lyftJson.json()

	print(lyft)

	lyftArray = []

	for i in range(0,len(lyft["cost_estimates"])):

		typeOfRide = lyft["cost_estimates"][i]['display_name']
		fareEstimateMaxCents = lyft["cost_estimates"][i]['estimated_cost_cents_max']
		fareEstimateMinCents = lyft["cost_estimates"][i]['estimated_cost_cents_min']
		fareEstimateMax =fareEstimateMaxCents/100
		fareEstimateMin = fareEstimateMinCents/100
		currency = lyft["cost_estimates"][i]["currency"]
		fareEstimate = str(fareEstimateMin)+"-"+str(fareEstimateMax)+currency
		timeEstimateSeconds = lyft["cost_estimates"][i]['estimated_duration_seconds']
		timeEstimate = timeEstimateSeconds/60
		surge = lyft["cost_estimates"][i]["primetime_percentage"]

		lyftArray.append(Fare(typeOfRide,fareEstimate,timeEstimate,surge,0)) #add fare to array


	taxiFare = 2.5+(0.4*5*distance)+(0.4*0.5*timeEstimate)
	taxiLow = taxiFare*0.85
	taxiLow = round(taxiLow,0)
	taxiHigh = taxiFare*1.15
	taxiHigh = round(taxiHigh,0)
	taxiEstimate = "%s-%s"%(taxiLow,taxiHigh)
	taxi = Fare("NYC taxi",taxiEstimate,timeEstimate,3,distance)

	for i in fareArray:
		print i.typeOfCar

	return render_template('index.html', fares = fareArray, lyft = lyftArray, taxi=taxi) #pass the array of fares


@app.route('/logout',methods=['GET'])

def logout():
	session.pop('username')
	return render_template('logout.html')

if __name__ == "__main__":
	app.run('127.0.0.1',5000, debug = True)

