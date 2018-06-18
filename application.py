import os
import sys
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify, g
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp
from werkzeug.utils import secure_filename
from pygeocoder import Geocoder
from helpers import *
import smtplib

UPLOAD_FOLDER = 'static/image'

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
# Check for Host constant
HOST = 'Host'

DATABASE = 'model.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args = (), one = False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv




# configure application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Homepage
@app.route("/")
def index():
    cur = get_db()
    if session.get("user_id") is None:

        detail = query_db("SELECT Property.name, Property.desc, Image.url FROM Property JOIN Image ON Property.property_id = Image.property_id WHERE Image.view = 'Ext'")
        return render_template("index.html", property = detail)
        return render_template("auth/register.html")
    else:
        id = session["user_id"]
        name = query_db("SELECT first, type FROM Registrant WHERE id = ?", [id], one = True)
        detail = query_db("SELECT Property.name, Property.desc, Image.url FROM Property JOIN Image ON Property.property_id = Image.property_id WHERE Image.view = 'Ext'")

        return render_template("index.html", property = detail, name = name[0])




# Register guest user
@app.route("/register", methods = ["GET", "POST"])
def register():
    cur = get_db()
    if request.method == "GET":
        return render_template("auth/register.html")
    elif request.method == "POST":
        # Validate user input - back-up incase javascript is turned off
        if not request.form.get("password") or not request.form.get("email") or not request.form.get("first") or not request.form.get("last"):
            return render_template("resp/error.html")
        email = request.form.get("email")

        # check that username doesn't already exist
        namecheck = query_db("SELECT email FROM Registrant WHERE email = ?", [email], one = True)
        print("Query_db success")

        if not namecheck:
            cur.execute("INSERT INTO Registrant (hash, email, first, last, type) Values(:hash, :email, :first, :last, :type)", {"hash": pwd_context.hash(request.form.get("password")), "email": email, "first": request.form.get("first"), "last": request.form.get("last"), "type": "Guest"})
            cur.commit()
            print("Success")
        else:
            return render_template("resp/error.html")
        # Log in user
        user = query_db("SELECT * FROM Registrant WHERE email = ?", [email], one = True)

        # close database connection
        session["user_id"] = user[0]
        email = user[2]
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login("beyondbnbinn@gmail.com", "meadowridge")
        server.sendmail("beyondbnbinn@gmail.com", email, "Thanks for registering")
        return redirect(url_for("regConfirm"))

# Host Property registration route. signs up a new host and their property
@app.route("/host", methods=["GET", "POST"])
def host():
    cur = get_db()
    if request.method == "GET":
        return render_template("auth/host.html")
    elif request.method == "POST":
        # Validate user information for Registrant table
        if not request.form.get("password") or not request.form.get("email") or not request.form.get("first") or not request.form.get("last"):
            return render_template("resp/error.html")
        if not request.form.get("propname") or not request.form.get("address") or not request.form.get("zipcode"):
            return render_template("resp/error.html")
        email = request.form.get("email")
        cur.execute("INSERT INTO Registrant (hash, email, first, last, type) Values(:hash, :email, :first, :last, :type)", {"hash": pwd_context.hash(request.form.get("password")), "email": email, "first": request.form.get("first"), "last": request.form.get("last"), "type": "Host"})
        cur.commit()
        print("INSERT success")
        host_id = query_db("SELECT * FROM Registrant WHERE email = ?", [email], one = True)
        # Generate geocoordinates for property's address - to be used with googlemaps on details page
        street = request.form.get("address")
        zip = request.form.get("zipcode")
        addr = ", ".join([street, zip])
        value = Geocoder('AIzaSyA_8dKMvm9l98sJMLFv-G6eV7K3vUPUat0').geocode(addr)
        coords = value[0].coordinates
        lat = coords[0]
        lng = coords[1]

        cur.execute("INSERT INTO Property (name, address, zip, desc, owner_id, lat, lng) Values(:name, :address, :zip, :desc, :owner_id, :lat, :lng)", {"name": request.form.get("propname"), "address": street, "zip": zip, "desc": request.form.get("desc"), "owner_id": host_id[0], "lat": lat, "lng": lng})
        cur.commit()
        print("INSERT success")
        # Log in user
        # Assign session variables to user
        session["user_id"] = host_id[0]
        session["type"] = host_id[5]
        session["name"] = request.form.get("propname")
        # Continue user to next section of property registration: Cover photo upload
        return render_template("upload_file.html")

# Display user registration confirmation page
@app.route("/regConfirm")
def regConfirm():
    if request.method == "GET":
        return render_template("resp/regConfirm.html")

# Display Booking Confirmation page
@app.route("/bookingConfirm")
def bookingConfirm():
    if request.method == "GET":
        return render_template("resp/bookingConfirm.html")

# Success landing page
@app.route("/roomConfirm")
def roomConfirm():
        return render_template("resp/roomConfirm.html")

# Success landing page
@app.route("/success")
def success():
        return render_template("resp/success.html")

# Host Log In route - Logs in Host user and displays "Host" Homepage
@app.route("/hostlogin", methods = ['GET', 'POST'])
def hostlogin():
    cur = get_db()
    # clear any users who are logged in
    session.clear()
    if request.method == 'GET':
        return render_template("auth/hostlogin.html")
    elif request.method == 'POST':
        # Validate user input
        if not request.form.get("email") or not request.form.get("password"):
            return render_template("resp/error.html")
        email = request.form.get("email")
        user = query_db("SELECT Registrant.id, Registrant.hash, Registrant.type, Property.name FROM Registrant JOIN Property ON Registrant.id = Property.owner_id WHERE Registrant.email = :email AND Registrant.type = :type", {"email": email, "type": "Host"}, one = True)
        if not user:
            return render_template("resp/error.html")
        if not pwd_context.verify(request.form.get("password"), user[1]):
            return render_template("resp/error.html")
        # If user exists and passwords match, log in the user
        session["user_id"] = user[0]
        session["type"] = user[2]
        session["name"] = user[3]
        return redirect(url_for("index"))

# Login route
@app.route("/login", methods = ["GET", "POST"])
def login():
    cur = get_db()
    # clear any users who are logged in
    session.clear()
    if request.method == "GET":
        return render_template("auth/login.html")
    elif request.method == "POST":
        # Validate user input
        if not request.form.get("email") or not request.form.get("password"):
            return render_template("resp/error.html")
        email = request.form.get("email")

        user = query_db("SELECT * FROM Registrant WHERE email = ?", [email], one = True)
        # if user doesn't exist, return error page
        if not user:
            return render_template("resp/error.html")
        if not pwd_context.verify(request.form.get("password"), user[1]):
            return render_template("resp/error.html")
        # If user exists and passwords match, log in the user
        session["user_id"] = user[0]
        return redirect(url_for("index"))

# Logout route
@app.route("/logout")
@login_required
def logout():
    # Log out user
    # forget any user_id
    session.clear()
    return redirect(url_for("index"))

# Host Homepage and access to tools
@app.route("/hostTools")
@login_required
def hostTools():
    cur = get_db()
    id = session["user_id"]
    detail = query_db("SELECT Property.name, Property.property_id, Image.url FROM Property JOIN Image ON Property.property_id = Image.property_id WHERE Property.owner_id = ?", [id])
    reservation = query_db("SELECT Calendar.event_id, Calendar.check_in, Calendar.check_out, Calendar.room, Calendar.guests, Registrant.email, Registrant.first, Registrant.last FROM Calendar JOIN Registrant ON Calendar.guest_id = Registrant.id WHERE Calendar.property_id = ?", [detail[0][1]])
    return render_template("hostTools.html", details = detail, reservations = reservation)

# Image Uploading Routes - runs after Host Registration
# Define the allowed type of file for image upload
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route for uploading an image
@app.route("/upload_file", methods=['GET', 'POST'])
@login_required
def upload_file():
    cur = get_db()
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # filename = "/".join(["image", filename])
            property_id = query_db("SELECT property_id FROM Property WHERE name = ?", [session["name"]], one = True)
            cur.execute("INSERT INTO Image (property_id, url, view) Values(:property_id, :filename, :view)", {"property_id": int(property_id[0]), "filename": "/".join(["image", filename]), "view": "Ext"})
            cur.commit()
            print("INSERT success")
            return redirect(url_for("roomConfirm"))
    return render_template("upload_file.html", home = session["name"])

# Route for uploading an image
@app.route("/upload_interior", methods=['GET', 'POST'])
def upload_interior():
    cur = get_db()
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # filename = "/".join(["image", filename])
            property_id = query_db("SELECT property_id FROM Property WHERE name = ?", [session["name"]], one = True)
            cur.execute("INSERT INTO Image (property_id, url, view) Values(:property_id, :filename, :view)", {"property_id": int(property_id[0]), "filename": "/".join(["image", filename]), "view": "Int"})
            cur.commit()
            print("INSERT success")
            return redirect(url_for("roomConfirm"))
    return render_template("upload_interior.html", home = session["name"])

# Display a property's room's and let user select booking dates. Displays map of location
# Details URL is built using <home> which is the property's name
@app.route("/details/<home>", methods = ["GET", "POST"])
def details(home):
    cur = get_db()
    if request.method == "GET":
        property_id = query_db("SELECT * FROM Property WHERE name = ?", [home], one = True)
        rooms = query_db("SELECT * FROM Room WHERE property_id = ?", [property_id[0]])
        image = query_db("SELECT url FROM Image WHERE property_id = ? AND view = 'Int'", [property_id[0]])
        return render_template("details.html", home = home, rooms = rooms, images = image, lat = property_id[6], lng = property_id[7])
    elif request.method == "POST":
        # Validate user input
        if not request.form.get("checkin") or not request.form.get("checkout") or not request.form.get("room"):
            return render_template("resp/error.html")
        checkin = request.form.get("checkin")
        checkout = request.form.get("checkout")
        room = request.form.get("room")
        #prop_id = db.execute("SELECT property_id FROM Property WHERE name = :home", home = home)
        #booking = db.execute("SELECT check_in, check_out FROM Calendar WHERE property = :prop_id AND room = :room AND check_in = :check_in AND check_out = :check_out", prop_id = prop_id[0]["property_id"], room = room, check_in = checkin, check_out = checkout)
        check_booking = query_db("SELECT Property.name, Calendar.check_in, Calendar.check_out, Calendar.room FROM Property JOIN Calendar ON Property.property_id = Calendar.property_id WHERE Property.name = ? AND Calendar.room = ? AND Calendar.check_in = ? AND Calendar.check_out = ?", [home, room, checkin, checkout], one = True)
        if not check_booking:
            #if session.get("user_id") is None:
            return redirect(url_for("booking", home = home, checkin = checkin, checkout = checkout, room = room))
            #else:
                #id = session["user_id"]
                #cur.execute("INSERT INTO Calendar (check_in, check_out, property_id, room, guests, guest_id) Values(:checkin, :checkout, :home, :room, :guests, :guest_id)", {"checkin": checkin, "checkout": checkout, "home": home, "room": room, "guests": 1, "guest_id": id})
                #cur.commit()
                #return render_template("resp/bookingConfirm.html")
        else:
            return render_template("resp/unavailable.html", home = home)

# Register property rooms, indicate Room name, max # of guests, room rate
@app.route("/room", methods = ['GET', 'POST'])
def room():
    cur = get_db()
    id = session["user_id"]
    if request.method == 'GET':
        # TODO after Host registers, log them in
        # use session["user_id"] to get property ID / name
        return render_template("room.html")
    elif request.method == 'POST':
        # Validate user's input
        if not request.form.get("room_name") or not request.form.get("rate") or not request.form.get("max"):
            return render_template("resp/error.html")
        property_id = query_db("SELECT property_id FROM Property WHERE owner_id = ?", [id], one = True)
        cur.execute("INSERT INTO Room (property_id, room_name, rate, max_occupancy) Values (:property_id, :room_name, :rate, :max_occupancy)", {"property_id": int(property_id[0]), "room_name": request.form.get("room_name"), "rate": int(request.form.get("rate")), "max_occupancy": int(request.form.get("max"))})
        cur.commit()
        return redirect(url_for("upload_interior"))

# Check Calendar database for booking availability
@app.route("/check_calendar/<home>")
def check_calendar(home):
    cur = get_db()
    room_name = request.args.get('room_name')
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    if not check_in or not check_out:
        return jsonify(result = "Not Available")

    property_id = query_db("SELECT property_id FROM Property WHERE name = ?", [home], one = True)
    calcheck = query_db("SELECT * FROM Calendar WHERE room = :room AND property_id = :property AND check_in = :check_in AND check_out = :check_out", {"room": room_name, "property": property_id[0], "check_in": check_in, "check_out": check_out})
    if not calcheck:
        return jsonify(result = "Available")
    else:
        return jsonify(result = "Not Available")

# User books a room, displays web form for signing up if its a new user
@app.route("/booking/<home>/<checkin>/<checkout>/<room>", methods = ["GET", "POST"])
def booking(home, checkin, checkout, room):
    cur = get_db()
    if request.method == "GET":
        return render_template("booking.html", home = home, checkin = checkin, checkout = checkout, room = room)
    elif request.method == "POST":
        if session.get("user_id") is None:
            if not request.form.get("email"):
                return render_template("resp/error.html")
            email = request.form.get("email")
            hash=pwd_context.hash(request.form.get("password"))
            cur.execute("INSERT INTO Registrant (hash, email, first, last, type) Values(:hash, :email, :first, :last, :type)", {"hash": pwd_context.hash(request.form.get("password")), "email": email, "first": request.form.get("first"), "last": request.form.get("last"), "type": "Guest"})
            cur.commit()
            property = query_db("SELECT property_id FROM Property WHERE name = :home", [home], one = True)
            guest = query_db("SELECT id FROM Registrant WHERE email = :email", [email], one = True)
            cur.execute("INSERT INTO Calendar (check_in, check_out, property_id, room, guests, guest_id) Values(:checkin, :checkout, :home, :room, :guests, :guest_id)", {"checkin": checkin, "checkout": checkout, "home": property[0], "room": room, "guests": int(request.form.get("guest")), "guest_id": guest[0]})
            cur.commit()
            email = request.form.get("resp/email")
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login("beyondbnbinn@gmail.com", "meadowridge")
            server.sendmail("beyondbnbinn@gmail.com", email, "Thank you for registering and booking a stay.")
            return redirect(url_for("regConfirm"))
        else:
            id = session["user_id"]
            property = query_db("SELECT property_id FROM Property WHERE name = :home", [home], one = True)
            guest = query_db("SELECT id FROM Registrant WHERE id = :id", [id], one = True)
            cur.execute("INSERT INTO Calendar (check_in, check_out, property_id, room, guests, guest_id) Values(:checkin, :checkout, :property_id, :room, :guests, :guest_id)", {"checkin": checkin, "checkout": checkout, "property_id": property[0], "room": room, "guests": int(request.form.get("guest")), "guest_id": guest[0]})
            cur.commit()
            return redirect(url_for("bookingConfirm"))

# Show upcoming bookings for a user
@app.route("/itinerary")
@login_required
def itinerary():
    cur = get_db()
    id = session["user_id"]
    # select user's upcoming history from Calendar table
    entry = query_db("SELECT Calendar.check_in, Calendar.check_out, Calendar.room, Calendar.guests, Property.name FROM Calendar JOIN Property ON Calendar.property_id = Property.property_id WHERE Calendar.guest_id = :id AND Calendar.check_in > date('now')", [id])
    return render_template("itinerary.html", itinerary = entry)

