import discord
import datetime
import calendar
import pytz
import aiohttp
import asyncio
import os

# Retrieve environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WA_API_KEY = os.getenv("WA_API_KEY")
RAIDHELPER_LEADER_ID = os.getenv("RAIDHELPER_LEADER_ID")
SERVER_ID = os.getenv("SERVER_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)


def generate_event_dates_for_month(year, month):
    event_dates = []
    first_day, days_in_month = calendar.monthrange(year, month)

    for day in range(1, days_in_month + 1):
        current_date = datetime.date(year, month, day)
        weekday = current_date.weekday()

        if weekday == calendar.TUESDAY or weekday == calendar.THURSDAY:
            event_dates.append(current_date)
        elif weekday == calendar.SUNDAY:
            event_dates.append(current_date)

    return event_dates


async def create_event_for_date(date, time, duration):
    event_datetime = datetime.datetime.combine(date, time)
    cst_timezone = pytz.timezone("America/Chicago")
    cst_datetime = cst_timezone.localize(event_datetime)
    utc_datetime = cst_datetime.astimezone(pytz.utc)
    unix_timestamp = int(utc_datetime.timestamp())

    return {
        "date": unix_timestamp,
        "duration": duration,
    }

async def post_event(event, channel_id):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"https://raid-helper.dev/api/v2/servers/{SERVER_ID}/channels/{channel_id}/event",
                headers={"Authorization": WA_API_KEY, "Content-Type": "application/json; charset=utf-8"},
                json=event,
            ) as response:
                response.raise_for_status()
                print(f'Posted event "{event["title"]}"')
                print(await response.text())
        except aiohttp.ClientResponseError as e:
            print(f"Error posting event: {e.status} - {e.message}")
        except Exception as e:
            print(f"Error posting event: {e}")

year, month = datetime.date.today().year, datetime.date.today().month + 1
event_dates = generate_event_dates_for_month(year, month)
tue_thu_time = datetime.time(hour=12, minute=0)
sunday_time = datetime.time(hour=11, minute=0)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

    for date in event_dates:
        if date.weekday() == calendar.SUNDAY:
            time = sunday_time
            duration = 180
            day = "Sunday"
        else:
            time = tue_thu_time
            duration = 120
            day = "Tuesday" if date.weekday() == calendar.TUESDAY else "Thursday"

        event_data = await create_event_for_date(date, time, duration)

        event = {
            "title": f"{day} Open Hours",
            "description": "",
            "templateId": 1,
            "date": event_data["date"],
            "leaderId": RAIDHELPER_LEADER_ID,
            "advancedSettings": {"duration": event_data["duration"], "limit": 1, "reminder": 120},
        }

        print(f"Event JSON data: {event}")

        post_data = {
            **event,
            "date": event["date"],
            "time": event["date"],
        }

        await post_event(post_data, CHANNEL_ID)

        # Optionally, you might want to add a delay between posting events
        # to avoid hitting API rate limits.
        await asyncio.sleep(5)  # Wait for 5 seconds before posting the next event
    await channel.send("/overview server")
    await client.close()
# Log in to Discord
client.run(DISCORD_BOT_TOKEN)
