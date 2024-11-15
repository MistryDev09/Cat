import requests
from twilio.rest import Client


def get_word():
    url = "https://catfact.ninja/fact"
    params = {"api_key": "API_KEY"}

    response = requests.get(url)

    data = response.json()
    word = data["fact"]
    return word


def send_word(word_def):

    account_sid = "YOUR_TWILIO_ACC_ID"
    auth_token = "AUTH_TOKEN"
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f"The Cat Fact of the day is: \n {word_def}",
        from_="TWILIO_NUMBER",
        to="RECIPIENT_NUMBER"
    )



word_def = get_word()
send_word(word_def)
