import requests
import json
import os
import time

check_path = "pricecheck"


def create_embed(title, description, fields):
    embed = {
        "title": title,
        "description": description,
        "color": 0x7289DA,  # Blurple color code
        "fields": fields,
        "footer": {
            "text": time.strftime(
                "%m/%d/%Y %I:%M %p", time.localtime()
            )  # Adds current time as footer
        },
    }
    return embed


def organize_by_retainer(auction_data):
    auctions_by_retainer = {}
    for item_id, details in auction_data.items():
        retainer_name = details["my_retainer"]
        if retainer_name not in auctions_by_retainer:
            auctions_by_retainer[retainer_name] = []
        auctions_by_retainer[retainer_name].append(details)
    return auctions_by_retainer


def send_to_discord(embed, webhook_url):
    # Send message
    print(f"sending embed to discord...")
    req = requests.post(webhook_url, json={"embeds": [embed]})
    if req.status_code != 204 and req.status_code != 200:
        print(f"Failed to send embed to discord: {req.status_code} - {req.text}")
    else:
        print(f"Embed sent successfully")


def create_pricecheck_message(json_response, webhook_url):
    title = "Price Alert"
    description = f"List of items that match your price alert settings"
    fields = []

    matching = json_response.get("matching", [])
    # Get rid of "itemName": false
    matching = list(filter(lambda x: x["itemName"], matching))

    if len(matching) == 0:
        return

    for match in matching:
        item_name = match.pop("itemName")
        desc = (
            f"[Universalis Link](https://universalis.app/market/{match['itemID']})\n"
            + f"Server: {match['server']}\n"
            + f"DC: {match['dc']}\n"
            + f"Lowest Price: {'{:,}'.format(match['minPrice'])}\n"
            + f"Quantity: {match['minListingQuantity']}\n"
            + f"HQ: {match['hq']}"
        )
        fields.append({"name": f"**{item_name}**", "value": desc, "inline": True})

    embed = create_embed(title, description, fields)
    send_to_discord(embed, webhook_url)


def run_undercut(webhooks):
    for filename in os.listdir(f"./wow_user_data/{check_path}"):
        if filename == "example.json":
            continue
        # skip when file name not in webhooks
        if filename.split(".")[0] not in webhooks:
            print(f"Error: No webhook found for {filename}")
            continue
        if filename.endswith(".json"):
            with open(f"./wow_user_data/{check_path}/{filename}") as f:
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
                    pricecheck_fields = {
                        "home_server": str,
                        "user_auctions": list,
                    }
                    for field, field_type in pricecheck_fields.items():
                        if field not in entry:
                            print(f"Error: {filename} is missing {field}")
                            continue
                        if not isinstance(entry[field], field_type):
                            print(f"Error: {filename} has an invalid {field} type")
                            continue

                    time.sleep(1)
                    response = requests.post(
                        "http://api.saddlebagexchange.com/api/pricecheck",
                        headers={
                            "Accept": "application/json",
                        },
                        json=entry,
                    )
                    if response.status_code == 200:
                        webhook = webhooks.get(filename.split(".")[0], None)
                        if webhook is None:
                            print(f"Error: No webhook found for {entry['server']}")
                            continue
                        elif not response.json():
                            print(
                                f"No listings found matching prices for | {json.dumps(entry)}"
                            )
                            continue
                        create_pricecheck_message(response.json(), webhook)
                    else:
                        print(f"Error: Failed to get a valid response for {filename}")


def main():
    # Load webhook URLs
    with open(f"./wow_user_data/config/{check_path}/webhooks.json") as f:
        webhooks = json.load(f)

    while True:
        run_undercut(webhooks)
        print("Sleeping for 5 minutes...")
        time.sleep(300)


if __name__ == "__main__":
    main()
