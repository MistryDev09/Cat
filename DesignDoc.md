# Cat Fact Messenger — Design Document

## 1. Overview

Cat Fact Messenger is a single-script Python utility with one job: deliver a
random cat fact to a list of subscribers over SMS every day. It is intentionally
small — no web server, no database, no framework. The design prioritises
simplicity and replaceability over extensibility.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        cats.py                          │
│                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │   CLI    │    │  Fact Engine │    │    Broadcaster│  │
│  │ (argparse│───▶│  get_cat_fact│───▶│    broadcast  │  │
│  │  args)   │    │  (HTTP GET)  │    │  send_fact x N│  │
│  └──────────┘    └──────────────┘    └───────────────┘  │
│        │                                     │          │
│        ▼                                     ▼          │
│  ┌──────────────────┐              ┌──────────────────┐ │
│  │ Subscriber Store │              │   Twilio Client  │ │
│  │ subscribers.json │              │  (SMS delivery)  │ │
│  └──────────────────┘              └──────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │                                     │
         ▼                                     ▼
  Local JSON file                     Twilio REST API
                                      → Recipient phones
```

**External dependencies:**

```
┌────────────┐         ┌──────────────────┐        ┌──────────────┐
│  cron / OS │──run──▶ │    cats.py        │──GET──▶│ catfact.ninja│
│  scheduler │         │                  │        │   (free API) │
└────────────┘         │                  │──SMS──▶│ Twilio API   │
                       └──────────────────┘        └──────────────┘
```

---

## 3. Component Breakdown

### 3.1 Entry Point & CLI (`main`, `build_parser`)

`argparse` exposes four modes of operation:

| Invocation | Behaviour |
|---|---|
| `python cats.py` | Fetch fact, broadcast to all subscribers |
| `python cats.py --add NUMBER` | Add a phone number to the subscriber list |
| `python cats.py --remove NUMBER` | Remove a phone number |
| `python cats.py --list` | Print all current subscribers |

`--add`, `--remove`, and `--list` are mutually exclusive; the default (no flags)
triggers the broadcast path.

### 3.2 Fact Engine (`get_cat_fact`)

Makes a single `GET` request to `https://catfact.ninja/fact` with a 10-second
timeout. Parses the `fact` field from the JSON response. Exits with a logged
error if the request fails — there is no retry logic, because the cron
scheduler will retry tomorrow.

### 3.3 Broadcaster (`broadcast`, `send_fact`)

Iterates the subscriber list and calls `send_fact` for each number. Each call
is wrapped in its own try/except so a failed delivery to one number does not
prevent delivery to the others. Outcomes (success or failure) are emitted to
the standard logger.

### 3.4 Twilio Client (`send_fact`)

Instantiates a fresh `twilio.rest.Client` per run using credentials read from
environment variables. Sends a plain-text SMS with the body:

```
Cat Fact of the Day:
<fact text>
```

### 3.5 Subscriber Store (`load_subscribers`, `save_subscribers`)

Reads from and writes to `subscribers.json` in the project directory. The file
schema is minimal:

```json
{
  "subscribers": ["+15550001111", "+15550002222"]
}
```

If the file does not exist, `load_subscribers` returns an empty list (no crash
on first run). The file is git-ignored to avoid committing personal phone
numbers.

### 3.6 Configuration (`.env` + `python-dotenv`)

`load_dotenv()` is called at module level so environment variables are
available before any function runs. The three required variables are:

| Variable | Purpose |
|---|---|
| `TWILIO_ACCOUNT_SID` | Identifies the Twilio account |
| `TWILIO_AUTH_TOKEN` | Authenticates API calls |
| `TWILIO_FROM_NUMBER` | The Twilio number messages are sent from |

If any variable is missing, `send_fact` logs a clear error and exits rather
than sending a confusing Twilio error response.

---

## 4. Data Flow (Daily Send)

```
cron triggers cats.py
        │
        ▼
load_dotenv() ──── reads .env ──── populates os.environ
        │
        ▼
get_cat_fact() ─── GET catfact.ninja/fact ─── returns fact string
        │
        ▼
load_subscribers() ── reads subscribers.json ── returns [number, ...]
        │
        ▼
broadcast(fact, subscribers)
        │
        ├─▶ send_fact(fact, number_1) ── Twilio API ── SMS delivered
        ├─▶ send_fact(fact, number_2) ── Twilio API ── SMS delivered
        └─▶ send_fact(fact, number_N) ── Twilio API ── SMS delivered / error logged
```

---

## 5. File Structure

```
Cat/
├── cats.py            # All application logic
├── subscribers.json   # Subscriber list (runtime, git-ignored)
├── .env               # Credentials (runtime, git-ignored)
├── .env.example       # Checked-in credential template
├── requirements.txt   # requests, twilio, python-dotenv
├── MakeFile           # Registers the daily cron job
├── FEATURE.md         # Original feature proposal
├── DesignDoc.md       # This document
└── README.md          # Setup and usage guide
```

---

## 6. Scheduling

The `MakeFile` target `setup_cat_cron` appends an entry to the user's crontab:

```
45 20 * * * /usr/bin/python3 /path/to/cats.py
```

This fires at 20:45 (8:45 PM) every day. To change the time, edit the cron
expression in `MakeFile` before running `make setup_cat_cron`.

---

## 7. Key Design Decisions

| Decision | Rationale |
|---|---|
| Single script, no framework | The task is a straight line: fetch → send. A framework would add indirection with no benefit. |
| JSON file for subscribers | Avoids a database dependency for what is essentially a small, rarely-changing list. |
| Environment variables for credentials | Separates secrets from code; works with `.env` locally and with system env vars in CI or on a server. |
| Per-recipient error isolation | One bad number (e.g. disconnected) should not silence everyone else. |
| No retry on API failure | The scheduler retries on the next scheduled run. Adding in-process retries would complicate the script for marginal gain. |
| `if __name__ == "__main__"` guard | Makes the module importable for testing without side effects. |

---

## 8. Possible Future Improvements

- **Two-way subscription** — let users text a keyword to subscribe/unsubscribe
  without needing CLI access.
- **Fact deduplication** — log sent facts and avoid repeats until the pool is
  exhausted.
- **Delivery receipts** — poll Twilio for message status and surface failures
  in a daily summary.
- **Configurable schedule** — make the cron time a variable in `.env` rather
  than hardcoded in the Makefile.
- **Test suite** — unit tests for `get_cat_fact` and subscriber CRUD using
  mocked HTTP and Twilio clients.
