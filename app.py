import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_pubs")
def get_pubs():
    pubs = list(mongo.db.pubs.find())
    return render_template("pubs.html", pubs=pubs)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    pubs = mongo.db.pubs.find({"$text": {"$search": query}})
    return render_template("pubs.html", pubs=pubs)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                        session["user"] = request.form.get("username").lower()
                        flash("Welcome, {}".format(
                            request.form.get("username")))
                        return redirect
                        (url_for("profile", username=session["user"]))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # grab the session user's username from db
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_pub", methods=["GET", "POST"])
def add_pub():
    if request.method == "POST":
        pub = {
            "pub_name": request.form.get("pub_name"),
            "location": request.form.get("location"),
            "date_of_visit": request.form.get("date_of_visit"),
            "beer_quality": request.form.get("beer_quality"),
            "food_available": request.form.get("food_available"),
            "dog_friendly": request.form.get("dog_friendly"),
            "comments": request.form.get("comments"),
            "created_by": session["user"]
        }
        mongo.db.pubs.insert_one(pub)
        flash("Pub Successfully Added")
        return redirect(url_for("add_pub"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_pub.html", categories=categories)


@app.route("/edit_pub/<pub_id>", methods=["GET", "POST"])
def edit_pub(pub_id):
    if request.method == "POST":
        submit = {
            "pub_name": request.form.get("pub_name"),
            "location": request.form.get("location"),
            "date_of_visit": request.form.get("date_of_visit"),
            "beer_quality": request.form.get("beer_quality"),
            "food_available": request.form.get("food_available"),
            "dog_friendly": request.form.get("dog_friendly"),
            "comments": request.form.get("comments"),
            "created_by": session["user"]
        }
        mongo.db.pubs.update({"_id": ObjectId(pub_id)}, submit)
        flash("Pub Successfully Updated")

    pub = mongo.db.pubs.find_one({"_id": ObjectId(pub_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_pub.html", pub=pub, categories=categories)


@app.route("/delete_pub/<pub_id>")
def delete_pub(pub_id):
    mongo.db.pubs.remove({"_id": ObjectId(pub_id)})
    flash("Pub Successfully Deleted")
    return redirect(url_for("get_pubs"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
