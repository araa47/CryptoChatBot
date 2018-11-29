# Crypto Chat Bot 

## Introduction

The program is a simple program that leverages the power of Dialogflow for natural language processing and understanding. It currently only leverages Dialogflow's ability to do NLU (Natural Language Understanding).  

## Archietecture  

User message --> Slack --> Python --> Dialogflow --> Python (check if intent is price/volume/stats for coin) -->  3rd Party API for prices --> Slack 

1) The program starts off with a slack bot that listens to converstations on a slack channel and waits for the user to tag the bot. 

2) When the bot is tagged, the python client reads this message from the user and passes it to dialogflow. 

3) Dialogflow than classifes the intent of this message and also possible Entities that it recognizes and returns this information to python. 

4) If any one of the intents + entities defined is recognized by dialogflow, python grabs price data using Coincap's API. This process would sometimes be slow and make the crypto bot seem slow. So the python script just grabs the price information for all coins every 15 mins and stores it locally in a dictionary. When price information is needed, it simply uses this dictionary to get the current price. This ensures there is no network latency and that the bots response isnt any slower.

## Configuring Dataflow 

1) Create a new Agent in dialogflow and configure and train based on the type of chat-bot you need
2) Generate service account credenitals under google cloud console and download the json credential file 
3) Keep this file ready for autenthication later on 

## Configuring Slack 

1) Create a slack app 
2) Create a bot user 
3) Install app under settings and add your bot to a slack channel 	
4) Copy the oauth acess token for use later on 

## Installation Instructions Locally

1) clone the project using the follwing command 
```
git clone https://github.com/araa47/CryptoChatBot
```

2) Cd into the the project directory

```
cd CryptoChatBot 
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

6) Open the file and set all the necessary configs. Make sure environment is "dev" and make sure "GOOGLE_APPLICATION_CREDENTIALS" is path to your credentials file

7) Now you are ready to run the program. Simply run 

```
python3 app.py 
```


## Deployment Instructions 

1) The program can simply be deployed into heroku without much configuration, simply connect heroku to this repository for direct deployment. You can also use heroku cli to deploy. 

```
# login to heroku cli
heroku login 
# create heroku app using gui and then add the app to remote of local project
heroku git:remote -a herokuprojectname
# push to heroku 
git push heroku master 
```

2) Once you have deployed using heroku cli you will need to run the following command to start your worker. 
```
heroku ps:scale worker=1
```

3) You will also need to set the env vars in heroku settings. For heroku cli all the configs are similar to local deployment, the only difference is that you will set "GOOGLE_APPLICATION_CREDENTIALS" to your json data in the credentials file instead and set "ENVIRONMENT" to production instead of dev. 


4) Your worker should be ready and running. You can run the following command to check the logs and make sure everything is working normally. 
```
heroku logs --tail
```




