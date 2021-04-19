from flask import Flask, render_template, redirect, request, flash, session
from flask_pymongo import PyMongo
import os
import re

app = Flask (__name__)
app.config["SECRET_KEY"] = "jjjj"
if os.environ.get("MONGO_URI") == None :
    file = open("connection_string.txt","r")
    connection_string = file.read().strip()
    app.config['MONGO_URI']=connection_string
else:
    app.config['MONGO_URI']= os.environ.get("MONGO_URI")

mongo = PyMongo(app)

regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$' #for sever-side validation of email


@app.route("/", methods= ["GET", "POST"])
def showData():
    if request.method == "GET":
        return render_template ("showData.html", people={})
    else:
        bloodType = request.form ["bloodType"]
        zipcode = request.form ["zipcode"].strip()
        if not zipcode.isnumeric():
            flash("zipcode must be numeric", "warning")
            return redirect ("/")
        #make sure to retain leading zeros in zip when adding and subtracting 1
        lenZip = len(zipcode)
        searchZipcodeUP = ( str( int(zipcode) + 1 ) ).zfill(lenZip)
        searchZipcodeDOWN = ( str( int(zipcode) - 1 ) ).zfill(lenZip)
        
        name = ""
        people =  {}
        #persons = mongo.db.newrecords.find({"bloodType":bloodType, "zipcode": zipcode})
        persons = mongo.db.newrecords.aggregate([ {"$match":{"bloodType":bloodType, "zipcode": zipcode}}, {"$sample":{ "size": 10 }} ])
        #print(persons)
        for person in persons:
            if "name" in person:
                name = person["name"]
            people [person["_id"]] = [name, person["phone"], person["zipcode"], person["bloodType"]]
            #print (person, people)"""

        if len(people) < 10:
            persons = mongo.db.newrecords.aggregate([ {"$match":{"bloodType":bloodType, "zipcode": searchZipcodeUP}}, {"$sample":{ "size": 10 - len(people) }} ])
            for person in persons:
                if "name" in person:
                    name = person["name"]
                people [person["_id"]] = [name, person["phone"], person["zipcode"], person["bloodType"]]

        if len(people) < 10:
            persons = mongo.db.newrecords.aggregate([ {"$match":{"bloodType":bloodType, "zipcode": searchZipcodeDOWN}}, {"$sample":{ "size": 10 - len(people) }} ])
            for person in persons:
                if "name" in person:
                    name = person["name"]
                people [person["_id"]] = [name, person["phone"], person["zipcode"], person["bloodType"]]

        if people == {}:
            flash("No applicable donors near you", "warning")
        elif len(people) < 10:
            zipcodes = zipcode + ", " + searchZipcodeDOWN + ", " + searchZipcodeUP
            flash("Unable to find 10 donors in "+zipcodes, "warning")
        return render_template ("showData.html", people = people)


@app.route("/add", methods= ["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template ("add.html")
    else:
        name = request.form ["name"].strip()
        phone = request.form ["phone"].strip()
        zipcode = request.form ["zipcode"].strip()
        bloodType = request.form ["bloodType"]
        email = request.form ["email"].strip()
        if (phone == "" or zipcode == ""):
            flash("Please fill in all fields", "danger")
            return redirect ("/add")
        elif not (re.search(regex, email)):
            flash("Please enter valid email", "danger")
            return redirect ("/add")
        person = {"name":name, "phone": phone, "zipcode": zipcode, "bloodType": bloodType, "email": email}
        #print (person)
        mongo.db.newrecords.insert_one(person)
        flash("Added! Thank you!", "success")
        return redirect ("/")


@app.route("/deleteUser", methods= ["GET", "POST"])
def deleteUser():
    if request.method == "GET":
        return render_template ("deleteUser.html")
    else:
        name = request.form ["name"].strip()
        phone = request.form ["phone"].strip()
        person = mongo.db.newrecords.find_one({"name":name, "phone": phone})
        if person != None:
            mongo.db.newrecords.delete_one({"name":name, "phone": phone})
            flash( name+" removed !", "success")
            return redirect ("/")
        flash("didn't work", "warning")
        return redirect ("/deleteUser")


@app.route("/autoAddData")
def autoAddData():
    for x in range (10):
        person = {"name":"TEST", "phone": "1234", "zipcode": "0000", "bloodType": "A+"}
        #print (person)
        mongo.db.newrecords.insert_one(person)
    flash("Added! Thank you!", "success")
    return redirect ("/")


if __name__ == "__main__":
    app.run(debug=True)


""" enter in zipcode, all they see is phone + psuedo-name, check nearest zip codes to fill in 10, search again to get 10, up to 3 sarch agains, after have to wait 10 min, OTP (verification) to register & remove, email for identifier, senf proof of registration to email - sendgrid, info icon, one blood type can donate to others, show conditions of donating blood, check box to agree to terms&conditions, recorded that they agreed, removing by email, remember zeros in zipcode"""