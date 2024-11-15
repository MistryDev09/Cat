# Cat Fact Messenger

This project fetches a random cat fact from the [Cat Fact API](https://catfact.ninja) and sends it as a text message to a specified recipient using Twilio's messaging service. 
The project also includes a Makefile for setting up a cron job to run the script daily at 8:05 AM.

## Requirements

Before running this project, ensure you have the following:

- **Python 3.x**
- **Requests library**: Install using `pip install requests`
- **Twilio library**: Install using `pip install twilio`
- **A Twilio account** for sending messages
- **Crontab**: To schedule tasks on Unix-based systems

## Setup Instructions

### Install Dependencies

Use `pip` to install the required libraries:

```bash
pip install requests twilio
```

### Configure the Code

1. **Cat Fact API Key**: If the Cat Fact API requires an API key in the future, replace `"API_KEY"` in the `get_word` function. Currently, it works without an API key.
2. **Twilio Configuration**: Update the following placeholders in the `send_word` function:
   - `YOUR_TWILIO_ACC_ID`: Your Twilio Account SID.
   - `AUTH_TOKEN`: Your Twilio Auth Token.
   - `TWILIO_NUMBER`: Your Twilio phone number.
   - `RECIPIENT_NUMBER`: The phone number you want to send the cat fact to.

### Run the Script

You can manually run the script with:

```bash
python3 catfacts.py
```

### Setup the Cron Job

Use the provided `Makefile` to set up a cron job that runs the script daily at 8:05 AM. Run:

```bash
make setup_cat_cron
```

This command will add a cron job entry to execute `catfacts.py` every day at 8:05 AM.

## License

This project is open-source and can be freely modified and distributed.

---
