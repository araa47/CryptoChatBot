# Crypto Chat Bot 

## Introduction

The program is a simple program that leverages the power of Dialogflow for natural language processing and understanding. 

## Archietecture  

User message --> Slack --> Python --> Dialogflow --> Python (check if intent is price for coin) -->  3rd Party API for prices --> Slack 

1) The program starts off with a slack bot that listens to converstations on a slack channel and waits for the user to tag the bot. 

2) When the bot is tagged, the python client reads this message from the user and passes it to dialogflow. 

3) Dialogflow than classifes the intent of this message and also possible Entities that it recognizes and returns this information to python. 

4) If any one of the entities defined is recognized by dialogflow, python grabs price data using Coincap's API. This process would sometimes be slow and make the crypto bot seem slow. So the python script just grabs the price information for all coins every 15 mins and stores it locally in a dictionary. When price information is needed, it simply uses this dictionary to get the current price. This ensures there is no network latency and that the bots response isnt any slower.

## Configuring Dataflow 

1) Create a new Agent in dialogflow and configure based on the type of chat-bot you need 
2) Generate service account credenitals under google cloud console and download the json credential file 
3) Keep this file ready for autenthication later on 

## Configuring Slack 

1) Create a slack app 
2) Create a bot user 
3) Install app under settings 
4) Copy the oauth acess token for use later on 

## Installation Instructions Locally

1) clone the project using the follwing command 
```
git clone ....
```

2) Cd into the the project directory

```
cd cryotobot 
```

3) Enable pipenv
```
pipenv shell 
```

4) Install dependencies 
```
pipenv install 
```

5) Now we can set up the config vars. Copy the file .env.example and call it .env 

6) Open the file and set "GOOGLE_APPLICATION_CREDENTIALS" to the path of the credentials file you created for dialogflow. 

7) Set the "SLACK_BOT_TOKEN" to the token that was copied over while configurin slack 

8) Now you are ready to run the program. Simply run 

```
python3 app.py 
```


## Deployment Instructions 

1) The program can simply be deployed into heroku without much configuration

2) 


