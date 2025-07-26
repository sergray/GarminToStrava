import os

import click
from garminconnect import Garmin

from garmin2strava.garmin2strava import (
    choose_activities_interactively,
    get_garmin_client,
    sync_activity,
    upload_file_to_strava,
)


@click.command()
@click.option("--limit", default=1, help="Number of activities to sync")
@click.option(
    "--dry-run", is_flag=True, help="Download activities but don't upload to Strava"
)
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
            click.echo(
                "Running in dry-run mode. No activities will be uploaded to Strava."
            )

        # Process the activities
        for activity in reversed(activities[:limit]):
            activity_id = sync_activity(garmin, activity, dry_run=dry_run)

            if dry_run:
                click.echo(f"[DRY RUN] Downloaded Garmin activity {activity_id}")
            else:
                click.echo(
                    f"Successfully synced Garmin activity {activity_id} to Strava"
                )

    except Exception as e:
        click.echo(f"Error during sync: {str(e)}", err=True)
        raise


@click.command()
@click.option("--limit", default=20, help="Number of recent activities to choose from")
@click.option(
    "--output-dir",
    default="downloads",
    help="Directory to save downloaded activity files",
)
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

        click.echo(
            f"Downloading {len(selected_activities)} selected activities to {output_dir}..."
        )

        # Download the selected activities
        for activity in selected_activities:
            activity_id = activity["activityId"]
            activity_name = activity.get("activityName", "Garmin_Activity")
            start_time = activity.get("startTimeLocal", "unknown_time")

            # Create a safe filename
            # Remove/replace problematic characters
            safe_name = "".join(
                c for c in activity_name if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            safe_name = safe_name.replace(" ", "_")

            # Format: YYYY-MM-DD_ActivityName_ID.tcx
            if start_time != "unknown_time":
                try:
                    # Parse start time to get date part
                    date_part = (
                        start_time.split("T")[0]
                        if "T" in start_time
                        else start_time.split(" ")[0]
                    )
                    filename = f"{date_part}_{safe_name}_{activity_id}.tcx"
                except:
                    filename = f"{safe_name}_{activity_id}.tcx"
            else:
                filename = f"{safe_name}_{activity_id}.tcx"

            filepath = os.path.join(output_dir, filename)

            # Download activity data
            activity_data = garmin.download_activity(
                activity_id, dl_fmt=Garmin.ActivityDownloadFormat.TCX
            )

            # Save to file
            with open(filepath, "wb") as f:
                f.write(activity_data)

            click.echo(f"Downloaded: {filename}")

        click.echo(
            f"Successfully downloaded {len(selected_activities)} activities to {output_dir}"
        )

    except Exception as e:
        click.echo(f"Error during download: {str(e)}", err=True)
        raise


@click.command()
@click.argument("files", nargs=-1, required=True)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be uploaded but don't actually upload",
)
def upload(files, dry_run):
    """Upload TCX activity files to Strava."""
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

    click.echo(f"\nUpload summary:")
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
