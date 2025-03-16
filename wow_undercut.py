#!/usr/bin/python3
from __future__ import print_function
import os, json, time
from datetime import datetime
import requests

from wow_auto_undercut_update import update_region_undercut_json

print("Sleep 10 sec on start to avoid spamming the api")
time.sleep(10)

#### GLOBALS ####
try:
    config_data = json.load(open("wow_user_data/config/undercut/webhooks.json"))
    webhook_url = config_data["webhook"]
    autoupdate = config_data["autoupdate"]
    include_sold_not_found = config_data["include_sold_not_found"]
except FileNotFoundError:
    print(
        "Error: No webhook file found for undercut, add your webhook to wow_user_data/config/undercut/webhooks.json"
    )
    exit(1)
except KeyError:
    print(
        "Error: No webhook found in wow_user_data/config/undercut/webhooks.json add one in"
    )
    exit(1)

alert_record = []


def update_user_undercut_data():
    """Updates the user undercut data from a specified JSON file.
    Parameters:
        None
    Returns:
        None
    Processing Logic:
        - Utilizes global variables `undercut_alert_data`, `region`, and `home_realm_id`.
        - Conducts an automatic update if `autoupdate` is enabled.
        - Loads data from 'wow_user_data/undercut/region_undercut.json'.
        - Exits with an error message if the JSON data is missing or empty."""
    global undercut_alert_data
    global region
    global home_realm_id
    if autoupdate:
        update_region_undercut_json()
    undercut_alert_data = json.load(open("wow_user_data/undercut/region_undercut.json"))
    if not undercut_alert_data or len(undercut_alert_data) == 0:
        print(
            "Error please generate your undercut data from our addon: https://www.curseforge.com/wow/addons/saddlebag-exchange"
        )
        print("Then paste it into wow_user_data/undercut/region_undercut.json")
        print(
            "Or setup automatic updates with wow_user_data/undercut/addon_undercut.json"
        )
        exit(1)
    region = undercut_alert_data[0]["region"]
    home_realm_id = undercut_alert_data[0]["homeRealmName"]


def simple_undercut(json_data):
    snipe_results = requests.post(
        "http://api.saddlebagexchange.com/api/wow/regionundercut",
        json=json_data,
    ).json()

    return snipe_results


def get_update_timers(region, simple_undercut=False):
    """Fetch update timers for specified region, optionally using a simplified undercut logic.
    Parameters:
        - region (str): Region for which to fetch update timers (e.g., 'EU', 'US').
        - simple_undercut (bool, optional): If True, apply a simplified undercut logic affecting the dataset ID filtering.
    Returns:
        - list: A list of server update timers relevant to the provided region and logic.
    Processing Logic:
        - Fetches data from an external API using a POST request.
        - Filters dataset IDs based on the 'simple_undercut' flag and 'region' parameter.
        - Distinguishes dataset ID selection criteria when 'simple_undercut' is True or False.
    """
    print("Getting update timers")
    # get from api every time
    update_timers = requests.post(
        "http://api.saddlebagexchange.com/api/wow/uploadtimers",
        json={},
    ).json()["data"]

    # cover specific realms
    if simple_undercut:
        if region == "EU":
            update_id = -2
        else:
            update_id = -1
        server_update_times = [
            time_data
            for time_data in update_timers
            if time_data["dataSetID"] == update_id
        ]
    else:
        server_update_times = [
            time_data
            for time_data in update_timers
            if time_data["dataSetID"] not in [-1, -2] and time_data["region"] == region
        ]
        print(server_update_times)

    return server_update_times


def send_to_discord(embed, webhook_url):
    # Send message
    # print(f"sending embed to discord...")
    """Send an embed message to a Discord channel via a webhook.
    Parameters:
        - embed (dict): The embedded message content formatted as a dictionary.
        - webhook_url (str): The URL of the Discord webhook for sending messages.
    Returns:
        - None
    Processing Logic:
        - Makes an HTTP POST request to the Discord webhook with the provided embed.
        - Logs a success message if the status code of the response is 200 or 204.
        - Logs an error message containing the status code and response text if the request fails.
    """
    req = requests.post(webhook_url, json={"embeds": [embed]})
    if req.status_code != 204 and req.status_code != 200:
        print(f"Failed to send embed to discord: {req.status_code} - {req.text}")
    else:
        print(f"Embed sent successfully")


def create_embed(title, description, fields, color="red"):
    """Create an embed dictionary for Discord messages.
    Parameters:
        - title (str): Title of the embed message.
        - description (str): Description text for the embed.
        - fields (list): List of dictionaries, where each dictionary contains field name and value for the embed.
        - color (str, optional): Color for the embed; can be "red", "green", or any other value for default shade. Default is "red".
    Returns:
        - dict: A dictionary structured as a Discord embed message containing title, description, fields, and footer.
    Processing Logic:
        - Uses hex color code depending on the specified color name.
        - Default embed color is set to a specific shade of blue (blurple) if the color is neither "red" nor "green".
        - Automatically includes the current time as footer text formatted as month, day, year, and 12-hour clock time.
    """
    if color == "red":
        embed_color = 0xFF0000
    elif color == "green":
        embed_color = 0x00FF00
    else:
        embed_color = 0x7289DA
    embed = {
        "title": title,
        "description": description,
        "color": embed_color,  # Blurple color code
        "fields": fields,
        "footer": {
            "text": time.strftime(
                "%m/%d/%Y %I:%M %p", time.localtime()
            )  # Adds current time as footer
        },
    }
    return embed


def split_list(input_list, max_length):
    return [
        input_list[i : i + max_length] for i in range(0, len(input_list), max_length)
    ]


def format_discord_message():
    """Formats and sends a Discord message with item data, including undercut and not found items.
    Parameters:
        - None
    Returns:
        - None
    Processing Logic:
        - Updates item data using a function designed to track undercuts.
        - Handles empty responses by sending an error message to a Discord webhook.
        - Constructs embedded messages with item information for undercut and not found datasets, split into manageable parts for Discord.
    """
    global alert_record
    # update to latest data
    update_user_undercut_data()
    # note that the global region and homeRealmID are legacy dummy data and dont matter
    raw_undercut_data = simple_undercut(
        {"region": "foo", "homeRealmID": 1, "addonData": undercut_alert_data}
    )
    if not raw_undercut_data:
        send_discord_message(
            f"An error occured got empty response {raw_undercut_data}", webhook_url
        )
        return
    for realm, json_data in raw_undercut_data["results_by_realm"].items():
        embed_uc = []
        embed_nf = []

        for dataset in ["undercuts", "not_found"]:
            for value in json_data[dataset]:
                # logger.info(value)

                item_name = value.pop("item_name")
                item_id = value.pop("item_id")
                link = value.pop("link")
                desc = (
                    f"[Link]({link})\nItem ID: ({item_id})\n"
                    + f"Lowest Price: {value['lowest_price']}\nYour Price: {value['user_price']}"
                )

                if dataset == "undercuts":
                    embed_uc.append(
                        {"name": f"**{item_name}**", "value": desc, "inline": True}
                    )
                else:
                    embed_nf.append(
                        {"name": f"**{item_name}**", "value": desc, "inline": True}
                    )

        # send message for each realm
        if len(embed_uc) > 0:
            # split embed_uc into lists no longer than 25
            split_uc = split_list(embed_uc, 25)
            for uc in split_uc:
                embed = create_embed(
                    "Undercuts",
                    f"List of your items that are undercut!\nRealm: {realm}\nRegion: {region}\n",
                    uc,
                    "red",
                )
                send_to_discord(embed, webhook_url)
            time.sleep(1)

        if len(embed_nf) > 0 and include_sold_not_found:
            # split embed_uc into lists no longer than 25
            split_nf = split_list(embed_nf, 25)
            for nf in split_nf:
                embed = create_embed(
                    "Sold, Expired or Not Found",
                    f"List of items with price levels not found in the blizzard api data.\nRealm: {realm}\nRegion: {region}\n",
                    nf,
                    "green",
                )
                send_to_discord(embed, webhook_url)
                time.sleep(1)


#### MAIN ####
def main():
    """Main function to manage timing and alert handling for update processes.
    Parameters:
        - None
    Returns:
        - None
    Processing Logic:
        - Clears the alert record at the start of each hour.
        - Checks and processes undercuts within a certain time window after the update trigger.
        - Pauses execution for a minute both during the active check and while waiting.
    """
    global alert_record
    update_time = get_update_timers(region, True)[0]["lastUploadMinute"]
    while True:
        current_min = int(datetime.now().minute)

        # clear out the alert record once an hour
        if current_min == 0:
            print("\n\nClearing Alert Record\n\n")
            alert_record = []

        # # update the update min once per hour
        # if current_min == 1:
        #     update_time = get_update_timers(region, True)[0]["lastUploadMinute"]

        # check the upload min up 3 to 5 min after the commodities trigger
        if update_time + 3 <= current_min <= update_time + 5:
            print(
                f"NOW AT MATCHING UPDATE MIN!!! {datetime.now()}, checking for undercuts"
            )
            if autoupdate:
                update_region_undercut_json()
            format_discord_message()
            time.sleep(60)
        else:
            print(
                f"at {datetime.now()}, waiting for {[update_time]} to check undercuts"
            )
            time.sleep(60)


def send_discord_message(message, webhook_url):
    """Send a message to a Discord channel using a webhook.
    Parameters:
        - message (str): The message content to send to Discord.
        - webhook_url (str): The URL of the Discord webhook to use for sending the message.
    Returns:
        - bool: True if the message was sent successfully, False otherwise.
    Processing Logic:
        - The function uses `requests.post` to send a message via a Discord webhook.
        - It raises an exception for non-2xx HTTP status codes to ensure the request was successful.
        - If an exception occurs during the request, it logs the error and returns False.
    """
    try:
        json_data = {"content": message}
        response = requests.post(webhook_url, json=json_data)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return True  # Message sent successfully
    except requests.exceptions.RequestException as ex:
        print("Error sending Discord message: %s", ex)
        return False  # Failed to send the message


if not send_discord_message("starting simple undercuts", webhook_url):
    print("Failed to send Discord message")
    exit(1)
else:
    print("Discord message sent successfully")

if __name__ == "__main__":
    # run once on start
    format_discord_message()
    # run on schedule
    main()
