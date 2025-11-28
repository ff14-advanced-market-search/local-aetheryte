import requests
import json
import os
import time
from constants import URL_BASE
###### CONFIGURATION ITEMS
# Option to @mention target user or role
# Populate with your own discord tag e.g. "<@114321431933142431>\n"
discordTag = ""
# Option to 'remember' last undercut and NOT repeat undercut messages
suppressRepeats = True
# Format to be used in the undercut message. This accepts markdown formatting.
# Accepted variables:
# - {item_name} - Name of the item
# - {link} - Universalis link to the item
# - {my_ppu} - Your current price per unit
# - {ppu} - The undercut price per unit
# - {undercut_retainer} - The retainer that undercut you
# DEFAULT FORMAT: "[{item_name}]({link})"
# Example: "[{item_name}]({link}) — Mine: {my_ppu}, {undercut_retainer}: {ppu}"
undercut_message_template = "[{item_name}]({link})"

localdata = {}


def create_embed(title, description, fields):
    """Creates a structured embed dictionary for displaying rich content.
    Parameters:
        - title (str): The title of the embed.
        - description (str): The main content or description of the embed.
        - fields (list): A list of dictionaries, each containing field information.
    Returns:
        - dict: A dictionary representing the embed with the provided title, description, fields, and other properties.
    Processing Logic:
        - The default color for the embed is set to green (0x00FF00).
        - Automatically includes a footer with the current date and time."""
    embed = {
        "title": title,
        "description": description,
        "color": 0x00FF00,  # You can change this to any color you prefer
        "fields": fields,
        "footer": {
            "text": time.strftime(
                "%m/%d/%Y %I:%M %p", time.localtime()
            )  # Adds current time as footer
        },
    }
    return embed


def organize_by_retainer(auction_data):
    """Organizes auction data by retainer name.
    Parameters:
        - auction_data (dict): A dictionary containing auction item details, where each key is an item ID, and each value is another dictionary with auction information including the retainer's name.
    Returns:
        - dict: A dictionary where each key is a retainer name and each value is a list of auction details corresponding to that retainer.
    Processing Logic:
        - Iterates over each auction item in `auction_data`.
        - Groups auction details under the key corresponding to the retainer's name.
        - Creates an entry for the retainer if it does not exist in the result dictionary.
    """
    auctions_by_retainer = {}
    for item_id, details in auction_data.items():
        retainer_name = details["my_retainer"]
        if retainer_name not in auctions_by_retainer:
            auctions_by_retainer[retainer_name] = []
        auctions_by_retainer[retainer_name].append(details)
    return auctions_by_retainer


def send_to_discord(embed, webhook_url):
    # Send message
    """Send an embed message to a Discord channel using a webhook.
    Parameters:
        - embed (dict): JSON-serializable dictionary representing the Discord embed to be sent.
        - webhook_url (str): URL of the Discord webhook through which the embed message will be sent.
    Returns:
        - None
    Processing Logic:
        - The function sends the provided embed to the specified Discord webhook URL.
        - A successful request will result in console output indicating success.
        - If the request fails, it logs the status code and error message to the console.
    """
    print(f"sending embed to discord...")
    req = requests.post(webhook_url, json={"embeds": [embed], "content": discordTag})
    if req.status_code != 204 and req.status_code != 200:
        print(f"Failed to send embed to discord: {req.status_code} - {req.text}")
    else:
        print(f"Embed sent successfully")


def check_auction_is_new(auction, server):
    """Check if the auction data is new or suppressed from repeats based on the existing local data.
    Parameters:
        - auction (dict): Auction details including 'real_name', 'my_ppu', 'ppu', and 'undercut_retainer'.
        - server (str): The name of the server where the auction is hosted.
    Returns:
        - bool: Indicates if the auction data is new or not, where 'True' means it's new.
    Processing Logic:
        - Compares the given auction data with existing data stored locally using a composed key.
        - Updates the local storage if the auction data is new.
        - Returns 'True' if entry is not found in local data, or if the auction attributes do not match existing entries. Returns 'False' if all attributes match and suppressRepeats is enabled.
        - Always returns 'True' if suppressRepeats is disabled."""
    if suppressRepeats:
        real_name = auction["real_name"]
        my_ppu = auction["my_ppu"]
        ppu = auction["ppu"]
        undercut_retainer = auction["undercut_retainer"]
        localdataKey = f"{real_name}-{server}"

        # Check if the entry exists in localdata
        if localdataKey in localdata:
            # Get the existing entry
            existing_entry = localdata[localdataKey]

            # Check if all attributes match
            if (
                existing_entry["my_ppu"] == my_ppu
                and existing_entry["ppu"] == ppu
                and existing_entry["undercut_retainer"] == undercut_retainer
            ):
                print(f"{real_name} -- Exact match found")
                is_new_undercut = False
            else:
                is_new_undercut = True
                print(f"{real_name} -- New undercut data")
        else:
            is_new_undercut = True
            print(f"{real_name} -- First undercut")

        # Update localdata with the latest information
        localdata[localdataKey] = {
            "my_ppu": my_ppu,
            "ppu": ppu,
            "undercut_retainer": undercut_retainer,
        }

        return is_new_undercut
    else:
        # Always return True if suppressing repeats is disabled
        return True


def create_undercut_message(json_response, webhook_url):
    """Create a formatted message identifying undercut auctions from a JSON response and send it to a specified Discord webhook.
    Parameters:
        - json_response (dict): The JSON data containing auction and server information.
        - webhook_url (str): The Discord webhook URL for sending the message.
    Returns:
        - None: This function does not return any value.
    Processing Logic:
        - Organizes auction data by retainer name from the provided JSON data.
        - Generates a list of undercut auctions per retainer, including auction details and links.
        - Creates and sends an embedded message to a Discord channel if undercuts are found.
    """
    server = json_response["server"]
    title = f"Undercuts - {server}"
    description = "List of items that are being undercut!"
    fields = []

    auctions_by_retainer = organize_by_retainer(json_response.get("auction_data", {}))

    for retainer, details in auctions_by_retainer.items():
        values = []
        for auction in details:
            if check_auction_is_new(auction, server):
                values.append(
                    f"[{auction['real_name']}]({auction['link']}) — Mine: {auction['my_ppu']}, {auction['undercut_retainer']}: {auction['ppu']}"
                )
        value = "\n".join(values)
        if values:
            fields.append({"name": f"**{retainer}**", "value": value, "inline": True})
    if fields:
        embed = create_embed(title, description, fields)
        send_to_discord(embed, webhook_url)


## not using embeds, but handles case of too much text
# def old_create_undercut_message(json_response, webhook_url):
#     # Start building the message content
#     server = json_response["server"]
#     message_content = (
#         f"Undercuts - {server}\nList of items that are being undercut!\n\n"
#     )
#     message_content_body = ""
#
#     auctions_by_retainer = organize_by_retainer(json_response.get("auction_data", {}))
#     # Append information about each undercut item
#     for retainer, details in auctions_by_retainer.items():
#         retainer_content_body = f"**{retainer}**\n"
#         for auction in details:
#             retainer_content_body += f"[{auction['real_name']}]({auction['link']})\n"
#
#         # make sure we dont go over 2000 characters
#         if len(retainer_content_body) > 1700:
#             retainer_content_body += f"Too many undercuts on {retainer}, update all items on on this or ignore it!\n"
#
#         message_content_body += retainer_content_body
#         if len(message_content + message_content_body) > 1700:
#             send_to_discord(message_content + message_content_body, webhook_url, server)
#             # reset message content after sending
#             message_content_body = retainer_content_body
#
#     # send final message if anything is left
#     if len(message_content_body) != 0:
#         send_to_discord(message_content + message_content_body, webhook_url, server)


def run_undercut(webhooks):
    """Run undercut processing for files in a specific directory, sending requests to a predefined API based on the data from JSON files.
    Parameters:
        - webhooks (dict): A dictionary mapping server names to webhook URLs. Used to determine where to send notifications.
    Returns:
        - None
    Processing Logic:
        - Skips processing for files named "example.json" and those not present in the webhooks list.
        - Validates that JSON files contain a list and each list entry has required fields of specific types.
        - Sends a POST request to an API endpoint for processing data in valid entries.
        - Fetches the appropriate webhook from the provided dictionary to send notifications based on the server name.
    """
    for filename in os.listdir("./ffxiv_user_data/undercut"):
        if filename == "example.json":
            continue
        # skip when file name not in webhooks
        if filename.split(".")[0] not in webhooks:
            print(f"Error: No webhook found for {filename}")
            continue
        if filename.endswith(".json"):
            with open(f"./ffxiv_user_data/undercut/{filename}") as f:
                # check that the file is a list
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        print(f"Error: {filename} is not a list")
                        continue
                except json.JSONDecodeError:
                    print(f"Error: Failed to decode {filename}")
                    continue

                for entry in data:
                    undercut_fields = {
                        "retainer_names": list,
                        "server": str,
                        "ignore_ids": list,
                        "add_ids": list,
                        "hq_only": bool,
                    }
                    for field, field_type in undercut_fields.items():
                        if field not in entry:
                            print(f"Error: {filename} is missing {field}")
                            continue
                        if not isinstance(entry[field], field_type):
                            print(f"Error: {filename} has an invalid {field} type")
                            continue

                    time.sleep(1)
                    response = requests.post(
                        f"{URL_BASE}/undercut",
                        headers={
                            "Accept": "application/json",
                        },
                        json=entry,
                    )
                    if response.status_code == 200:
                        webhook = webhooks.get(entry["server"], None)
                        if webhook is None:
                            print(f"Error: No webhook found for {entry['server']}")
                            continue
                        elif not response.json():
                            print(
                                f"No auctions found or not undercut at all for | {json.dumps(entry)}"
                            )
                            continue
                        create_undercut_message(response.json(), webhook)
                    else:
                        print(f"Error: Failed to get a valid response for {filename}")


def main():
    # Load webhook URLs
    """Execute the `run_undercut` function periodically using webhook URLs from a JSON file.
    Parameters:
        - None
    Returns:
        - None
    Processing Logic:
        - Loads webhook URLs from './ffxiv_user_data/config/undercut/webhooks.json'.
        - The `run_undercut` function is called with the loaded webhooks.
        - The function enters a loop that waits for 5 minutes between each execution."""
    with open("./ffxiv_user_data/config/undercut/webhooks.json") as f:
        webhooks = json.load(f)

    while True:
        run_undercut(webhooks)
        print("Sleeping for 5 minutes...")
        time.sleep(300)


if __name__ == "__main__":
    main()
