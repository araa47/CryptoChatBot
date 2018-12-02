import dialogflow_v2 as dialogflow
from google.protobuf.json_format import MessageToJson
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
# -*- coding: utf-8 -*-
"""
Created on Nov 27 21:46:38 2018

@author: Akshay
"""

# import necessary libraries 
import json 
import os
import time
import re
from slackclient import SlackClient
import requests 
from dotenv import load_dotenv, find_dotenv
from apscheduler.scheduler import Scheduler


################# Global Variables that change in value #####################################

# global stat dict (used to store all info locally)
crypto_data = {}
# starterbot's user ID in Slack: value is assigned after the bot starts up, so set to none 
starterbot_id = None

################# Fixed global variables that are usually the same ##########################

# google auth scope 
scope = ["https://www.googleapis.com/auth/cloud-platform"]
# Slack delay between reading from RT api , almost always set to 1 second
RTM_READ_DELAY = 1 
# this regex is used to check if someone mentioned the bot 
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"


################### Configurable vars from .env file #########################################
# dialogflow project id 
project_id = os.getenv("PROJECT_ID")
# get refresh interval for coincap data
coincap_refresh_interval_mins = int(os.getenv("COINCAP_REFRESH_INTERVAL_MINS"))
# get slackbot token 
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
# get environment 
env = os.getenv("ENVIRONMENT")

######################## Configurable var  for actions based on intent #######################

intent_cofig = {  
    "get_price": " The current price of %s is %s USD",
    "get_volume": " The current 24 hour USD Volume for %s is %s USD",
    "get_supply": " The current circulating supply of %s is %s coins",
    "get_change": "In the past 24 hours %s has changed by %s percent"
}

##############################################################################################

# Configure creds for google 
if env == "dev":
    # if local secret is filename, read creds from file 
    secret = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    creds = service_account.Credentials.from_service_account_file(secret)
else:
    # if production (heroku), secret is the json, read creds by loading json directly 
    secret = json.loads((os.getenv("GOOGLE_APPLICATION_CREDENTIALS")))
    creds = service_account.Credentials.from_service_account_info(secret)

# Configure creds and instantiate slack 
slack_client = SlackClient(SLACK_BOT_TOKEN)



# Enable cron sheduler 
cron = Scheduler(daemon=True)
# Explicitly kick off the background thread
cron.start()




# This function was used to build all entities required for dialog flow, not used in production (only for config)
def build_coincap_entities_json(filename):
    api_url = "https://api.coincap.io/v2/assets?limit=2000"
    response = requests.get(api_url)
    response = response.json()
    raw_list = []
    # build a raw_list based on json spec from dialogflow for adding entities using json 
    for item in response['data']:
        item_dict = {}
        item_dict['value'] = item['id']
        item_dict['synonyms'] = [item['id'], item['symbol'], item['name']]
        raw_list.append(item_dict)
    with open(filename, 'w') as outfile:  
        json.dump(raw_list, outfile, indent=4)
    # Once this file is written, simply open up the file and copy paste the json into dialogflow, saves time from manually adding every single coin as entity



# This function grabs data from coincap every x mins, and locally stors all the stats required   
@cron.interval_schedule(minutes=coincap_refresh_interval_mins)
def update_crypto_data():
    global crypto_data 
    api_url = "https://api.coincap.io/v2/assets?limit=2000"
    try:
        response = requests.get(api_url)
        response = response.json()
        data = response.get('data', [])
        for item in data:
            coin = item.get('id')
            price = item.get('priceUsd', None)
            volume = item.get('volumeUsd24Hr', None)
            supply = item.get('supply', None)
            change_24hr_percent = item.get('changePercent24Hr', None)
            crypto_data[coin] = {} 
            # Make sure entry exists, if None, just skip (some coins dont have details on coincap api)
            if price is not None:
                crypto_data[coin]['price'] = round(float(price), 4)
            if volume is not None:
                crypto_data[coin]['volume'] = round(float(volume) , 4)
            if supply is not None:
                crypto_data[coin]['supply'] = round(float(supply), 4)
            if change_24hr_percent is not None:
                crypto_data[coin]['change_24hr_percent'] = round(float(change_24hr_percent), 4)

        print("Grabbed data from coincap.io!")
    except Exception as e:
        print("Exception ad update_price_dict() : %s"%e)
          
# This function reads crypto_data and returns the price 
def get_price(coin):
    global crypto_data 
    coin = coin.lower()
    stats = crypto_data.get(coin, {})
    price = stats.get('price', "No price data available")
    return price 
# This function reads crypto_data and returns the volumeUsd24Hr
def get_volume(coin):
    global crypto_data 
    coin = coin.lower()
    stats = crypto_data.get(coin, {})
    volume = stats.get('volume', "No volume data available")
    return volume 
# This function reads crypto_data and returns the supply 
def get_supply(coin):
    global crypto_data 
    coin = coin.lower()
    stats = crypto_data.get(coin, {})
    supply = stats.get('supply', "No supply data available")
    return supply

def get_change(coin):
    global crypto_data
    coin = coin.lower()
    stats = crypto_data.get(coin, {})
    change = stats.get('change_24hr_percent', "No 24 hour change data available")
    return change 




# Simple function that takes text and get the intent, entities and response from Dialogflow (entities are actually inside parameters)
def get_intent_from_text(project_id, session_id, text, language_code):
    # create a session 
    global intent_cofig
    session_client = dialogflow.SessionsClient(credentials=creds)
    session = session_client.session_path(project_id, session_id)

    # Convert text to the way dialogflow needs it 
    text_input = dialogflow.types.TextInput(
        text=text, language_code=language_code)
    query_input = dialogflow.types.QueryInput(text=text_input)

    # Get the response from dialogflow api 
    response = session_client.detect_intent(
        session=session, query_input=query_input)

    #print('=' * 20)
    # print the querry text as parsed by dialogflow 
    print('Query text: %s'%(response.query_result.query_text))

    # get the parameters we need 
    detected_intent = response.query_result.intent.display_name
    detected_intent_confidence = response.query_result.intent_detection_confidence
    bots_response = str(response.query_result.fulfillment_text)
    parameters = MessageToJson(response.query_result.parameters)

    # Return these parameters 
    return detected_intent, parameters, bots_response  


## This is where we decide what to do. We use intent config to check if intent is inside, if yes call the function that has the same name as the intent, return the data in format required
def nlu_core(detected_intent, parameters, bots_response):
    global intent_cofig
    print(parameters)

    # Check if coin is configured (This makes sure that there was an Entity identified by dialogflow )
    try:
        parameters = json.loads(parameters)
        coin = parameters.get("Coins", None)
    except Exception as e:
        print(e)
        coin = None 
    print(coin)
    available_intents = intent_cofig.keys()

    if (detected_intent in available_intents) and coin:
        data = eval(detected_intent + "(coin)")
        if type(data) == float:
            data = "{:,}".format(data)
        bots_response = bots_response + (intent_cofig[detected_intent])%(coin, data)

    print('Response: %s'%bots_response)
    return bots_response
  

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    global project_id
    print("Handle_command: %s, channel:%s"%(command, channel))


    detected_intent, parameters, bots_original_response = get_intent_from_text(project_id, '1231424315', str(command), 'en')

    bots_parsed_response = nlu_core(detected_intent, parameters, bots_original_response)
    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=bots_parsed_response or default_response
    )



if __name__ == "__main__":
    update_crypto_data()
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")