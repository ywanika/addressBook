from flask import Flask, render_template, redirect, request, flash, session
from flask_pymongo import PyMongo
import os

app = Flask (__name__)
app.config["SECRET_KEY"] = "jjjj"
if os.environ.get("MONGO_URI") == None :
    file = open("connection_string.txt","r")
    connection_string = file.read().strip()
    app.config['MONGO_URI']=connection_string
else:
    app.config['MONGO_URI']= os.environ.get("MONGO_URI")

mongo = PyMongo(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add", methods= ["GET", "POST"])
def add():
    if request.method == "GET":
        return render_template ("add.html")
    else:
        f_name = request.form ["f_name"]
        l_name = request.form ["l_name"]
        phone = request.form ["phone"]
        bloodType = request.form ["bloodType"]
        dob = request.form ["dob"]
        person = {"f_name":f_name, "l_name": l_name, "phone": phone, "bloodType": bloodType, "dob": dob,}
        print (person)
        mongo.db.newrecords.insert_one(person)
        flash("Added! Thank you!", "success")
        return redirect ("/")

@app.route("/showData", methods= ["GET", "POST"])
def showData():
    if request.method == "GET":
        persons = mongo.db.newrecords.aggregate([{ "$sample": { "size": 10 } }])
        people =  {}
        for person in persons:
            people [person["f_name"]] = [person["f_name"], person["l_name"], person["phone"], person["dob"], person["bloodType"]]
            print (person, people)
        return render_template ("showData.html", people = people)
    else:
        bloodType = request.form ["bloodType"]
        persons = mongo.db.newrecords.find({"bloodType":bloodType})
        people =  {}
        for person in persons:
            people [person["f_name"]] = [person["f_name"], person["l_name"], person["phone"], person["dob"], person["bloodType"]]
            print (person, people)
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
        print (person)
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
        print (person)
        if person != None:
            mongo.db.newrecords.delete_one({"f_name":f_name, "l_name":l_name, "dob":dob})
            flash( f_name+" removed !", "success")
            return redirect ("/")
        flash("didn't work", "warning")
        return redirect ("/deleteUser")

if __name__ == "__main__":
    app.run()
