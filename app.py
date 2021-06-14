from flask import Flask, render_template, redirect, request, flash, session
from flask_pymongo import PyMongo
import os
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv

# loading environment from .env file
app_path = os.path.join(os.path.dirname(__file__), '.')
dotenv_path = os.path.join(app_path, '.env')
load_dotenv(dotenv_path)

app = Flask (__name__)

app.config.update(
    MONGO_URI= os.environ.get("MONGO_URI"),
    SECRET_KEY= os.environ.get("SECRET_KEY"),
    SENDGRID_API= os.environ.get("SENDGRID_API"),
    DOMAIN= os.environ.get("DOMAIN"),
    SECURITY_PASS_SALT= os.environ.get("SECURITY_PASS_SALT"),
    PLACES_API= os.environ.get("PLACES_API")
)


mongo = PyMongo(app)

regex_email = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$' #for sever-side validation of email


@app.route("/", methods= ["GET", "POST"])
def showData():
    if request.method == "GET":
        return render_template ("showData.html", people={}, places=app.config['PLACES_API'], searchedType = "Pick Option Below...")
    else:
        if "button" in request.form:
            bloodType = request.form ["bloodType"]
            place = request.form ["place"].strip().lower()
            button = request.form["button"]

            if (bloodType == "" or place == ""):
                flash("Please fill in all fields", "danger")
                return redirect ("/")

            possibleTypes={"AB+":["O-", "O+", "B-", "B+", "A-", "A+", "AB-", "AB+"],
            "AB-":["O-", "B-", "A-", "AB-"],
            "A+":["O-", "O+", "A-", "A+"],
            "A-":["O-", "A-"],
            "B+":["O-", "O+", "B-", "B+"],
            "B-":["O-", "B-"],
            "O+":["O-", "O+"],
            "O-":["O-"]}
            donorTypes=[]
            for donorType in possibleTypes[bloodType]:
                donorTypes.append({"bloodType":donorType})
                #db.inventory.find( { $or: [ { quantity: 20 } , { price: 10 } ] } )
            
            name = ""
            people =  {}
            #persons = mongo.db.donors.find({"bloodType":bloodType, "zipcode": zipcode})
            persons = mongo.db.donors.aggregate([ {"$match": { "$or": donorTypes , "place": {"$in":[place]}, "confirmed": True}}, {"$sample":{ "size": 10 }} ])
            if button == "Search Plasma Donors":
                persons = mongo.db.donors.aggregate([ {"$match":{"$or": donorTypes, "place": {"$in":[place]}, "confirmed": True, "plasma": True}}, {"$sample":{ "size": 10 }} ])
            #print(persons)
            for person in persons:
                if "name" in person:
                    name = person["name"]
                people [person["_id"]] = [name, person["phone"], person["place"], person["bloodType"]]
                #print (person, people)"""

            if people == {}:
                flash("No applicable donors near you", "warning")
            return render_template ("showData.html", people = people, places=app.config['PLACES_API'], searchedType = bloodType, searchedPlace = place)

        elif "searchAgain" in request.form:
            bloodType = request.form ["bloodType"]
            place = request.form ["place"].strip()
            #use session["people_considered"] = [10 people]
            return request.form


@app.route("/add", methods= ["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template ("add.html", places=app.config['PLACES_API'])
    else:
        name = request.form ["name"].strip().lower()
        phone = request.form ["phone"].strip()
        place = request.form ["place"].strip().lower()
        bloodType = request.form ["bloodType"]
        email = request.form ["email"].strip().lower()
        plasma = False
        if "plasma" in request.form:
            plasma = True
        if "TandC" in request.form:
            agree = True
            #print (agree)
        else:
            flash("Please agree to terms and conditions if you wish to register", "danger")
            return redirect ("/add")
        if (phone == "" or place == "" or bloodType == ""):
            flash("Please fill in all fields", "danger")
            return redirect ("/add")
        elif not (re.search(regex_email, email)):
            flash("Please enter valid email", "danger")
            return redirect ("/add")
        elif not ( phone.isnumeric() ):
            flash("Please enter numeric values for phone", "danger")
            return redirect ("/add")
        elif place.count(",") < 2:
            flash("Please enter your place in 'City, State, Country' format", "danger")
            return redirect ("/add")
        person = {"name":name, "phone": phone, "place": place, "bloodType": bloodType, "email": email, "confirmed": False, "agreed_TandC":agree, "plasma":plasma}
        #print (person)
        mongo.db.donors.insert_one(person)

        domain = app.config['DOMAIN']
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        #print ("hi",domain, email)
        token = serializer.dumps(email, salt=app.config['SECURITY_PASS_SALT'])
        #print ("hello",token)
        url = domain + "/email_verification?token=" + token
        
        message = Mail(
            from_email='support@vitalrelation.com',
            to_emails= "ankagugu@gmail.com",
            subject='Vital Relation - Account Confirmation',
            html_content= render_template("createUser_email.html", name = name.title(), phone = phone, place = place, bloodType = bloodType, url = url))
        try:
            sg = SendGridAPIClient(app.config['SENDGRID_API'])
            response = sg.send(message)
            flash("Please check your inbox to confirm your account. Thank you!", "success")
        except Exception as e:
            print(e)
        return redirect ("/")


@app.route("/email_verification")
def email_verification():
    token = request.args.get("token")
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=app.config['SECURITY_PASS_SALT'], max_age = (45*60))
        mongo.db.donors.update_one({"email":email}, {"$set":{"confirmed":True}})
        flash ("Your account has been confirmed! Thank you!", "success")
    except:
        flash("It seems this link has expired", "warning")
    return redirect("/")


@app.route("/deleteUser", methods= ["GET", "POST"])
def deleteUser():
    if request.method == "GET":
        return render_template ("deleteUser.html")
    else:
        name = request.form ["name"].strip()
        phone = request.form ["phone"].strip()
        person = mongo.db.donors.find_one({"name":name, "phone": phone})
        if person != None:
            mongo.db.donors.delete_one({"name":name, "phone": phone})
            flash( name+" removed !", "success")
            return redirect ("/")
        flash("didn't work", "warning")
        return redirect ("/deleteUser")

@app.route("/otherResources")
def otherResource():
    return render_template ("otherResources.html")

@app.route("/autoAddData")
def autoAddData():
    for x in range (5):
        person = {"name":"TEST", "phone": "123"+str(x), "place": "0010", "bloodType": "A+","email": "test"+str(x)+"@anika.com", "confirmed": True }
        #print (person)
        mongo.db.donors.insert_one(person)
    for x in range (5):
        person = {"name":"TEST", "phone": "122"+str(x), "place": "0011", "bloodType": "A-","email": "test1"+str(x)+"@anika.com", "confirmed": True }
        #print (person)
        mongo.db.donors.insert_one(person)
    for x in range (5):
        person = {"name":"TEST", "phone": "121"+str(x), "place": "0009", "bloodType": "O-","email": "test2"+str(x)+"@anika.com", "confirmed": True }
        #print (person)
        mongo.db.donors.insert_one(person)
    flash("Added! Thank you!", "success")
    return redirect ("/")


if __name__ == "__main__":
    app.run(debug=True)


"""up to 3 sarch agains, after have to wait 10 min, info icon, contains/in in mongo($in), city/state/country validation java, type of phone # (area code, adding the +1/+91), have ppl check spam (what if I didn't get the email), """
#remove debug, change recieving email
"""make the email prettier, vaccination info"""
"""confirm email to delete user"""
"""dlib library"""

"""https://covidwin.in/               Tracking availability of many types of Covid related resources.
https://covid19-twitter.in/    Twitter query generator which finds info from Twitter.
https://covid19.neera.ai/      Provides beds information
https://covidfightclub.org/   Lists Covid resource availability with phone numbers."""