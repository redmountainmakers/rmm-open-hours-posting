import discord
import datetime
import pytz
import aiohttp
import asyncio
import os

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

# Retrieve environment variables
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WA_API_KEY = os.getenv("WA_API_KEY")
RAIDHELPER_LEADER_ID = os.getenv("RAIDHELPER_LEADER_ID")
SERVER_ID = os.getenv("SERVER_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TEST_CHANNEL_ID = os.getenv("TEST_CHANNEL_ID")

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

async def create_single_event():
    event_date = datetime.date(2023, 11, 1)  # November 1, 2023
    event_time = datetime.time(0, 0)  # Midnight
    
    event_data = await create_event_for_date(event_date, event_time, duration=120)  # 2-hour event

    event = {
        "title": "Test Event 2",
        "description": "A single test event",
        "templateId": 1,
        "date": event_data["date"],
        "leaderId": RAIDHELPER_LEADER_ID,
        "advancedSettings": {"duration": event_data["duration"], "limit": 1},
    }

    post_data = {
        **event,
        "date": event["date"],
        "time": event["date"],
    }
    
    await post_event(post_data, TEST_CHANNEL_ID)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await create_single_event()
    await client.close()

# Log in to Discord
client.run(DISCORD_BOT_TOKEN)
