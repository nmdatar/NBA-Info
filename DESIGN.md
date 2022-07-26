This project was implemented using Python (with the library flask and template jinja), SQL for backend, as well as HTML/CSS for backend. First, there are several functions with corresponding app routes that exist in app.py, which help to display different items on each page, and navigate the user among the different html files in the projects directory when needed. 

First, take note of the login() function in app.py. We decided to implement this function in the manner we did because the login page can be requested via two methods - "GET" and "POST" (this is a recurring theme across all functions). Thus, we must have different functionality for each one. The POST method is called with action /login when a user submits the form, as observed by checking the login.html file and seeing that upon submission of the form, the action is as such along with desired method. We want this method to be POST because we don't want key-value pairs to be in the url of the browser, if a user submits a password or username. Note, in the login function in app.py however, that several 'if statements' exist to check if the user indeed submitted a username and password. 

The register function in app.py is very similar to that of login. The user must enter both a username, password, and confirmation for that password, and app.py contains several if statements since we wanted to check to make sure the user actually inputted information to all fields when trying to create an account. Note that we decided to store all login information in a SQL database, because it provided ease of checking if a username already exists or if a username/password match when trying to login with one simple SQL execution. Additionally, note that in register, the item stored for the password in the SQL database is a password hash rather than an actual password inputted by the user. We chose this implementation because it allows for a plain text password to essentially be stored as an unreadable sequence to humans. 

At this point, we had the login authorization complete, and we began trying to get data from an API we selected. We initially used a NBA API (https://rapidapi.com/api-sports/api/api-nba/) from rapidapi.com, but we realized that the API did not actually contain the data we wanted to create a betting website. Thus, we chose to switch to a general Basketball API on rapidapi.com (https://rapidapi.com/api-sports/api/api-basketball/ ). After getting an API key, we began trying to implement getting data from the API using JavaScript, following resources online. We tried for a long time, and tried different methods of testing whether the data was correctly being read into a json file, such as by printing to the console, but couldn't seem to properly extract the data. So, we switched to Python. rapidapi already had code we could copy to actually implement the request to the API to get data. We copied the following code:

```url = "https://api-basketball.p.rapidapi.com/standings"

        querystring = {"league":"12","season":"2021-2022"}

        headers = {
                    'x-rapidapi-host': "api-basketball.p.rapidapi.com",
                    'x-rapidapi-key': "2591224834msh59c35823a966b16p1920e7jsn9f7223ef13eb"
                }
        # Request API
        response = requests.request("GET", url, headers=headers, params=querystring)

        temporary = response.text```

After this, we converted the temporary string into readable Python dictionary using the code:

```convert = json.loads(temporary)```

That code utilized the json library to actually load the string into a dictionary.

We used the same combination of code above to make a request to the API multiple times. However, we changed the parameters in querystring multiple times throughout the different functions games(), stats(), and bet() according to the information we wanted the user to be able to input to get back specific data. For example, when implementing games(), our idea was to be able to display the scores of the games from the day of the users choice. That is why we allowed the user to enter the number of days from the current date in a form called "daychange", followed by determining the day the user was referring to using the libraries date and timedelta in python. This was done with the following code:

```difference = request.form.get("daychange")
        
day = date.today() + timedelta(days=int(difference))```

We didn't allow the user to enter the string format of the date itself, because we wanted to ensure that the correct format was being entered as a parameter into querystring. In this case, "day" was passed in as the value to the parameter, showing the need for dynamically calling the API in many cases.

Importantly, the way we accessed the data once converted into a dictionary, we obtained specific information by accessing nested dictionaries, as "convert" itself is a dictionary containing dictionaries which themselves contain dictionaries and so on. For example, one item we stored was game information in a list called matches. We did this with the following implementation:

```for rows in convert["response"]:
            if rows["league"]["name"] == 'NBA':
                game = {"home": rows["teams"]["home"]['name'],"homeid": rows["teams"]["home"]['id'], "away": rows["teams"]["away"]['name'], "awayid": rows["teams"]["away"]['id'], "scorehome": rows["scores"]["home"]["total"], "scoreaway": rows["scores"]["away"]["total"], "prediction": rows["teams"]["home"]['name'], "underdog": rows["teams"]["away"]['name']}
                matches.append(game)```

We knew how to access information within the convert dictionary based on the documentation in rapidapi.com. Above, we stored game information we needed in our own dictionary we created called game, and then appended each time to a list. Note how the list matches, teamsN, and teamsS within the app.py file are declared globally, rather than witin each function. We did this because we wanted to save the current game information from the last API request, which was important for placing bets later and showing stats. 

 Additionally, we were only familiar with the NBA, so we limited the results in all such API calls to the league name 'NBA'. The results were displayed to the user with the following, which dynamically adds table rows based on the number of games matching parameter request to the API: 


{% for x in range(0, games|length) %}
                        
    <tr>
        <th class = "table-start">{{ games[x]["home"] }}</th>
        <th class = "table-start">{{ games[x]["scorehome"] }}</th>
        <th class = "table-end">{{ games[x]["scoreaway"] }}</th>
        <th class = "table-end">{{ games[x]["away"] }}</th>
        <th class = "table-end">{{ games[x]["prediction"] }}</th>
    </tr>
                            
{% endfor %}

Apart from games, we wanted to provide statistics for any user, not just basketball fans, so that was the justificatior for including statistics pages. However, to provide a detailed summary of each team, we included a stats() function and html page whose function was to display specific information for each team in the Eastern and Western conference, such as position/ranking, wins, losses, etc. acrosses the three seasons (current and past two) available on the API. We got and displayed the information similar to above, and allowed the user to toggle between 3 different seasons using a select dropdown implemented in HTML, with backend in app.py. 

With these summaries of the previous seasons, we implemented letting the user place bets by making requests similar to those in games() and stats(). Note however, we wanted to limit the display of the possible matches the user could place bets on, so we only allowed the user to place bets on matches search for in games.html, which they could do by clicking on the button at the bottom of the page. This highlights another need to store the matches list globally, since the information in it is needed in bets after each call in games. We simply allowed the user to select games to bet on by producing a dropdown with all the game options on the day the user selected. For each game in the select dropdown, we bolded the game we predicted to win by implementing the following style in bet.html: class='bolden'. We initially wanted to include odds from the API, but there was no data available on it, so we tried to implement our own simple prediction for the winner using the following code: (winpercenthome + 0.05)*(1/positionhome) < winpercentaway*(1/positionaway). It is easy to see we gave a slight edge to the home team, which is natural since home teams tend to have an advantage in sports games. 

From this, the user could select a certain team, enter a dollar amount, and place a bet on the match. We then had our own method of calculating the gain if the user bet on a predicted winner, non-predicted winner, or loser, similar to our own method of predicted winner. However, we utilized an if statement to check if some of the available data from the API existed, such as the score, by which we could see if the match had occurred or not yet, since we don't want to post a gain if the outcome of the match has not been determined yet! Additionally, we checked to make sure the user had enough money to actually place the bet, by grabbing data from a users table which stored each users current cash amount. These bets were placed in a SQL table, since this provided ease of storing and accessing data, along with information on when they occurred, how much the gain is, for what team the bet was placed, etc. since we wanted the user to be able to see a complete history of all the bets made. 

One thing we wish we could have included was actually adding the money gained from each bet to the user's current cash. However, this would have involved redifining another primary key for each bet in the bets SQL table. Other factors that made this difficult was the fact that specific bets in the history for games that are not complete yet would need to be reupdated, to see which team actually ended up winning and how much was gained. This would have involved a lot of requests to the API, which may have costed us, the developers, money, which we didn't want. 
