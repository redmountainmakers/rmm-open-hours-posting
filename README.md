# Red Mountain Makers Open Hours Posting

This repository contains a script and associated GitHub Action to automate the posting of open hours for the Red Mountain Makers on Discord. It uses the "RMM-Helper" discord bot as a user 

## Overview

1. **[discord_open_hours_posting.py](https://github.com/redmountainmakers/rmm-open-hours-posting/blob/main/discord_open_hours_posting.py)**: This Python script is responsible for generating and posting events on Discord for the open hours of Red Mountain Makers. The script uses the `discord.py` library to interact with Discord and `aiohttp` to make HTTP requests. The events are scheduled for Tuesdays, Thursdays, Saturdays, and Sundays.

2. **[GitHub Action Workflow](https://github.com/redmountainmakers/rmm-open-hours-posting/blob/main/.github/workflows/github-actions-rmm-open-hours.yml)**: This workflow is set up to run the script automatically on a schedule. It checks out the repository, sets up Python, installs the required dependencies, and then runs the `discord_open_hours_posting.py` script.

3. **[requirements.txt](https://github.com/redmountainmakers/rmm-open-hours-posting/blob/main/requirements.txt)**: Lists the Python dependencies required to run the script.

## Setup

1. **Environment Variables**: The script requires several environment variables to be set:
   - `DISCORD_BOT_TOKEN`: Token for the Discord bot.
   - `RH_API_KEY`: API key for the Raid Helper.
   - `RH_API_KEY`: API key for Wild Apricot.
   - `RAIDHELPER_LEADER_ID`: Leader ID for the Raid Helper.
   - `SERVER_ID`: Discord server ID.
   - `CHANNEL_ID`: Discord channel ID where the events will be posted.

2. **Dependencies**: Install the required Python packages using:
   pip install -r requirements.txt
3. **Running the Script**: You can run the script using:
  python discord_open_hours_posting.py

4. **GitHub Action**: The action is scheduled to run on the 20th of every month at 7 PM CST. It uses the environment variables set in the repository's secrets.
