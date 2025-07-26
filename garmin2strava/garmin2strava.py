import logging
import os
import sys
import time
from datetime import datetime

import click
import questionary
from dotenv import load_dotenv
from garminconnect import Garmin
from stravalib.client import Client

from garmin2strava.auth_strava import update_env_file

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


def upload_file_to_strava(filepath, dry_run=False, max_attempts=3):
    """Upload a single TCX file to Strava."""
    if not os.path.exists(filepath):
        click.echo(f"Error: File not found: {filepath}", err=True)
        return None

    if not filepath.lower().endswith(".tcx"):
        click.echo(
            f"Warning: File {filepath} is not a TCX file, but will attempt upload anyway"
        )

    # Extract activity name from filename
    filename = os.path.basename(filepath)
    # Remove extension and replace underscores with spaces for better readability
    activity_name = os.path.splitext(filename)[0].replace("_", " ")

    if dry_run:
        click.echo(f"[DRY RUN] Would upload file: {filepath} as '{activity_name}'")
        return filepath

    try:
        # Read file content
        with open(filepath, "rb") as f:
            activity_data = f.read()

        # Upload to Strava
        strava = get_strava_client()

        upload = strava.upload_activity(
            activity_file=activity_data,
            data_type="tcx",
            name=activity_name,
            description=f"Uploaded from local file on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with https://bit.ly/garmin2strava",
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
            click.echo(
                f"Failed to get upload status after {max_attempts} attempts", err=True
            )
            return None

        return strava_activity_id

    except Exception as e:
        click.echo(f"Error uploading file {filepath}: {str(e)}", err=True)
        return None


def sync_activity(garmin, activity, dry_run=False, max_attempts=3):
    activity_id = activity["activityId"]

    # Download activity data
    activity_data = garmin.download_activity(
        activity_id, dl_fmt=Garmin.ActivityDownloadFormat.TCX
    )

    if dry_run:
        click.echo(
            f"[DRY RUN] Would upload activity: {activity.get('activityName', 'Garmin Activity')}"
        )
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
        click.echo(
            f"Failed to get upload status after {max_attempts} attempts", err=True
        )
        return None

    return strava_activity_id


def choose_activities_interactively(activities):
    """Prompt user to select one or more activities to download using an interactive checkbox list."""
    choices = []
    for activity in activities:
        name = activity.get("activityName", "Garmin Activity")
        start = activity.get("startTimeLocal", "?")
        act_id = activity.get("activityId", "?")
        label = f"{start} | {name} | ID: {act_id}"
        choices.append(questionary.Choice(title=label, value=activity))
    result = questionary.checkbox(
        "Select activities to download (j/k to move, space to select, enter to confirm, esc to cancel):",
        choices=choices,
        validate=lambda a: True if a else "Select at least one activity.",
    ).ask()
    if result is None:
        click.echo("Cancelled.")
        sys.exit(0)
    return result
