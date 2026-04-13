# Feature Proposal: Subscriber Management System

## Overview

Add a subscriber management system so multiple phone numbers can receive daily cat
facts, with a simple CLI to add/remove subscribers and secure credential handling
via environment variables.

## Motivation

The current script hardcodes a single recipient and exposes Twilio credentials
directly in source code. This makes the project unusable for anyone other than the
original author and creates a security risk if the code is ever shared or committed
to a public repository.

## Proposed Changes

### 1. Environment Variable Configuration
Move all credentials out of source code into a `.env` file loaded at runtime via
`python-dotenv`. This prevents accidental credential exposure.

**Variables:**
```
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_FROM_NUMBER=...
```

### 2. Subscriber List (subscribers.json)
Store recipients in a local JSON file. The file holds a list of E.164-formatted
phone numbers.

```json
{
  "subscribers": ["+15550001111", "+15550002222"]
}
```

### 3. CLI for Subscriber Management
Extend `cats.py` with command-line arguments so subscribers can be managed without
editing any files.

```
python cats.py --add +15550001111       # Add a subscriber
python cats.py --remove +15550001111    # Remove a subscriber
python cats.py --list                   # List all subscribers
python cats.py                          # Send today's fact to all subscribers (default)
```

### 4. Broadcast to All Subscribers
On a normal (no-args) run, the script sends the cat fact to every number in
`subscribers.json` rather than a single hardcoded number.

### 5. Basic Error Handling & Logging
Wrap API and Twilio calls in try/except blocks and emit simple log lines so cron
job failures are visible in system logs.

## Scope

| Area | Change |
|------|--------|
| `cats.py` | Refactored — env vars, subscriber logic, CLI args, error handling |
| `subscribers.json` | New file — persists subscriber list (git-ignored) |
| `.env` | New file — credentials (git-ignored) |
| `.env.example` | New file — template showing required variables |
| `.gitignore` | New file — excludes `.env` and `subscribers.json` |
| `requirements.txt` | New file — pins `requests`, `twilio`, `python-dotenv` |
| `README.md` | Updated — new setup and usage instructions |

## Out of Scope

- Web UI or API endpoint
- Two-way SMS (subscribe by texting a keyword)
- Cloud/database storage
- Unsubscribe links

## Acceptance Criteria

- [ ] Running `python cats.py` with no args sends a cat fact to all subscribers
- [ ] `--add`, `--remove`, and `--list` work correctly
- [ ] No credentials appear in source code
- [ ] Script logs success/failure for each recipient
- [ ] Failure to reach one recipient does not prevent others from receiving the fact
