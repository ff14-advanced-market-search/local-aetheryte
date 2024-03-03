import requests
import json
import os
import time

def create_embed(title, description, fields):
    embed = {
        "title": title,
        "description": description,
        "color": 0x00ff00,  # You can change this to any color you prefer
        "fields": fields,
        "footer": {
            "text": time.strftime('%m/%d/%Y %I:%M %p', time.localtime())  # Adds current time as footer
        }
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


def create_undercut_message(json_response, webhook_url):
    server = json_response["server"]
    title = f"Undercuts - {server}"
    description = "List of items that are being undercut!"
    fields = []

    auctions_by_retainer = organize_by_retainer(json_response.get("auction_data", {}))

    for retainer, details in auctions_by_retainer.items():
        value = "\n".join(f"[{auction['real_name']}]({auction['link']})" for auction in details)
        fields.append({"name": f"**{retainer}**", "value": value, "inline": True})

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
    for filename in os.listdir("./user_data/undercut"):
        if filename == "example.json":
            continue
        # skip when file name not in webhooks
        if filename.split(".")[0] not in webhooks:
            print(f"Error: No webhook found for {filename}")
            continue
        if filename.endswith(".json"):
            with open(f"./user_data/undercut/{filename}") as f:
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
                        "seller_id": str,
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
                        "http://api.saddlebagexchange.com/api/undercut",
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
    with open("./user_data/config/undercut/webhooks.json") as f:
        webhooks = json.load(f)

    while True:
        run_undercut(webhooks)
        print("Sleeping for 5 minutes...")
        time.sleep(300)


if __name__ == "__main__":
    main()
