# Cat Fact Messenger

A lightweight Python utility that fetches a random cat fact from the
[Cat Fact API](https://catfact.ninja) and broadcasts it via SMS to a list of
subscribers using [Twilio](https://www.twilio.com). A cron job keeps it running
daily without any manual intervention.

---

## Requirements

- Python 3.x
- A [Twilio](https://www.twilio.com) account (Account SID, Auth Token, and a
  Twilio phone number)
- Unix/Linux system with `crontab` for scheduled runs

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/MistryDev09/Cat.git
cd Cat
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**3. Configure credentials**

Copy the example environment file and fill in your Twilio credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+15550000000
```

> Your `.env` file is git-ignored and will never be committed.

---

## Managing Subscribers

Phone numbers must be in
[E.164 format](https://www.twilio.com/docs/glossary/what-e164) (e.g.
`+15551234567`).

**Add a subscriber**

```bash
python cats.py --add +15551234567
```

**Remove a subscriber**

```bash
python cats.py --remove +15551234567
```

**List all subscribers**

```bash
python cats.py --list
```

Subscribers are stored in `subscribers.json` (git-ignored).

---

## Sending a Cat Fact

Run the script manually to send today's fact to every subscriber:

```bash
python cats.py
```

The script will:
1. Fetch a random cat fact from the Cat Fact API.
2. Send it to each subscriber via Twilio SMS.
3. Log success or failure for every recipient.

---

## Automated Daily Delivery (Cron)

Use the provided Makefile target to register a cron job that runs the script
every day at 8:05 AM:

```bash
make setup_cat_cron
```

To verify the job was added:

```bash
crontab -l
```

To remove the cron job, run `crontab -e` and delete the relevant line.

---

## Project Structure

```
Cat/
├── cats.py            # Main script — fetch, broadcast, subscriber CLI
├── subscribers.json   # Subscriber list (auto-created, git-ignored)
├── .env               # Twilio credentials (git-ignored)
├── .env.example       # Credential template
├── requirements.txt   # Python dependencies
├── MakeFile           # Cron job helper
├── FEATURE.md         # Feature proposal for subscriber management
├── DesignDoc.md       # Architecture and design overview
└── README.md          # This file
```

---

## License

This project is open-source and can be freely modified and distributed.
