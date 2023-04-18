Technical Specifications for UFC database
CSC 365

User Stories/User Requirements (min 6):

1. As a casual sports bettor / member of the UFC community,
I want to be query for a certain fight or UFC event(which consists of multiple fights) and be able to view who people think will win.
So that I can get an insight of who the UFC community believes will win upcoming fights and stay engaged with other UFC community members.

2. As a casual sports bettor / member of the UFC community,
I want to be able to be add my personal input/ reasoning on who is most likely to win a UFC match to inform other members of
the UFC community, adding my predictions to the database.
So that I can give others insight on who will win and actively engage with the rest of the UFC community.

3. As a casual bettor,
I want to be able to query a match up between two upcoming fighters and then be able to display relevant stats such as
average fight time, recent fight results, any relevant injuries.

4. As a journalist,
I want to be able to easily look up fighters and their statistics
So that I can create relevant and up to date inforgraphics.

5. As a casual bettor,
I want to be able to gain expert insight from the application on who is most likely to win, with the api explaining why given
relevant statistics, such as fight history, recent injuries, and age.
So that I can make a more informed decision on who is going to win a fight.

6. As a moderator,
I want to be able to write to the UFC event data and player outcomes
So that the information on the website remains up to date and gives the most time to users to predict winners of fights.

7. As a casual fan of the UFC,
I want to be able to quickly search for a fighter amongst the database to see fighting stats of players.
So that I become more informed of fighters and broaden my knowledge of the UFC sport.

Endpoints:
Your initial version of your application should have at least 5 endpoints, and at least one endpoint must be adding/updating data.
1. **add_data**,
This endpoint takes an fighter datatype and adds new data into the database. The fighter datatype is given in the following format:
```json
{
  "name": "string",
  "nick": "string",
  "height": 0,
  "weight": 0,
  "reach": 0,
  "stance": "string",
  "wins": 0,
  "losses": 0,
  "draws": 0,
  "active": true,
  "recent_fights": []
}
```

2. **update_data**,
This endpoint takes a fight and updates the existing data of the fighters associated with the fight in the database.
Each fight is represented by a dictionary with the following keys:
* `fight_id`: The internal id of the fight.
* `event`: The name of the event the fight took place at.
* `result`: The result of the fight, given as the name of the fighter or "Draw".
* `fighter1`: The name of the first fighter.
* `fighter2`: The name of the second fighter.
* `kd_1`: The number of knockdowns fighter 1 got.
* `strikes_1`: The number of strikes given fighter 1 did.
* `td_1`: The number of takedowns fighter 1 did.
* `sub_1`: The number of submission attempts fighter 1 did.
* `kd_2`: The number of knockdowns fighter 2 got.
* `strikes_2`: The number of strikes given fighter 2 did.
* `td_2`: The number of takedowns fighter 2 did.
* `sub_2`: The number of submission attempts fighter 2 did.
* `weight`: The weight division of the fight.
* `method`: The method of win.
* `round`: The round the win happened.
* `time`: The time during the round when the win happened.

3. **prediction**,
This endpoint provide UFC community members a chance to make their own predictions, and the predictions will be added to the database.  
Each prediction is given in the following format:
```json
{
  "prediction_id": 0,
  "choices": 
    {
      "option_1": "string",
      "option_2": "string",
      "option_3": null,
      "option_4": null,
      "option_5": null,
      "option_6": null
    },
  "agree_count": 0,
  "disagree_count": 0,
  "user_responses": [
    {
      "user_id": 0,
      "choice": 1,
    }, 
  ]
}
```
4. **get_fighter_by_name**,
This endpoint returns a fighter by their name. For each fighter it returns:
* `fighter_id`: The internal id of the fighter.
* `name`: The name of the fighter, in the format of [First Name, Last Name].
* `nick`: The nickname of the fighter (if it exists).
* `height`: The height of the fighter in inches.
* `weight`: The weight of the fighter in pounds.
* `reach`: The reach of the fighter given in inches.
* `stance`: The stance of the fighter.
* `wins`: The amount of wins the fighter has.
* `losses`: The amount of losses the fighter has.
* `draws`: The amount of draws the fighter has.
* `active`: A boolean indicating whether or not the fighter still fights in the UFC.
* `recent_fights`: A list of the 5 most recent fights the fighter participated in. The list is descending ordered based on recency.

   Each fight is represented the same way as seen in endpoint `update_data`.

5. **get_fighters**,
This endpoint takes a few filter options and returns the information and statistics about all the filtered fighters.

6. **compare_fighters**,
This endpoint takes two fighter names and compare the statistics between them

7. **login**,
This endpoint takes an UserId and a Password and jump to different URLs for different type of users

Transaction Flows:

Edgecases:
* some of these I believe should go under certain endpoints.

- Incomplete prediction of fights for an event: UFC main cards consist of usually 5-6 fights, users who want to upload their predictions
to the database will either need to predict a winner for each respective fight for an event or on the backend we will make sure that any empty prediction for
a fight is a valid input and we will not update prediction entries relevant to that entry.

- Incomplete statistics on a fighters/event: any entry returned from a endpoint that returns None or null values must be detected and reflected on the front end
of the web page informing the user that the data they attempt to search for may be incomplete for some results.

- Empty queries: Any empty queries for endpoints that require a specific name/names to gather results will alert user that their request is incomplete, 
prompting them to fill out the respective information that is missing.

- Empty return results: Provide a formal message with the given query (for them to see if their is a mistake in what they were searching for) stating that there were no
search results found.