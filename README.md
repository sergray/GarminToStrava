# Garmin to Strava Sync Tool

A command-line tool that automatically syncs latest Garmin activity to Strava.

## Setup

1. https://docs.astral.sh/uv/getting-started/installation/ `uv` 

2. Install the required dependencies:
```bash
uv sync
```

3. Create a `.env` file based on `.env.example` and fill in credentials:
   - Garmin Connect credentials (email and password)
   - Strava API credentials (you can get these from [Strava API Settings](https://www.strava.com/settings/api))

## Strava API Setup

1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create a new application
3. Set the "Authorization Callback Domain" to `localhost`
4. Copy the Client ID and Client Secret to your `.env` file
5. Run `uv run auth_strava.py`

## Usage

Run the sync command:
```bash
uv run garmin2strava.py
```

The tool will:
1. Connect to Garmin account
2. Download latest activity
3. Upload it to Strava
4. Automatically handle token refresh when needed
