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

@app.route("/add", methods= ["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template ("add.html")
    else:
        name = request.form ["name"]
        phone = request.form ["phone"]
        zipcode = request.form ["zipcode"]
        bloodType = request.form ["bloodType"]
        email = request.form ["email"]
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

@app.route("/", methods= ["GET", "POST"])
def showData():
    if request.method == "GET":
        return render_template ("showData.html", people={})
    else:
        bloodType = request.form ["bloodType"]
        zipcode = request.form ["zipcode"]
        name = ""
        #persons = mongo.db.newrecords.find({"bloodType":bloodType, "zipcode": zipcode})
        persons = mongo.db.newrecords.aggregate([ {"$match":{"bloodType":bloodType, "zipcode": zipcode}}, {"$sample":{ "size": 10 }} ])
        print(persons)
        people =  {}
        for person in persons:
            if "name" in person:
                name = person["name"]
            people [person["_id"]] = [name, person["phone"], person["zipcode"], person["bloodType"]]
            #print (person, people)"""
        if people == {}:
            flash("No applicable donors near you ", "warning")
        return render_template ("showData.html", people = people)

@app.route("/changeData", methods= ["GET", "POST"])
def changeData():
    if request.method == "GET":
        return render_template ("changeData.html")
    else:
        f_name = request.form ["f_name"]
        l_name = request.form ["l_name"]
        dob = request.form ["dob"]
        phone = request.form ["phone"]
        person = mongo.db.newrecords.find_one({"f_name":f_name, "l_name":l_name, "dob":dob,})
        #print (person)
        if person != None:
            mongo.db.newrecords.update_one({"f_name":f_name, "l_name":l_name, "dob":dob}, {"$set":{"phone":phone}})
            flash("Updated!", "success")
            return redirect ("/")
        flash("didn't work", "warning")
        return redirect ("/changeData")

@app.route("/deleteUser", methods= ["GET", "POST"])
def deleteUser():
    if request.method == "GET":
        return render_template ("deleteUser.html")
    else:
        f_name = request.form ["f_name"]
        l_name = request.form ["l_name"]
        dob = request.form ["dob"]
        person = mongo.db.newrecords.find_one({"f_name":f_name, "l_name":l_name, "dob":dob,})
        #print (person)
        if person != None:
            mongo.db.newrecords.delete_one({"f_name":f_name, "l_name":l_name, "dob":dob})
            flash( f_name+" removed !", "success")
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


"""geotagging, enter in zipcode, all they see is phone + psuedo-name, check nearest zip codes to fill in 10, search again to get 10, up to 3 sarch agains, after have to wait 10 min, OTP (verification) to register & remove, email for identifier, senf proof of registration to email - sendgrid, info icon, one blood type can donate to others"""