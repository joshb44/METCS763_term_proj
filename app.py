import os
import json
import random
import openai
import sqlite3
from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

db_name = "vacation_packages.db"

users_db_name = "users.db"

# Tells flask-sqlalchemy what database to connect to
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///{0}".format(users_db_name)
# Enter a secret key
app.config["SECRET_KEY"] = "k%$A84#!tUK"
# Initialize flask-sqlalchemy extension
db = SQLAlchemy()

# LoginManager is needed for our application
# to be able to log in and out users
login_manager = LoginManager()
login_manager.init_app(app)


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True,
                         nullable=False)
    password = db.Column(db.String(250),
                         nullable=False)


# Initialize app with extension
db.init_app(app)
# Create database within app context

with app.app_context():
    db.create_all()


# Creates a user loader callback that returns the user object given an id
@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id)


@app.route("/")
def home():
    # Render home.html on "/" route
    return render_template("home.html")


@app.route("/vacation", methods=("GET", "POST"))
def index():
    if request.method == "POST":

        user_input = request.form["user_input"]

        sentiment_prompt = generate_sentiment_analysis_prompt(user_input)

        # Prompt ChatGPT to do sentiment analysis on the user's input
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user",
                       "content": sentiment_prompt}])

        parsed_sentiments = json.loads(response.choices[0].message['content'])

        # Retrieve destinations that fit the sentiments expressed
        # in the user's input
        filtered_destinations = \
            query_database_for_destinations(parsed_sentiments)

        if len(filtered_destinations) > 1:
            destination = select_package(filtered_destinations)
        else:
            destination = filtered_destinations[0]

        # Retrieve the language tone suitable for the desired vacation type
        tone = query_database_for_tone(parsed_sentiments['vacation_type'])

        # Prompt ChatGPT to generate a "sales pitch" for the destination using
        # the appropriate tone
        pitch_prompt = generate_package_sales_pitch_prompt(destination,
                                                           parsed_sentiments,
                                                           tone)

        print(pitch_prompt, '\n')

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user",
                       "content": pitch_prompt}])

        return redirect(url_for(
            "index", result=response.choices[0].message['content']))

    result = request.args.get("result")
    return render_template("vacation.html", result=result)


@app.route('/register', methods=["GET", "POST"])
def register():
    # If the user made a POST request, create a new user
    if request.method == "POST":
        user = Users(username=request.form.get("username"),
                     password=request.form.get("password"))
        # Add the user to the database
        db.session.add(user)
        # Commit the changes made
        db.session.commit()
        # Once user account created, redirect them
        # to login route (created later on)
        return redirect(url_for("login"))
    # Renders sign_up template if user made a GET request
    return render_template("sign_up.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # If a post request was made, find the user by
    # filtering for the username
    if request.method == "POST":
        user = Users.query.filter_by(
            username=request.form.get("username")).first()
        # Check if the password entered is the
        # same as the user's password
        if user.password == request.form.get("password"):
            # Use the login_user method to log in the user
            login_user(user)
            return redirect(url_for("home"))
    # Redirect the user back to the home
    # (we'll create the home route in a moment)
    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


def generate_sentiment_analysis_prompt(user_input):
    """
    Construct a prompt for the OpenAI API to request that the AI model perform
    sentiment analysis on the user's input and determine the vacation style,
    environment, and travel companions that the user prefers. Prompt also
    specifies that we will want a JSON object as the response.

    :param user_input: The text input by the user.
    :return: The formatted text to be sent to OpenAI API.
    """
    return """Our travel agency’s application just asked a prospective customer
     to describe their ideal vacation. They responded as follows: 
     {user_input}
     Please use sentiment analysis to determine which following word best 
     describes the type of vacation the customer is seeking based on their 
     response: 
     Relaxing, Adventurous, Dining, Exploratory

    Repeat this process to determine which following word best describes the
    environment the customer prefers for their vacation: 
    Beach, Wilderness, Urban

    Repeat this process to determine which of the following best describes who 
    will be traveling with the customer:
    Alone, With Significant Other, With Family, With Friends
    
	Your response should be a JSON object in the following format:
	{{vacation_type: Type, environment: Type, companions: Type}}

	Do not make your response conversational, 
	include only the JSON object.""".format(user_input=user_input)


def select_package(filtered_packages):
    """
    In the event that more than one matching package is retrieved from the
    database, simply choose a random one.

    :param filtered_packages: A dict of all packages that passed query filter
    :return: a dict with a single package
    """
    random_package = dict([random.choice(list(filtered_packages.items()))])

    return random_package


def generate_package_sales_pitch_prompt(destination, parsed_sentiments, tone):
    """
    Construct a prompt for the OpenAI API to request that the AI model craft a
    tailored response to the user which consists of a sales pitch for a locale
    with an appropriate tone and details all specified by the application.

    :param destination: the matched destination
    :param parsed_sentiments: the sentiments returned from the initial prompt
    :param tone: the language tone that matches the vacation type
    :return: The formatted text to be sent to OpenAI API.
    """
    type = parsed_sentiments['vacation_type']

    environment = parsed_sentiments['environment']

    companions = parsed_sentiments['companions']

    return """Pretend you are a travel agent making a first-time recommendation
     to a customer that they purchase a package to visit {destination}. Use a 
     positive {tone} tone and emphasize the qualities about {destination} that 
     make it a great {type} place. Emphasize the allure of its {environment} 
     setting as well as its appeal to those traveling {companions}. Confine your 
     response to a single paragraph. """.format(destination=destination,
                                                type=type,
                                                tone=tone,
                                                environment=environment,
                                                companions=companions)


def build_destination_query(filters):
    """
    Builds a parameterized SQL query filtered by dictionary of "sentiments"

    :param filters: dictionary of sentiments
    :return: a SQL query statement
    """
    placeholders = []

    for column, value in filters.items():
        # Enclose the column name in double quotation marks
        placeholders.append('"{0}" = 1'.format(value))

    # Combine the placeholders with 'AND' for the WHERE clause
    where_clause = " AND ".join(placeholders)

    query = f"""
    SELECT destination
    FROM packages
    WHERE {where_clause};
    """
    return query


def query_database_for_destinations(parsed_sentiments):
    """
    Query the database for vacation destinations that match the user's
    sentiments.

    :param parsed_sentiments: a dict of sentiments
    :return: an array of destination names
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Build the parameterized query and values
    query = build_destination_query(parsed_sentiments)

    # Execute the query with the specified values
    cursor.execute(query)
    destinations = cursor.fetchall()

    # Close the connection
    conn.close()

    # Print the destinations
    if destinations:
        print("Destinations meeting the criteria:")
        for destination in destinations:
            print(destination)

        return destinations
    else:
        print("No destinations found that meet the criteria.")


def query_database_for_tone(vacation_style):
    """
    Query the database to retrieve the appropriate language tone for the style
    of vacation desired.

    :param vacation_style: the style of vacation desired
    :return: a language tone
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    query = f"""
    SELECT tone
    FROM tones
    WHERE style = "{vacation_style}";
    """

    # Execute the query with the specified values
    cursor.execute(query)
    tone = cursor.fetchone()

    # Close the connection
    conn.close()

    # Print the destinations
    if tone:
        print("Tone meeting the criteria:")
        print(tone)
        return (tone)
    else:
        print("No tone found that meets the criteria.")


if __name__ == "__app__":
    app.run()
