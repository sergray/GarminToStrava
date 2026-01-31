#!/usr/bin/env python3
import logging
import os
import time
from datetime import datetime
import sys

import click
from dotenv import load_dotenv
from garminconnect import Garmin
from stravalib.client import Client
import questionary

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


def upload_file_to_strava(filepath, dry_run=False, max_attempts=3):
    """Upload a single activity file to Strava (TCX/GPX/FIT, optionally gzipped)."""
    if not os.path.exists(filepath):
        click.echo(f"Error: File not found: {filepath}", err=True)
        return None

    # Determine Strava upload data_type based on extension.
    # Strava supports: tcx, gpx, fit (and .gz variants).
    filepath_lower = filepath.lower()
    if filepath_lower.endswith(".tcx.gz"):
        data_type = "tcx.gz"
        name_suffix = ".tcx.gz"
    elif filepath_lower.endswith(".gpx.gz"):
        data_type = "gpx.gz"
        name_suffix = ".gpx.gz"
    elif filepath_lower.endswith(".fit.gz"):
        data_type = "fit.gz"
        name_suffix = ".fit.gz"
    else:
        ext = os.path.splitext(filepath_lower)[1].lstrip(".")
        supported = {"tcx", "gpx", "fit"}
        if ext in supported:
            data_type = ext
            name_suffix = f".{ext}"
        else:
            data_type = ext or "tcx"
            name_suffix = os.path.splitext(os.path.basename(filepath))[1]
            click.echo(
                f"Warning: File {filepath} has an unsupported extension; will attempt upload with data_type='{data_type}'"
            )
    
    # Extract activity name from filename
    filename = os.path.basename(filepath)
    # Remove extension and replace underscores with spaces for better readability
    if name_suffix and filename.lower().endswith(name_suffix):
        base_name = filename[: -len(name_suffix)]
    else:
        base_name = os.path.splitext(filename)[0]
    activity_name = base_name.replace("_", " ")
    
    if dry_run:
        click.echo(
            f"[DRY RUN] Would upload file: {filepath} as '{activity_name}' (data_type='{data_type}')"
        )
        return filepath
    
    try:
        # Read file content
        with open(filepath, 'rb') as f:
            activity_data = f.read()
        
        # Upload to Strava
        strava = get_strava_client()
        
        upload = strava.upload_activity(
            activity_file=activity_data,
            data_type=data_type,
            name=activity_name,
            description="Uploaded from local file with https://bit.ly/garmin2strava",
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
        click.echo(f"[DRY RUN] Would upload activity: {activity.get('activityName', 'Garmin Activity')}")
        return activity_id

    # Upload to Strava
    strava = get_strava_client()

    upload = strava.upload_activity(
        activity_file=activity_data,
        data_type="tcx",
        name=activity.get("activityName", "Garmin Activity"),
        description="Synced from Garmin Connect with https://bit.ly/garmin2strava",
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
        validate=lambda a: True if a else "Select at least one activity."
    ).ask()
    if result is None:
        click.echo("Cancelled.")
        sys.exit(0)
    return result


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


@click.command()
@click.option("--limit", default=20, help="Number of recent activities to choose from")
@click.option("--output-dir", default="downloads", help="Directory to save downloaded activity files")
def download(limit, output_dir):
    """Interactively choose and download Garmin activities as TCX files."""
    try:
        # Get recent activities from Garmin
        garmin = get_garmin_client()
        activities = garmin.get_activities(start=0, limit=limit)

        if not activities:
            click.echo("No activities found in Garmin")
            return
            
        # Let user choose activities interactively
        selected_activities = choose_activities_interactively(activities)
        
        if not selected_activities:
            click.echo("No activities selected.")
            return
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            click.echo(f"Created directory: {output_dir}")
        
        click.echo(f"Downloading {len(selected_activities)} selected activities to {output_dir}...")
        
        # Download the selected activities
        for activity in selected_activities:
            activity_id = activity["activityId"]
            activity_name = activity.get("activityName", "Garmin_Activity")
            start_time = activity.get("startTimeLocal", "unknown_time")
            
            # Create a safe filename
            # Remove/replace problematic characters
            safe_name = "".join(c for c in activity_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            
            # Format: YYYY-MM-DD_ActivityName_ID.tcx
            if start_time != "unknown_time":
                try:
                    # Parse start time to get date part
                    date_part = start_time.split('T')[0] if 'T' in start_time else start_time.split(' ')[0]
                    filename = f"{date_part}_{safe_name}_{activity_id}.tcx"
                except Exception:
                    filename = f"{safe_name}_{activity_id}.tcx"
            else:
                filename = f"{safe_name}_{activity_id}.tcx"
            
            filepath = os.path.join(output_dir, filename)
            
            # Download activity data
            activity_data = garmin.download_activity(
                activity_id, dl_fmt=Garmin.ActivityDownloadFormat.TCX
            )
            
            # Save to file
            with open(filepath, 'wb') as f:
                f.write(activity_data)
            
            click.echo(f"Downloaded: {filename}")

        click.echo(f"Successfully downloaded {len(selected_activities)} activities to {output_dir}")

    except Exception as e:
        click.echo(f"Error during download: {str(e)}", err=True)
        raise


@click.command()
@click.argument('files', nargs=-1, required=True)
@click.option("--dry-run", is_flag=True, help="Show what would be uploaded but don't actually upload")
def upload(files, dry_run):
    """Upload activity files (TCX/GPX/FIT, optionally gzipped) to Strava."""
    if not files:
        click.echo("Error: No files specified", err=True)
        return
        
    if dry_run:
        click.echo("Running in dry-run mode. No files will be uploaded to Strava.")
    
    successful_uploads = 0
    failed_uploads = 0
    
    for filepath in files:
        click.echo(f"Processing file: {filepath}")
        
        result = upload_file_to_strava(filepath, dry_run=dry_run)
        
        if result:
            successful_uploads += 1
            if dry_run:
                click.echo(f"[DRY RUN] Would upload: {filepath}")
            else:
                click.echo(f"Successfully uploaded: {filepath}")
        else:
            failed_uploads += 1
            click.echo(f"Failed to upload: {filepath}")
    
    click.echo("\nUpload summary:")
    if dry_run:
        click.echo(f"[DRY RUN] Would upload {successful_uploads} files")
        if failed_uploads > 0:
            click.echo(f"[DRY RUN] Would fail to upload {failed_uploads} files")
    else:
        click.echo(f"Successfully uploaded: {successful_uploads} files")
        if failed_uploads > 0:
            click.echo(f"Failed to upload: {failed_uploads} files")


@click.group()
def cli():
    """Garmin to Strava CLI"""
    pass

cli.add_command(sync)
cli.add_command(download)
cli.add_command(upload)

if __name__ == "__main__":
    cli()
