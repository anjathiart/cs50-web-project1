import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))




@app.route("/")
def index():
	if session:
		return render_template("index.html")
	return redirect(url_for("login"))
	

@app.route("/signup", methods=["GET","POST"])
def signup():
	"""signs up a user by inserting them into the db if validation succeeds"""
	if request.method != "POST":
		return render_template("signup.html")
	else:
		username = request.form.get("username")
		password = request.form.getlist("password")
		print(password)
		print (username)
		# check that all fields have been filled in
		if password ==  None or username == None:
			return render_template("signup.html", error_msg="Please enter all fields")

		# check that two passwords match
		if password[0] != password[1]:
			return render_template("signup.html", error_msg="Passwords do not match")

		# check that user does not already exist
		if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount != 0:
			return render_template("signup.html", error_msg="Username already taken")

		# TODO hash passwords
		password_hash = password[0]

		# insert user into database
		db.execute("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)",
	            {"username": username, "password_hash": password_hash})
		db.commit()

		# TODO: set the session id and redirect straight to the home page
		session["username"] = username
		session["user_id"] = db.execute("SELECT id FROM users WHERE username = :username", {"username": username}).fetchone()
		return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
	"""logs a user in and redirects to home page"""
	if request.method=="POST":
		username = request.form.get("username")
		password = request.form.get("username")

		if username == "" or not username or password == "" or  not password:
			return render_template("login.html", error_msg = "All fields are required")
		user = db.execute("SELECT * FROM users WHERE username=:username", {"username": username}).fetchone()
		if not user:
			return render_template("login.html", error_msg = "This username does not exist, try again or signup")
		# TODO: check that password matches decoded password hash in db
		if user.password_hash == password:
			session["user_id"] = user.id
			session["username"] = user.username

		return redirect(url_for("index"))

	return render_template("login.html")

@app.route("/logout")
def logout():
	"""clear the session and redirect to the login page"""
	session.clear()
	return redirect(url_for("index"))

@app.route("/search", methods=["POST"])
def search():
	search_text = request.form.get("search_text")
	if not search_text or search_text == "":
		render_template("index.html", error_msg="Search field is empty")
	#search_results = db.execute("SELECT * FROM books WHERE isbn LIKE :search_text OR title LIKE :search_text OR author LIKE :search_text", {"search_text": search_text}).fetchall()
	search_results = db.execute("SELECT * FROM books INNER JOIN authors ON books.author_id = authors.id WHERE isbn LIKE :search_text OR title LIKE :search_text OR name LIKE :search_text", {"search_text": '%' + str(search_text) + '%'}).fetchall()
	if search_results:
		print("we have results")
		return render_template("index.html", search_results=search_results)
	return render_template("index.html")

@app.route("/books/<int:book_id>")
def books(book_id):
	book_details = db.execute("SELECT * FROM books INNER JOIN authors ON books.author_id = authors.id WHERE books.id=:book_id", {"book_id": book_id}).fetchone()
	error_msg = request.args.get("error_msg")
	if book_details:
		# get any data from goodreads API
		goodreads_data = {}
		res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "vzDZyq1Qul7iugyOtRh0A", "isbns": book_details.isbn})
		if res.json()["books"][0]["reviews_count"]:
			print(res.json()["books"][0]["reviews_count"])
			goodreads_data["reviews_count"] = res.json()["books"][0]["reviews_count"]
			goodreads_data["average_score"] = res.json()["books"][0]["average_rating"]
			return render_template("books.html", book_details=book_details, goodreads_data=goodreads_data, error_msg=error_msg)
		else:
			return render_template("books.html", book_details=book_details, error_msg=error_msg)
	else:
		return redirect(url_for('search'), error_msg="something went wrong")


@app.route("/books/<int:book_id>/review", methods=["POST"])
def review(book_id):
	"""enters a new review for a particular book"""
	# check that the user has not reviewed this book yet
	print("x")
	print(session)
	res = db.execute("SELECT * FROM reviews WHERE user_id=:user_id AND book_id=:book_id", {"user_id": session["user_id"], "book_id": book_id}).fetchone()
	
	if res:
		return redirect(url_for('books', book_id=book_id, error_msg="You have already reviewed this book"))

	# insert review into database
	review = request.form.get("review")
	score = request.form.get("score")

	db.execute("INSERT INTO reviews(review, score, user_id, book_id) VALUES (:review, :score, :user_id, :book_id)", {"review": review, "score": int(score), "user_id": session["user_id"], "book_id": book_id })
	db.commit()



	









