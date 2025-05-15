#!/usr/bin/env python3
import logging
import os
import time
from datetime import datetime

import click
from dotenv import load_dotenv
from garminconnect import Garmin
from stravalib.client import Client

logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()


def get_garmin_client():
    """Initialize and authenticate Garmin Connect client."""
    try:
        client = Garmin(
            email=os.getenv("GARMIN_EMAIL"), password=os.getenv("GARMIN_PASSWORD")
        )
        client.login()
        return client
    except Exception as e:
        click.echo(f"Error connecting to Garmin: {str(e)}", err=True)
        raise


def get_strava_client():
    """Initialize and authenticate Strava client."""
    try:
        client = Client()
        client.access_token = os.getenv("STRAVA_ACCESS_TOKEN")
        client.refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
        client.token_expires_at = int(os.getenv("STRAVA_TOKEN_EXPIRES_AT", 0))

        # Refresh token if expired
        if datetime.fromtimestamp(client.token_expires_at) <= datetime.now():
            refresh_response = client.refresh_access_token(
                client_id=os.getenv("STRAVA_CLIENT_ID"),
                client_secret=os.getenv("STRAVA_CLIENT_SECRET"),
                refresh_token=client.refresh_token,
            )
            client.access_token = refresh_response["access_token"]
            client.refresh_token = refresh_response["refresh_token"]
            client.token_expires_at = refresh_response["expires_at"]

            # Update .env file with new tokens
            update_env_file(refresh_response)

        return client
    except Exception as e:
        click.echo(f"Error connecting to Strava: {str(e)}", err=True)
        raise


def update_env_file(token_data):
    """Update the .env file with new Strava tokens."""
    env_path = ".env"
    if not os.path.exists(env_path):
        click.echo("Error: .env file not found", err=True)
        return

    with open(env_path, "r") as f:
        lines = f.readlines()

    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("STRAVA_ACCESS_TOKEN="):
                f.write(f"STRAVA_ACCESS_TOKEN={token_data['access_token']}\n")
            elif line.startswith("STRAVA_REFRESH_TOKEN="):
                f.write(f"STRAVA_REFRESH_TOKEN={token_data['refresh_token']}\n")
            elif line.startswith("STRAVA_TOKEN_EXPIRES_AT="):
                f.write(f"STRAVA_TOKEN_EXPIRES_AT={token_data['expires_at']}\n")
            else:
                f.write(line)


def sync_activity(garmin, activity, dry_run=False, max_attempts=3):
    activity_id = activity["activityId"]

    # Download activity data
    activity_data = garmin.download_activity(
        activity_id, dl_fmt=Garmin.ActivityDownloadFormat.TCX
    )

    if dry_run:
        click.echo(f"[DRY RUN] Would upload activity: {activity.get('activityName', 'Garmin Activity')}")
        return activity_id

    # Upload to Strava
    strava = get_strava_client()

    upload = strava.upload_activity(
        activity_file=activity_data,
        data_type="tcx",
        name=activity.get("activityName", "Garmin Activity"),
        description=f"Synced from Garmin Connect on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with https://bit.ly/garmin2strava",
    )

    # Wait for the upload to complete and get the activity ID
    attempts = 0
    strava_activity_id = None
    while attempts < max_attempts:
        upload.poll()
        if upload.activity_id:
            strava_activity_id = upload.activity_id
            activity_url = f"https://www.strava.com/activities/{strava_activity_id}"
            click.echo(f"Activity URL: {activity_url}")
            break
        elif upload.error:
            click.echo(f"Upload status error: {upload.error}", err=True)
            break
        time.sleep(1)
        attempts += 1
    else:
        click.echo(f"Failed to get upload status after {max_attempts} attempts", err=True)
        return None

    return strava_activity_id


@click.command()
@click.option("--limit", default=1, help="Number of activities to sync")
@click.option("--dry-run", is_flag=True, help="Download activities but don't upload to Strava")
def sync(limit, dry_run):
    """Sync last N (defined by limit) Garmin activities to Strava."""
    try:
        # Get latest activity from Garmin
        garmin = get_garmin_client()
        activities = garmin.get_activities(start=0, limit=limit)

        if not activities:
            click.echo("No activities found in Garmin")
            return

        if dry_run:
            click.echo("Running in dry-run mode. No activities will be uploaded to Strava.")
            
        # Process the activities
        for activity in reversed(activities[:limit]):
            activity_id = sync_activity(garmin, activity, dry_run=dry_run)
            
            if dry_run:
                click.echo(f"[DRY RUN] Downloaded Garmin activity {activity_id}")
            else:
                click.echo(f"Successfully synced Garmin activity {activity_id} to Strava")

    except Exception as e:
        click.echo(f"Error during sync: {str(e)}", err=True)
        raise


if __name__ == "__main__":
    sync()
