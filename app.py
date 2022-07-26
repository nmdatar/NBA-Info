
import os
import requests
import json
from datetime import date, timedelta


from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

api_key = os.environ.get('NBA-Info API Key')

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///betting.db")

# Create global arrays to store data
teamsN = []
teamsS = []
matches = []


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/stats", methods=["GET", "POST"])
@login_required
def stats():
    if request.method == "POST":
        teamsS.clear()
        teamsN.clear()
        # Check if user inputted year
        if not request.form.get("year"):
            return render_template("stats.html", error=1)

        year = request.form.get("year")

        # Make request to API to get data from year inputted
        url = "https://api-basketball.p.rapidapi.com/standings"

        querystring = {"league": "12", "season": year}

        headers = {
            'x-rapidapi-host': "api-basketball.p.rapidapi.com",
            'x-rapidapi-key': api_key
        }

        response = requests.request("GET", url, headers=headers, params=querystring)

        # Create temporary string of key-values from API request
        temporary = response.text
        i = 0
        # Convert string to dictionary using json library load method
        convert = json.loads(temporary)
        for rows in convert["response"]:
            for row in rows:
                if i < 30:
                    # Create team information dictionary
                    team = {"position": row["position"], "win%": row["games"]["win"]["percentage"], "wins": row["games"]["win"]["total"], "lose%": row["games"]["lose"]["percentage"],
                            "losses": row["games"]["lose"]["total"], "pointsfor": row["points"]["for"], "pointsagainst": row["points"]["against"], "id": row["team"]["id"], "name": row["team"]["name"]}
                    # Append all Eastern Conference teams to one array
                    if i < 15:
                        teamsN.append(team)
                    # Append all Western Conference teams to one array
                    else:
                        teamsS.append(team)
                    i = i + 1
                else:
                    break
        return render_template("stats.html", teamsN=teamsN, teamsS=teamsS)
    # When accessed through GET method
    else:
        return render_template("stats.html")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    # indexs the table to find all stocks bought or sold by a person
    history = db.execute("SELECT * FROM bets WHERE user = ? ORDER BY time DESC", session["user_id"])
    return render_template("index.html", history=history)


@app.route("/games", methods=["GET", "POST"])
@login_required
def games():
    if request.method == "POST":
        # Clear current matches  to only store matches from day requested
        matches.clear()
        if not request.form.get("daychange"):
            return render_template("games.html", error=1)
        # Get difference in days user inputted
        difference = request.form.get("daychange")
        
        url = "https://api-basketball.p.rapidapi.com/games"
        # Determine day user wants to find based on daychange difference
        day = date.today() + timedelta(days=int(difference))
        print(day)
        querystring = {"date": day}

        headers = {
            'x-rapidapi-host': "api-basketball.p.rapidapi.com",
            'x-rapidapi-key': api_key
        }

        # Get response after requesting API
        response = requests.request("GET", url, headers=headers, params=querystring)

        # Store in temporary variable
        temporary = response.text

        # Convert string of key-values to dictionary
        convert = json.loads(temporary)
    
        # Append individual games with game information to all matches list
        for rows in convert["response"]:
            if rows["league"]["name"] == 'NBA':
                game = {"home": rows["teams"]["home"]['name'], "homeid": rows["teams"]["home"]['id'], "away": rows["teams"]["away"]['name'], "awayid": rows["teams"]["away"]['id'], 
                        "scorehome": rows["scores"]["home"]["total"], "scoreaway": rows["scores"]["away"]["total"], "prediction": rows["teams"]["home"]['name'], "underdog": rows["teams"]["away"]['name']}
                matches.append(game)
        url = "https://api-basketball.p.rapidapi.com/standings"

        querystring = {"league": "12", "season": "2021-2022"}

        headers = {
            'x-rapidapi-host': "api-basketball.p.rapidapi.com",
            'x-rapidapi-key': api_key
        }
        # Request API
        response = requests.request("GET", url, headers=headers, params=querystring)

        temporary = response.text
        i = 0
        convert = json.loads(temporary)
        
        # Create table to store statistics
        db.execute("CREATE TABLE IF NOT EXISTS stats (position INTEGER NOT NULL, winpercent REAL NOT NULL, losepercent REAL NOT NULL, pointsfor REAL NOT NULL, pointsagainst REAL NOT NULL, teamid INTEGER PRIMARY KEY, name TEXT NOT NULL)")

        for rows in convert["response"]:
            for row in rows:
                if i < 30:
                    # Check if team already exists in stats table
                    if db.execute("SELECT teamid FROM stats WHERE teamid == ?", row["team"]["id"]):
                        # Update stats with new statistics for a given team
                        db.execute("UPDATE stats SET position = ?, winpercent = ?, losepercent = ?,pointsfor = ?, pointsagainst =? WHERE teamid = ?", 
                                   row["position"], row["games"]["win"]["percentage"], row["games"]["lose"]["percentage"], row["points"]["for"], row["points"]["against"], row["team"]["id"])
                    else:
                        # Enter new team into stats table if doesn't already exist
                        db.execute("INSERT INTO stats (position,winpercent,losepercent,pointsfor,pointsagainst,teamid,name) VALUES(?,?,?,?,?,?,?)", 
                                   row["position"], row["games"]["win"]["percentage"], row["games"]["lose"]["percentage"], row["points"]["for"], row["points"]["against"], row["team"]["id"], row["team"]["name"])
                    i = i + 1
                else:
                    break
        for games in matches:
            # Calculate winpercentages and position/rankings
            winpercenthome = db.execute("SELECT winpercent FROM stats WHERE teamid =?", games["homeid"])[0]["winpercent"]
            winpercentaway = db.execute("SELECT winpercent FROM stats WHERE teamid =?", games["awayid"])[0]["winpercent"]
            positionhome = db.execute("SELECT position FROM stats WHERE teamid =?", games["homeid"])[0]["position"]
            positionaway = db.execute("SELECT position FROM stats WHERE teamid =?", games["awayid"])[0]["position"]
            # Change odds/prediction based on below algorithm
            if (winpercenthome + 0.05)*(1/positionhome) < winpercentaway*(1/positionaway):
                games["prediction"] = games["away"]
                games["underdog"] = games["home"]
        return render_template("games.html", games=matches)
    else: 
        return render_template("games.html")


@app.route("/info")
@login_required
def info():
    return render_template("info.html")


@app.route("/bet", methods=["GET", "POST"])
@login_required
def bet():

    if request.method == "POST":
        # Select cash user has in account
        cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        # Check if team or cash for team submitted is not inputted
        if not request.form.get("team"):
            return render_template("bet.html", error=1, games=matches, cash=cash[0]['cash'])
        if not request.form.get("amount"):
            return render_template("bet.html", error=2, games=matches, cash=cash[0]['cash'])
        
        amount_spent = int(request.form.get("amount"))
        
        # Check if cash amount inputted is more than amount user has in account
        if amount_spent > cash[0]['cash']:
            return render_template("bet.html", error=3, games=matches, cash=cash[0]['cash'])

        # Create table to store bets
        db.execute("CREATE TABLE IF NOT EXISTS bets (team TEXT NOT NULL, time TEXT NOT NULL, amount REAL NOT NULL, game TEXT NOT NULL, winner REAL, gain REAL, user TEXT NOT NULL)")
        for rows in matches:
            # Find game which user wants to bet on
            if (rows["home"] == request.form.get("team")) or (rows["away"] == request.form.get("team")):
                # Set game name
                game = rows["home"] + " vs " + rows["away"]
                # Check if game already occurred
                if rows["scorehome"] != None:
                    # Determine game winner
                    if rows["scorehome"] < rows["scoreaway"]:
                        winner = rows["away"]
                    else:
                        winner = rows["home"]
                    # Check if user bet on winning team
                    if winner == request.form.get("team"):
                        # Check if winning team is or is not winning team
                        if winner != rows["prediction"]:
                            gain = 2*request.form("amount")
                        else:
                            gain = 0.05 * int(request.form.get("amount")) + int(request.form.get("amount"))
                    else: 
                        gain = 0
                    # Log new bet
                    db.execute("INSERT INTO bets (team, time, amount, game, winner, gain, user) VALUES ( ?, datetime('now','localtime'), ?, ?, ?, ?, ?)", 
                               request.form.get("team"), request.form.get("amount"), game, winner, gain, session["user_id"])
                else:
                    # Log new bet
                    db.execute("INSERT INTO bets (team, time, amount, game, winner, gain, user) VALUES ( ?, datetime('now','localtime'), ?, ?, ?, ?,?)", 
                               request.form.get("team"), request.form.get("amount"), game, "game not done", "game not done", session["user_id"])
        # Determine cash amount user has left
        amount_left = cash[0]['cash'] - amount_spent
        # Update cash for this user
        db.execute("UPDATE users SET cash = ? WHERE id = ?", amount_left, session["user_id"])
        return redirect("/")
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    return render_template("bet.html", games=matches, cash=cash[0]['cash'])


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", error=1)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", error=2)
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", error=3)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    
    # checks to see if form is sumbitted 
    if request.method == "POST":

        error = 0

        # checks to see if username is provided 
        if not request.form.get("username"):
            error = 1
        # checks to see if username is unqiue 
        elif db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username")):
            error = 2
        # checks to see if password and confromation are there
        elif not request.form.get("password") or not request.form.get("confirmation"):
            error = 3
        # checks to see if password matches conformation
        elif request.form.get("password") != request.form.get("confirmation"):
            error = 4
    
        if error != 0:
            return render_template("register.html", error=error)

        # inserts new user and hashed password into users
        db.execute("INSERT INTO users (username, hash) VALUES (?,?)", request.form.get("username"), 
                   generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8))
        # logs in
        login = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        session["user_id"] = login[0]["id"]
        # takes you to home page
        return redirect("/")
    # takes you to register page if you got here from get 
    else:
        return render_template("register.html")


@app.route("/addcash", methods=["GET", "POST"])
@login_required
def addcash():
    # sets bool to 0
    yes = 0
    error = 0
    # checks for form
    if request.method == "POST":
        # makes sure form was filled out
        if not request.form.get("amount") and not request.form.get("withdraw"):
            error = 1
        elif not request.form.get("withdraw"):
            # gets amount of money you have
            cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            # adds that to how much you want to add
            amount_left = cash[0]['cash'] + int(request.form.get("amount"))
            # updates user 
            db.execute("UPDATE users SET cash = ? WHERE id = ?", amount_left, session["user_id"])
            yes = 1
        else:
            # gets amount of money you have
            cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            # adds that to how much you want to add
            amount_left = cash[0]['cash'] - int(request.form.get("withdraw"))
            if amount_left < 0:
                error = 2
            else:
                db.execute("UPDATE users SET cash = ? WHERE id = ?", amount_left, session["user_id"])
                yes = 2
    cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    return render_template("cash.html", cash=cash[0]['cash'], yes=yes, error=error)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
