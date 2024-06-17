import os
import pytz
import logging
from hosting_reminder_functions import *

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WA_API_KEY = os.getenv("WA_API_KEY")
RH_API_KEY = os.getenv("RH_API_KEY")
SERVER_ID = os.getenv("SERVER_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TEST_CHANNEL_ID = int(os.getenv("TEST_CHANNEL_ID"))

#main functionality

logging.info("Starting hosting open hours reminder script")

current_time = int(time.time())# - 9 * 3600 #offsets for testing

local_timezone = pytz.timezone('US/Central')
today = datetime.now(local_timezone) # - timedelta(days=1)
formatted_date = f"{today.month}/{today.day}/{today.year}"

tour_summary = find_tours(formatted_date)

print(tour_summary)

print(f"Current time: {current_time}")

discord_id = find_open_hours_host(RH_API_KEY, CHANNEL_ID, SERVER_ID, current_time)

if discord_id == None:
    send_discord_reminder(DISCORD_BOT_TOKEN, discord_id, CHANNEL_ID, f"No one is signed up to host this evening. Please address accordingly.\n {tour_summary}")
    exit()

discord_username = get_discord_username(DISCORD_BOT_TOKEN, discord_id)

access_token = get_wild_apricot_access_token(WA_API_KEY)
wild_apricot_user_id = find_contact_by_discord_username(discord_username, access_token)

if wild_apricot_user_id == None:
    logging.info(f"Contact not found, sending discord message to {discord_id}")
    send_discord_reminder(DISCORD_BOT_TOKEN, discord_id, CHANNEL_ID, f"RMM Open Hours starts in 2 hours!\n {tour_summary}")
    exit()

email, first_name = get_contact_info(wild_apricot_user_id, access_token)

html_template = read_template_file("reminder_email_template.html")

email_body = fill_email_template(first_name, html_template)

send_discord_reminder(DISCORD_BOT_TOKEN, discord_id, CHANNEL_ID, f"RMM Open Hours starts in 2 hours!\n {tour_summary}")
send_email(access_token, email_body, wild_apricot_user_id, first_name, email)



