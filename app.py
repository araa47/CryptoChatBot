import dialogflow_v2 as dialogflow
from google.protobuf.json_format import MessageToJson
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
import json 
import os
import time
import re
from slackclient import SlackClient
import requests 

from dotenv import load_dotenv, find_dotenv
from apscheduler.scheduler import Scheduler

cron = Scheduler(daemon=True)
# Explicitly kick off the background thread
cron.start()

# global price dict (used to store prices locally)
prices = {}
# google auth scope 
scope = ["https://www.googleapis.com/auth/cloud-platform"]
# constants for slack 
RTM_READ_DELAY = 1 # 1 second delay between reading from RT
# this regex checks if someone mentioned the bot 
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
# dialogflow project id 
project_id = os.getenv("PROJECT_ID")
# get refresh interval for coincap data
coincap_refresh_interval_mins = int(os.getenv("COINCAP_REFRESH_INTERVAL_MINS"))
# get slackbot token 
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
# get environment 
env = os.getenv("ENVIRONMENT")



intent_cofig = {  
    "get_price": " The current price of %s is %s USD",
    "get_volume": " The current 24 hour USD Volume for %s is %s USD",
    "get_supply": " The current circulating supply of %s is %s coins"
}




#print(project_id, coincap_refresh_interval_mins, SLACK_BOT_TOKEN, env)
## local envirnoment
if env == "dev":

    secret = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    creds = service_account.Credentials.from_service_account_file(secret)
   # creds = ServiceAccountCredentials.from_service_account_file(secret, scope)
else:
## Heroku 
    secret = json.loads((os.getenv("GOOGLE_APPLICATION_CREDENTIALS")))
    creds = service_account.Credentials.from_service_account_info(secret)
    #creds = ServiceAccountCredentials.from_service_account_info(secret, scope)



# instantiate Slack client
slack_client = SlackClient(SLACK_BOT_TOKEN)

# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# ## THis function was used to build all entities required for dialog flow, not used in production 
# def build_coincap_entities_json(filename):
#     api_url = "https://api.coincap.io/v2/assets?limit=2000"
       
#     response = requests.get(api_url)
#     response = response.json()

#     raw_list = []

#     for item in response['data']:
#         item_dict = {}
#         item_dict['value'] = item['id']
#         item_dict['synonyms'] = [item['id'], item['symbol'], item['name']]
#         raw_list.append(item_dict)
#     with open(filename, 'w') as outfile:  
#         json.dump(raw_list, outfile, indent=4)

# This get prices 
@cron.interval_schedule(minutes=coincap_refresh_interval_mins)
def update_price_dict():
    global prices 
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
            prices[coin] = {} 
            if price is not None:
                prices[coin]['price'] = round(float(price), 4)
            if volume is not None:
                prices[coin]['volume'] = round(float(volume) , 4)
            if supply is not None:
                prices[coin]['supply'] = round(float(supply), 4)
        print("Grabbed data from coincap.io!")
    except Exception as e:
        print("Exception ad update_price_dict() : %s"%e)
          


def get_price(coin):
    global prices 
    coin = coin.lower()
    stats = prices.get(coin, {})
    price = stats.get('price', "No price data available")
    return price 

def get_volume(coin):
    global prices 
    coin = coin.lower()
    stats = prices.get(coin, {})
    volume = stats.get('volume', "No volume data available")
    return volume 
def get_supply(coin):
    global prices 
    coin = coin.lower()
    stats = prices.get(coin, {})
    supply = stats.get('supply', "No supply data available")
    return supply
# Simple function that takes text and get the intent and response from google 
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


    try: 
        parameters = json.loads(parameters)
        coin = parameters.get("Coins", None)
    except Exception as e:
        print(e)
        coin = None 

    available_intents = intent_cofig.keys()

    if (detected_intent in available_intents) and coin:
        data = eval(detected_intent + "(coin)")
        if type(data) == float:
            data = "{:,}".format(data)
        bots_response = bots_response + (intent_cofig[detected_intent])%(coin, data)

    # if detected_intent == "get_price" and coin:
    #     price = get_price(coin)
    #     bots_response = bots_response +" The current price of %s is %s USD"%(coin, "{:,}".format(price))

    # if detected_intent == "get_volume" and coin:
    #     volume = get_volume(coin)
    #     bots_response = bots_response + " The current 24 hour USD Volume for %s is %s USD"%(coin, "{:,}".format(volume))

    # if detected_intent == "get_supply" and coin:
    #     supply = get_supply(coin)
    #     bots_response = bots_response + " There is currently %s %s circulating."%("{:,}".format(supply), coin)


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


    bots_response = get_intent_from_text(project_id, '1231424315', str(command), 'en')


    slack_client.api_call(
        "chat.postMessage",
        channel=channel,
        text=bots_response or default_response
    )



if __name__ == "__main__":
    update_price_dict()
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