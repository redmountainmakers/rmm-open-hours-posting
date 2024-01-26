import os
import time
import discord
import requests
import logging
import base64
import asyncio

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WA_API_KEY = os.getenv("WA_API_KEY")
RH_API_KEY = os.getenv("RH_API_KEY")
SERVER_ID = os.getenv("SERVER_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TEST_CHANNEL_ID = int(os.getenv("TEST_CHANNEL_ID"))

log_file_path = 'hosting_reminder.log'
logging.basicConfig(level=logging.INFO, filename= log_file_path, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

def get_wild_apricot_access_token(api_key):
    """Obtains and returns an access token for the Wild Apricot API."""
    auth_url = 'https://oauth.wildapricot.org/auth/token'
    encoded_key = base64.b64encode(f'APIKEY:{api_key}'.encode()).decode()
    auth_headers = {'Authorization': f'Basic {encoded_key}', 'Content-Type': 'application/x-www-form-urlencoded'}
    auth_data = {'grant_type': 'client_credentials', 'scope': 'auto'}
    auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data)
    return auth_response.json().get('access_token')

def get_account_id(headers):
    """Retrieves the account ID."""
    api_base_url = 'https://api.wildapricot.org/v2.2'
    response = requests.get(f"{api_base_url}/accounts", headers=headers)
    if response.status_code != 200:
        logging.error(f"Error: Unable to retrieve account details. Status code: {response.status_code}")
        return None
    return response.json()[0]['Id']

def find_contact_by_discord_username(discord_username, access_token):
    """Finds a contact by Discord username."""
    api_base_url = 'https://api.wildapricot.org/v2.2'
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json', 'Accept': 'application/json'}
    
    account_id = get_account_id(headers)
    if not account_id:
        print("Error: Unable to retrieve account ID.")
        return None

    filter_query = f"$filter='Discord Username' eq '{discord_username}'"
    contacts_url = f"{api_base_url}/accounts/{account_id}/contacts?$async=false&{filter_query}"

    contacts_response = requests.get(contacts_url, headers=headers)

    if contacts_response.status_code != 200:
        print(f"Error: Unable to retrieve contacts. Status code: {contacts_response.status_code}")
        return None
    elif len(contacts_response.json().get("Contacts", [])) != 1:
        print("Error: incorrect number of contacts returned, expected 1.")
        return None
    else:
        return contacts_response.json().get("Contacts", [])[0].get("Id")

def get_contact_info(contact_id, access_token):
    """Retrieves the email address and first name of a contact given a contact ID."""
    api_base_url = 'https://api.wildapricot.org/v2.1'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    # Make an API request to retrieve the account details
    account_response = requests.get(f'{api_base_url}/accounts', headers=headers)
    if account_response.status_code != 200:
        logging.error(f'Error: Unable to retrieve account details. Status code: {account_response.status_code}')
        return

    account_id = account_response.json()[0]['Id']

    # Make an API request to retrieve the contact details
    contact_response = requests.get(f'{api_base_url}/accounts/{account_id}/contacts/{contact_id}', headers=headers)
    if contact_response.status_code != 200:
        logging.error(f'Error: Unable to retrieve contact details. Status code: {contact_response.status_code}')
        return

    contact_details = contact_response.json()

    # Get the email address, first name, and membership status from the contact details
    email = contact_details.get('Email', 'Unknown')
    first_name = contact_details.get('FirstName', 'Unknown')

    return email, first_name

def send_email(access_token, body, contact_id, first_name, email):


    """Sends a test email using the Wild Apricot API."""
    api_base_url = 'https://api.wildapricot.org/v2.2'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    account_response = requests.get(f'{api_base_url}/accounts', headers=headers)
    if account_response.status_code != 200:
        logging.error(f'Error: Unable to retrieve account details. Status code: {account_response.status_code}')
        return

    account_id = account_response.json()[0]['Id']

    # Prepare email data
    email_data = {
        "Subject": "Open Hours Reminder",
        "Body": body,
        "ReplyToAddress": "secretary@redmountainmakers.org",
        "ReplyToName": "Red Mountain Makers",
        "Recipients": [
            {
                "Id": contact_id,
                "Type": "IndividualContactRecipient",
                "Name": first_name,
                "Email": email,
            }
        ],
    }


    # Make an API request to send the email
    send_email_response = requests.post(f'{api_base_url}/rpc/{account_id}/email/SendEmail', headers=headers, json=email_data)
    
    if send_email_response.status_code != 200:
        logging.error(f'Error: Unable to send email. Status code: {send_email_response.status_code}')
        return False
    else:
        logging.info(f"Email sent successfully! to {first_name}")
        return True

def fill_email_template(Contact_First_Name, template):
    return template.format(Contact_First_Name=Contact_First_Name)

def read_template_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def find_open_hours_host(api_key, channel_id, server_id):

    # Current time and 8 hours from now in Unix timestamp
    current_time = int(time.time()) - 5 * 3600
    eight_hours_later = current_time + 8 * 3600

    # Set up the header
    headers = {
        'Authorization': api_key,
        'Page': '1',
        'IncludeSignUps': 'True',
        'ChannelFilter': str(channel_id),
        'StartTimeFilter': str(current_time),
        'EndTimeFilter': str(eight_hours_later)
    }

    # Endpoint URL
    url = f'https://raid-helper.dev/api/v3/servers/{server_id}/events'

    # Send the GET request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Process the response here
        try:
            discord_id = response.json().get('postedEvents')[0]['signUps'][0]['userId']
            return discord_id
        except:
            logging.info("Issue finding discord user from event. Error:", response.status_code, response.text)
            return None

        
    else:
        logging.error("Error:", response.status_code, response.text)
    
    return None

async def fetch_discord_username(discord_id):
    intents = discord.Intents.default()  # Use default intents
    intents.members = True  # Set to True if you need to access the members
    client = discord.Client(intents=intents)

    await client.login(DISCORD_BOT_TOKEN)
    try:
        user = await client.fetch_user(discord_id)
        return user.name  # or use user.display_name
    finally:
        await client.close()

def get_discord_username(discord_id):
    return asyncio.run(fetch_discord_username(discord_id))

async def send_discord_message(channel_id, discord_user_id, message):
    """Sends a message in a Discord channel and tags a user."""
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    backup_message = "No one is signed up to host this evening. Please address accordingly."

    async def on_ready():
        print(f'Logged in as {client.user}')
        channel = client.get_channel(channel_id)
        if channel:
            if discord_user_id is not None:
                await channel.send(f'<@Leadership> {message}')
            else:
                await channel.send(f'<@{discord_user_id}> {backup_message}')
        await client.close()

    client.event(on_ready)
    await client.start(DISCORD_BOT_TOKEN)

def send_discord_reminder(discord_user_id, message):
    asyncio.run(send_discord_message(CHANNEL_ID, discord_user_id, message))




#main functionality

logging.info("Starting hosting open hours reminder script")

discord_id = find_open_hours_host(RH_API_KEY, CHANNEL_ID, SERVER_ID)

if discord_id == None:
    send_discord_reminder(discord_id, "RMM Open Hours starts in 2 hours!")
    exit()

discord_username = get_discord_username(discord_id)

access_token = get_wild_apricot_access_token(WA_API_KEY)
wild_apricot_user_id = find_contact_by_discord_username(discord_username, access_token)

if wild_apricot_user_id == None:
    logging.info(f"Contact not found, sending discord message")
    send_discord_reminder(discord_id, "RMM Open Hours starts in 2 hours!")
    exit()

email, first_name = get_contact_info(wild_apricot_user_id, access_token)

html_template = read_template_file("reminder_email_template.html")

email_body = fill_email_template(first_name, html_template)

send_email(access_token, email_body, wild_apricot_user_id, first_name, email)
