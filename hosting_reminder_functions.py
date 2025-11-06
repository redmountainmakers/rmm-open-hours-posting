import os
import time
import json
import discord
import requests
import logging
import base64
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta


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

def find_open_hours_host(api_key, channel_id, server_id, time):

    # Current time and 8 hours from now in Unix timestamp
    logging.info("Searching for open hours host")

    eight_hours_later = time + 8 * 3600

    # Set up the header
    headers = {
        'Authorization': api_key,
        'Page': '1',
        'IncludeSignUps': 'True',
        'ChannelFilter': str(channel_id),
        'StartTimeFilter': str(time),
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
            for signUp in response.json().get('postedEvents')[0]['signUps']:
                if signUp['className'] == "Accepted":
                    discord_id = signUp['userId']
                    return discord_id
        except:
            logging.info("Issue finding discord user from event. Error:", response.status_code, response.text)
            return None

        
    else:
        logging.error("Error:", response.status_code, response.text)
    
    return None

async def fetch_discord_username(discord_bot_token, discord_id):
    intents = discord.Intents.default()  # Use default intents
    intents.members = True  # Set to True if you need to access the members
    client = discord.Client(intents=intents)

    await client.login(discord_bot_token)
    try:
        user = await client.fetch_user(discord_id)
        return user.name  # or use user.display_name
    finally:
        await client.close()

def get_discord_username(discord_bot_token, discord_id):
    return asyncio.run(fetch_discord_username(discord_bot_token, discord_id))

async def send_discord_message(discord_bot_token, discord_user_id, channel_id, message):
    """Sends a message in a Discord channel and tags a user."""
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)


    notified_role_id = 839006433050886174 #Currently Leadership
    async def on_ready():
        print(f'Logged in as {client.user}')
        channel = client.get_channel(channel_id)
        if channel:
            if discord_user_id is None:
                await channel.send(f'<@&{notified_role_id}> {message}')
            else:
                await channel.send(f'<@{discord_user_id}> {message}')
        await client.close()

    client.event(on_ready)
    await client.start(discord_bot_token)

def send_discord_reminder(discord_bot_token, discord_user_id, channel_id, message):
    asyncio.run(send_discord_message(discord_bot_token, discord_user_id, channel_id, message))

def find_tours(date):
    # Set up Google Sheets API credentials
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    
    # Open the Google Sheet
    spreadsheet = client.open('Schedule a Tour (Responses)')
    sheet = spreadsheet.sheet1  # or use .worksheet('Sheet Name') for a specific sheet

    # Get all records from the sheet
    records = sheet.get_all_records()

    # Initialize summary string
    summary = f"Tour Summary for {date}:\n"

    found_tour = False

    # Check for rows with the specified date
    for record in records:
        if record['TOUR DATE'] == date:
            # Format the output for each matching record
            found_tour = True
            summary += f"Name: {record['NAME']}, Time: {record['Time']}, Phone Number: {record['PHONE NUMBER']}\n"
            summary += "Please provide the following information about each tour:\n\n"
            summary += "1. Did the tour occur?\n"
            summary += "2. What are their specific interests at RMM?\n"
            summary += "3. Do they have any specific questions about the space?\n"
    if not found_tour:
        summary = f"No tours are scheduled for {date}."

    return summary

