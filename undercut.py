import requests
import json
import os
import time


def create_undercut_message(json_response, webhook_url):
    # Start building the message content
    server = json_response['server']
    message_content = (
        f"Undercuts - {server}\nList of items that are being undercut!\n\n"
    )
    message_content_body = ""

    # Append information about each undercut item
    for item_id, details in json_response.get("auction_data", {}).items():
        message_content_body += f"[{details['real_name']}]({details['link']})\n"
        # make sure we dont go over 2000 characters
        if len(message_content+message_content_body) > 1500:
            send_to_discord(message_content+message_content_body, webhook_url, server)
            # reset message content after sending
            message_content_body = ""
    # send final message if anything is left
    send_to_discord(message_content+message_content_body, webhook_url, server)


def send_to_discord(message, webhook_url, server):
    # Send message
    if len(message) > 0:
        print(f"sending message for {server} undercuts to discord...")
        req = requests.post(
            webhook_url, json={"content": message}
        )
        if req.status_code != 204 and req.status_code != 200:
            print(f"Failed to send message to discord for {server} undercuts: {req.status_code} - {req.text}")
        else:
            print(f"Message sent for {server} undercuts")
    else:
        print(f"No undercuts found on {server}")

def main():
    # Load webhook URLs
    with open("./user_data/config/undercut/webhooks.json") as f:
        webhooks = json.load(f)

    for filename in os.listdir("./user_data/undercut"):
        if filename == "example.json":
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
                        webhook = webhooks.get(entry['server'],None)
                        if webhook is None:
                            print(f"Error: No webhook found for {entry['server']}")
                            continue
                        elif not response.json():
                            print(f"Error: No undercut data found for {entry['server']}")
                            continue
                        create_undercut_message(response.json(), webhook)
                    else:
                        print(f"Error: Failed to get a valid response for {filename}")


if __name__ == "__main__":
    main()
