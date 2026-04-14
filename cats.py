import argparse
import json
import logging
import os
import sys

import requests
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

SUBSCRIBERS_FILE = os.path.join(os.path.dirname(__file__), "subscribers.json")


# ---------------------------------------------------------------------------
# Subscriber persistence
# ---------------------------------------------------------------------------

def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    with open(SUBSCRIBERS_FILE) as f:
        return json.load(f).get("subscribers", [])


def save_subscribers(numbers):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump({"subscribers": numbers}, f, indent=2)


# ---------------------------------------------------------------------------
# Cat fact fetching
# ---------------------------------------------------------------------------

def get_cat_fact():
    try:
        response = requests.get("https://catfact.ninja/fact", timeout=10)
        response.raise_for_status()
        return response.json()["fact"]
    except Exception as exc:
        logging.error("Failed to fetch cat fact: %s", exc)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Sending
# ---------------------------------------------------------------------------

def send_fact(fact, to_number):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not all([account_sid, auth_token, from_number]):
        logging.error(
            "Missing Twilio credentials. Set TWILIO_ACCOUNT_SID, "
            "TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER in your .env file."
        )
        sys.exit(1)

    client = Client(account_sid, auth_token)
    try:
        client.messages.create(
            body=f"Cat Fact of the Day:\n{fact}",
            from_=from_number,
            to=to_number,
        )
        logging.info("Sent to %s", to_number)
    except Exception as exc:
        logging.error("Failed to send to %s: %s", to_number, exc)


def broadcast(fact, subscribers):
    if not subscribers:
        logging.warning("No subscribers. Add one with: python cats.py --add <number>")
        return
    for number in subscribers:
        try:
            send_fact(fact, number)
        except Exception as exc:
            logging.error("Unexpected error sending to %s: %s", number, exc)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Send a daily cat fact to all subscribers via SMS."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--add", metavar="NUMBER", help="Add a subscriber (E.164 format)")
    group.add_argument("--remove", metavar="NUMBER", help="Remove a subscriber")
    group.add_argument("--list", action="store_true", help="List all subscribers")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.add:
        subscribers = load_subscribers()
        if args.add in subscribers:
            print(f"{args.add} is already subscribed.")
        else:
            subscribers.append(args.add)
            save_subscribers(subscribers)
            print(f"Added {args.add}.")
        return

    if args.remove:
        subscribers = load_subscribers()
        if args.remove not in subscribers:
            print(f"{args.remove} is not subscribed.")
        else:
            subscribers.remove(args.remove)
            save_subscribers(subscribers)
            print(f"Removed {args.remove}.")
        return

    if args.list:
        subscribers = load_subscribers()
        if not subscribers:
            print("No subscribers.")
        else:
            for number in subscribers:
                print(number)
        return

    # Default: send today's fact to all subscribers
    fact = get_cat_fact()
    subscribers = load_subscribers()
    broadcast(fact, subscribers)


if __name__ == "__main__":
    main()
