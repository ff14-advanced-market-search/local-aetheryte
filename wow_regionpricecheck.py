#!/usr/bin/python3
from __future__ import print_function
import os, json, time
from datetime import datetime
import requests
from tenacity import retry, stop_after_attempt


print("Sleep 10 sec on start to avoid spamming the api")
time.sleep(10)

#### GLOBALS ####
alert_record = []
price_alert_data = json.load(open("wow_user_data/regionpricecheck/region_snipe.json"))
if len(price_alert_data) == 0:
    print(
        "Error please generate your snipe data at: https://saddlebagexchange.com/wow/price-alert"
    )
    print("Then paste it into wow_user_data/config/regionpricecheck/single_snipe.json")
    exit(1)
region = price_alert_data["region"]

try:
    webhook_url = json.load(open("wow_user_data/config/regionpricecheck/webhooks.json"))[
        "webhook"
    ]
except FileNotFoundError:
    print(
        "Error: No webhook file found for regionpricecheck, add your webhook to wow_user_data/config/regionpricecheck/webhooks.json"
    )
    exit(1)
except KeyError:
    print(
        "Error: No webhook found in wow_user_data/config/regionpricecheck/webhooks.json add one in"
    )
    exit(1)


def simple_snipe(json_data):
    snipe_results = requests.post(
        "http://api.saddlebagexchange.com/api/wow/regionpricecheck",
        json=json_data,
    ).json()

    return snipe_results


def get_update_timers(region):
    print("Getting update timers")
    # get from api every time
    update_timers = requests.post(
        "http://api.saddlebagexchange.com/api/wow/uploadtimers",
        json={},
    ).json()["data"]

    # cover specific realms
    if region == "EU":
        update_id = -2
    else:
        update_id = -1
    server_update_times = [
            time_data
            for time_data in update_timers
            if time_data["dataSetID"] == update_id
    ]

    return server_update_times


@retry(stop=stop_after_attempt(3))
def send_discord_message(message, webhook_url):
    try:
        json_data = {"content": message}
        response = requests.post(webhook_url, json=json_data)
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return True  # Message sent successfully
    except requests.exceptions.RequestException as ex:
        print("Error sending Discord message: %s", ex)
        return False  # Failed to send the message


def format_discord_message():
    global alert_record
    snipe_data = simple_snipe(price_alert_data)
    if not snipe_data:
        send_discord_message(
            f"An error occured got empty response {snipe_data}", webhook_url
        )
        return
    if "matching" not in snipe_data:
        send_discord_message(f"No matching snipes found", webhook_url)
        return
    if len(snipe_data["matching"]) == 0:
        send_discord_message(f"No matching snipes found", webhook_url)
        return

    for auction in snipe_data["matching"]:
        message = (
            "==================================\n"
            + f"`item:` {auction['item_name']}\n"
            + f"`price:` {auction['ah_price']}\n"
            + f"`desired_state`: {auction['desired_state']}\n"
            + f"`itemID:` {auction['item_id']}\n"
            + f"[Undermine link]({auction['link']})\n"
            + f"realmNames: {auction['realm_names']}\n"
            + "==================================\n"
        )
        if auction not in alert_record:
            send_discord_message(message, webhook_url)
            alert_record.append(auction)


#### MAIN ####
def main():
    global alert_record
    alert_item_ids = [item["itemID"] for item in price_alert_data["user_auctions"]]
    update_time = get_update_timers(region)[0]["lastUploadMinute"]
    while True:
        current_min = int(datetime.now().minute)

        # clear out the alert record once an hour
        if current_min == 0:
            print("\n\nClearing Alert Record\n\n")
            alert_record = []
        # update the update min once per hour
        if current_min == 1:
            update_time = get_update_timers(region)[0]["lastUploadMinute"]

        # check the upload min up 3 to 5 min after the commodities trigger
        if update_time + 3 <= current_min <= update_time + 7:
            print(
                f"NOW AT MATCHING UPDATE MIN!!! {datetime.now()}, checking for snipes on {alert_item_ids}"
            )
            format_discord_message()
            time.sleep(60)
        else:
            print(
                f"at {datetime.now()}, waiting for {[update_time]} for {alert_item_ids}"
            )
            time.sleep(60)


if not send_discord_message("starting simple alerts", webhook_url):
    print("Failed to send Discord message")
    exit(1)
else:
    print("Discord message sent successfully")

if __name__ == "__main__":
    # run once on start
    format_discord_message()
    # run on schedule
    main()
