import os
from hosting_reminder_functions import *

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
RH_API_KEY = os.getenv("RH_API_KEY")
SERVER_ID = os.getenv("SERVER_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TEST_CHANNEL_ID = int(os.getenv("TEST_CHANNEL_ID"))

one_day_from_now = int(time.time()) + 26 * 3600 #offset by 26 hours for testing doing a 24 hr notice to open hours

test_time = 1710201600

discord_id = find_open_hours_host(RH_API_KEY, CHANNEL_ID, SERVER_ID, one_day_from_now)

print(discord_id)


# if discord_id == None:
    #send_discord_reminder(DISCORD_BOT_TOKEN, discord_id, CHANNEL_ID, "No one is signed up to host tomorrow. Please address accordingly.")

# TODO
# if today is Monday:
    #pull events for the week, and send a summary to @leadership in the #leadership channel


