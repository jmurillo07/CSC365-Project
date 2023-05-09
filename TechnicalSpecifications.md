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
1. **POST /fighters/**  
This endpoint takes an fighter datatype and adds new data into the database.  
   
   The fighter datatype is given in the following format:
   ```json
   {
     "first_name": "string",
     "last_name": "string",
     "height": 0,
     "reach": 0,
     "stance": null,
     "recent_fights": []
   }
   ```
   Where stance is either empty or an enumeration between 1-3, representing "Orthodox", "Southpaw", and "Switch" respectively.

2. **POST /fights/**  
This endpoint adds a new fight and updates the existing data of the fighters associated with the fight in the database.  

   The endpoint returns the fight_id of the new fight.

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

3. **GET /fights/{fight_id}/predictions**  
This endpoint returns the results of a prediction. A prediction can be done on any fight and records the number of votes voted on each fighter.

   The author of the prediction has their internal id stored in the `user_id` key.

   The keys `fighter1_count` and `fighter2_count` correspond to the `fighter1` and `fighter2` keys from the fight the `fight_id` is from. The values of `fighter1_count` and `fighter2_count` represent how many people have predicted on which fighter to win.

   Each prediction is given in the following format:
   ```json
   {
     "prediction_id": 0,
     "fight_id": 0,
     "fighter1_count": 0,
     "fighter2_count": 0,
     "user_id": 0,
   }
   ```
4. **POST /fights/{fight_id}/predictions**
This endpoint provides functionality for a user to create their own prediction.  

   The prediction is generated based on the given `fight_id` in the request.

   Below is a sample request body.
   ```json
   {
     "fight_id": 0
   }
   ```
5. **GET fighters/{fighter_id}**  
This endpoint returns a fighter by their internal id.  
   
   For each fighter it returns:
* `fighter_id`: The internal id of the fighter.
* `name`: The name of the fighter, in the format of [First Name, Last Name].
* `height`: The height of the fighter in inches.
* `weight`: The weight of the fighter in pounds.
* `reach`: The reach of the fighter given in inches.
* `stance`: The stance of the fighter.
* `wins`: The amount of wins the fighter has.
* `losses`: The amount of losses the fighter has.
* `draws`: The amount of draws the fighter has.
* `recent_fights`: A list of the 5 most recent fights the fighter participated in. The list is descending ordered based on recency.

   Each fight is represented by a dictionary with the following keys:
* `fight_id`: The internal id of the fight.
* `opponent_id`: The internal id of the opponent.
* `opponent_name`: The name of the opponent.
* `result`: The internal id of the victor or none if a draw.

6. **GET fighters/**  
This endpoint takes a few filter options and returns a list of fighters matching the criteria.  
   Available filters are:  
* `stance`: The stance of the fighter.
* `name`: Inclusive search on the name string.
* `height_min`: Minimum height in inches (inclusive). Defaults to 0.
* `height_max`: Maximum height in inches (inclusive). Defaults to 999.
* `weight_min`: Minimum weight in pounds (inclusive). Defaults to 0.
* `weight_max`: Maximum weight in pounds (inclusive). Defaults to 9999.
* `reach_min`: Minimum reach in inches (inclusive). Defaults to 0.
* `reach_max`: Maximum reach in inches (inclusive). Defaults to 9999.
* `wins_min`: Minimum number of wins, defaults to 0.
* `wins_max`: Maximum number of wins, defaults to 9999.
* `loses_min`: Minimum number of loses, defaults to 0.
* `loses_max`: Maximum number of loses, defaults to 9999.
* `draws_min`: Minimium number of draws defaults to 0.
* `draws_max`: Maximum number of draws, defaults to 9999.
* `event`: Takes the name of an event and will return the fighters who participated in it.

   Additionally, this endpoint takes a `sort` query parameter:
* `name`: Sorts alphabetically.
* `height`: Sorts by height.
* `weight`: Sorts by weight.
* `reach`: Sorts by reach.
* `win_rate`: Sorts by win rate.
* `order`: Either `"ascending"` or `"descending"`.

   The `limit` and `offset` query parameters are used for pagination. `limit` will limit the amount of results to return and `offset` species the number of results to skip before returning the result.

Transaction Flows:
* Any request made by a user that involves writing will have to go through integrity and consistency checks. Should they fail at any point then their query shall be voided and any changes made to the database reversed.

* ***(WIP)*** A user creates a prediction on the website by creating a POST request on the a fight of their choice. Their prediction is signed with their user id. They can share their prediction around with other users where they can collect data to see who the community (or at least the people they reached) believes will win the fight. Each prediction is unique based on the combination of its `fight_id` and `user_id`, that is, a user can only create one prediction per fight.

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