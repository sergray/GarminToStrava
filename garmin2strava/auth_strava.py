import os
import threading
import time
import webbrowser

from dotenv import load_dotenv
from flask import Flask, request
from stravalib.client import Client

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Define your client ID and secret
load_dotenv()


client_id = os.getenv("STRAVA_CLIENT_ID")
client_secret = os.getenv("STRAVA_CLIENT_SECRET")

# Define the scope
request_scope = ["read_all", "activity:read_all", "activity:write"]

# Set a redirect URL
redirect_url = "http://127.0.0.1:5000/authorization"

# Global variable to store the authorization code
auth_code = None

# Create Flask app
app = Flask(__name__)


@app.route("/authorization")
def authorization():
    global auth_code
    code = request.args.get("code")
    if code:
        auth_code = code
        return "Authorization successful! You can close this window."
    return "Authorization failed. Please try again."


def run_flask():
    app.run(port=5000)


# Save the tokens to .env file
def update_env_file(token_data):
    env_path = os.path.join(THIS_DIR, "..", ".env")
    if not os.path.exists(env_path):
        print("Error: .env file not found")
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


def main():
    # Create a client object
    client = Client()

    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Generate the authorization URL
    url = client.authorization_url(
        client_id=client_id, redirect_uri=redirect_url, scope=request_scope
    )

    # Open the URL in a web browser
    webbrowser.open(url)

    # Wait for the authorization code
    while auth_code is None:
        time.sleep(0.1)

    # Exchange the code for an access token
    token_response = client.exchange_code_for_token(
        client_id=client_id, client_secret=client_secret, code=auth_code
    )

    # Use the access token to interact with Strava
    client.access_token = token_response["access_token"]

    # Update the .env file with the new tokens
    update_env_file(token_response)

    print("Successfully authenticated with Strava!")


if __name__ == "__main__":
    main()
