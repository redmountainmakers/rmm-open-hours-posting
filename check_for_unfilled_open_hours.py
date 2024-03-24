import os
from datetime import datetime, timezone, timedelta
import time
from hosting_reminder_functions import *

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
RH_API_KEY = os.getenv("RH_API_KEY")
SERVER_ID = os.getenv("SERVER_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
TEST_CHANNEL_ID = int(os.getenv("TEST_CHANNEL_ID"))


log_file_path = 'hosting_reminder.log'
logging.basicConfig(level=logging.INFO, filename= log_file_path, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

logging.info(f"Starting to look 1 day ahead for open hours host")
one_day_from_now = int(time.time()) + 23 * 3600 #offset by 23 hours for testing doing a 24 hr notice to open hours
print(one_day_from_now)

# test_time = dt_cst = datetime(2024, 3, 12, 18, 55, tzinfo=timezone(timedelta(hours=-6)))
# print(test_time)
# unix_test_time = int(test_time.timestamp())
# print(unix_test_time)

discord_id = find_open_hours_host(RH_API_KEY, CHANNEL_ID, SERVER_ID, one_day_from_now)

print(discord_id)


if discord_id == None:
    send_discord_reminder(DISCORD_BOT_TOKEN, discord_id, CHANNEL_ID, "No one is signed up to host tomorrow. Please address accordingly.")
else:
    logging.info(f"Found host {discord_id} no notification necessary")

# TODO
# if today is Monday:
    #pull events for the week, and send a summary to @leadership in the #leadership channel


