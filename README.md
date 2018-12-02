# Crypto Chat Bot 

## Introduction

The program is a simple program that leverages the power of Dialogflow for natural language processing and understanding. It currently only leverages Dialogflow's ability to do NLU (Natural Language Understanding).  

## Architecture   

User message --> Slack --> Python --> Dialogflow --> Python (check if intent is price/volume/stats for coin) -->  3rd Party API for prices --> Slack 

1) The program starts off with a slack bot that listens to converstations on a slack channel and waits for the user to tag the bot. 

2) When the bot is tagged, the python client reads this message from the user and passes it to dialogflow. 

3) Dialogflow than classifes the intent of this message and also possible Entities that it recognizes and returns this information to python. 

4) If any one of the intents + entities defined is recognized by dialogflow, python grabs price data using Coincap's API and add's this response to Dialogflows message. 

## Configuring Dataflow 

1) Create a new Agent in dialogflow and configure and train based on the type of chat-bot you need. 
2) Name your intents based on the name of your functions that will handle this intent in python 
3) Generate service account credenitals under google cloud console and download the json credential file 
4) Keep this file ready for autenthication later on 

## Configuring Slack 

1) Create a slack app 
2) Create a bot user 
3) Install app under settings and add your bot to a slack channel 	
4) Copy the oauth access token for use later on 

## Installation Instructions Locally

1) clone the project using the following command 
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

6) Open the file and set all the necessary configs. Make sure environment is "dev" and make sure "GOOGLE_APPLICATION_CREDENTIALS" is path to your credentials file. 

7) Now we have to configure intents based off the names on dialogflow. In the core_intent.json file configure all your intent names as the key and for the value you can write any sentance. Be sure to add two '%s'. The first for the coin and the second for the value returned by python. Once you have this, you will need to implement these functions that takes coin as the arguement and returns the stat requested. These functions should be named based off the intent for the program to automatically pick up the functions. Currently there are already functions implemented for the intents in core_intent.json. 

8) Now you are ready to run the program. Simply run 

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

4) You will also need a new settings var called "INTENT_CONFIG" who's value is the contents of the core_intent.json. This is to make configuring the core easy during deployment, since Heroku doesnt allow changing file contents without having to re-deploy. 


5) Your worker should be ready and running. You can run the following command to check the logs and make sure everything is working normally. 
```
heroku logs --tail
```

## Usage

Once deployed simply go into your slack channel with the slack bot. Tag your bot using @ command and start talking to your bot. 


## Challenges 

1) Waiting for a third party api to respond to get data seemed to slow down the bot by several magnitudes. In order to solve this I poll the information every 15 mins insatead using a python cron sheduler. This allows the bots to respond as fast as possible since it can simply grab the stat requested from the memory without having to wait for the third party api to respond. This time is also configurable incase more real-time information is needed. 

2) Maintaining the project was getting difficult as soon as intents were being added. This was because everytime a new intent was added I had to add a conditional statement that would handle this. This does not seem scaleable so I made the intent configuration a config file called core_intent.json. This makes it easy to add intents, and all you need to do is after adding it to the configuration, create a simple function that takes in the entity name and returns the stat. If the intent name and functions name matched, the script would automatically start handling this new intent. 



