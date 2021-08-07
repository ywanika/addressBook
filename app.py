from flask import Flask, render_template, redirect, request, flash, session
from flask_pymongo import PyMongo
import os
import re
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
from datetime import datetime

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
    PLACES_API= os.environ.get("PLACES_API"),
    TEST_EMAIL = os.environ.get("TEST_EMAIL")
)


mongo = PyMongo(app)

regex_email = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$' #for sever-side validation of email

#redirect http to https
@app.before_request
def before_request():
    if os.environ.get("DEPLOYMENT") == "vital-relation-production":
        if request.url.startswith("http://"):
            url = request.url.replace("http://", "https://", 1)
            code = 301
            return redirect(url, code = code)
        elif request.url.startswith("v"):
            url = request.url.replace("v", "https://v", 1)
            code = 301
            return redirect(url, code = code)
        elif "favicon" in request.url:
            return redirect("/")


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

            if bloodType not in possibleTypes:
                flash("Invalid Blood Type", "danger")
                return redirect ("/")

            for donorType in possibleTypes[bloodType]:
                donorTypes.append({"bloodType":donorType})
            
            name = ""
            people =  {}
            #persons = mongo.db.donors.find({"bloodType":bloodType, "zipcode": zipcode})
            persons = mongo.db.donors.aggregate([ {"$match": { "$or": donorTypes , "place": {"$regex": place}, "confirmed": True}}, {"$sample":{ "size": 10 }} ])
            if button == "Search Plasma Donors":
                persons = mongo.db.donors.aggregate([ {"$match":{"$or": donorTypes, "place": {"$regex": place}, "confirmed": True, "plasma": True}}, {"$sample":{ "size": 10 }} ])
            for person in persons:
                if "name" in person:
                    name = person["name"]
                people [person["_id"]] = [name, person["phone"], person["place"], person["bloodType"]]

            if people == {}:
                flash("No applicable donors near you", "warning")
            return render_template ("showData.html", people = people, places=app.config['PLACES_API'], searchedType = bloodType, searchedPlace = place, previousSearch = button)

        elif "searchAgain" in request.form:
            bloodType = request.form ["bloodType"]
            place = request.form ["place"].strip()
            previousSearch = ""
            if "previousSearch" in request.form:
                previousSearch = request.form ["previousSearch"]
            #use session["people_considered"] = [10 people]
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

            if bloodType not in possibleTypes:
                flash("Invalid Blood Type", "danger")
                return redirect ("/")

            for donorType in possibleTypes[bloodType]:
                donorTypes.append({"bloodType":donorType})
            
            name = ""
            people =  {}
            #persons = mongo.db.donors.find({"bloodType":bloodType, "zipcode": zipcode})
            persons = mongo.db.donors.aggregate([ {"$match": { "$or": donorTypes , "place": {"$regex": place}, "confirmed": True}}, {"$sample":{ "size": 10 }} ])
            if previousSearch == "Search Plasma Donors":
                persons = mongo.db.donors.aggregate([ {"$match":{"$or": donorTypes, "place": {"$regex": place}, "confirmed": True, "plasma": True}}, {"$sample":{ "size": 10 }} ])
            for person in persons:
                if "name" in person:
                    name = person["name"]
                people [person["_id"]] = [name, person["phone"], person["place"], person["bloodType"]]

            if people == {}:
                flash("No applicable donors near you", "warning")
            return render_template ("showData.html", people = people, places=app.config['PLACES_API'], searchedType = bloodType, searchedPlace = place, previousSearch = previousSearch)


@app.route("/add", methods= ["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template ("add.html", places=app.config['PLACES_API'])
    else:
        name = request.form ["name"].strip().lower()
        area_code = request.form ["area_code"].strip()
        if "+" in area_code:
            area_code= area_code.replace("+", "")
        phone = request.form ["phone"].strip()
        place = request.form ["place"].strip().lower()
        bloodType = request.form ["bloodType"]
        email = request.form ["email"].strip().lower()
        plasma = False
        if "plasma" in request.form:
            plasma = True
        if "TandC" in request.form:
            agree = True
        else:
            flash("Please agree to terms and conditions if you wish to register", "danger")
            return redirect ("/add")
        if (phone == "" or place == "" or bloodType == "" or area_code == "" or area_code == "+"):
            flash("Please fill in all fields", "danger")
            return redirect ("/add")
        elif not (re.search(regex_email, email)):
            flash("Please enter valid email", "danger")
            return redirect ("/add")
        elif not phone.isnumeric() or not area_code.isnumeric():
            flash("Please enter numeric values for phone number and area code", "danger")
            return redirect ("/add")
        elif place.count(",") != 2 or len(place) < 5:
            flash("Please enter your place in 'City, State, Country' format", "danger")
            return redirect ("/add")
        person = {"name":name, "phone": "+"+area_code+"-"+phone, "place": place, "bloodType": bloodType, "email": email, "confirmed": False, "agreed_TandC":agree, "plasma":plasma}
        mongo.db.donors.insert_one(person)

        domain = app.config['DOMAIN']
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        token = serializer.dumps(email, salt=app.config['SECURITY_PASS_SALT'])
        url = domain + "/email_verification?token=" + token
        
        if app.config["TEST_EMAIL"] is None:
            message = Mail(
                from_email=('support@vitalrelation.com', "Vital Relation Support"),
                to_emails= email,
                subject='Vital Relation - Account Confirmation',
                html_content= render_template("createUser_email.html", name = name.title(), phone = phone, place = place.title(), bloodType = bloodType, url = url))
            try:
                sg = SendGridAPIClient(app.config['SENDGRID_API'])
                response = sg.send(message)
                flash("Please check your inbox to confirm your account. Thank you!", "success")
            except Exception as e:
                print(e)

        else:
            message = Mail(
                from_email=('support@vitalrelation.com', "Vital Relation Support"),
                to_emails= app.config["TEST_EMAIL"],
                subject='Vital Relation - Account Confirmation',
                html_content= render_template("createUser_email.html", name = name.title(), phone = phone, place = place.title(), bloodType = bloodType, url = url))
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

@app.route("/feedback", methods = ["GET", "POST"])
def feedback():
    if request.method == "GET":
        return render_template ("feedback.html")
    else:
        email = request.form["email"].strip().lower()
        feedback = request.form["feedback"]
        if email != "":
            if not (re.search(regex_email, email)):
                flash("Please enter valid email", "danger")
                return redirect ("/feedback")
        mongo.db.feedback.insert_one({"email":email, "feedback":feedback, "time_updated":datetime.utcnow()})

        return redirect ("/feedback")

@app.route("/otherResources")
def otherResource():
    return render_template ("otherResources.html")

@app.errorhandler(404)
def page_not_found(error):
    flash("Page Not Found", "danger")
    return redirect("/")

@app.errorhandler(500)
def something_wrong(error):
    flash("Something Went Wrong", "danger")
    return redirect("/")

if __name__ == "__main__":
    app.run(debug= True)


"""up to 3 sarch agains, after have to wait 10 min, info icon, +1/+91 🆗, have ppl check spam (what if I didn't get the email), get it out, testing, promote to production, contact us, save info on add - javascript, about page, confrim email"""
#remove debug
"""make the email prettier, vaccination info"""
"""confirm email to delete user"""
"""profanity fileter, combine search again + main search funtionalities, display feedback = flask moment"""