# Cat Fact Messenger — Test Plan

## 1. Scope

Unit tests for every function in `cats.py`. No real HTTP requests or SMS
messages are made — all external calls are mocked. Tests are implemented in
`test_cats.py` using the standard `unittest` library.

---

## 2. Test Groups

### 2.1 `get_cat_fact`

| ID | Description | Input / Condition | Expected Result |
|----|-------------|-------------------|-----------------|
| F-01 | Returns fact string on success | Mock returns `{"fact": "Cats sleep 16 hours a day."}` | Returns `"Cats sleep 16 hours a day."` |
| F-02 | Exits on HTTP error status | Mock raises `HTTPError` | `SystemExit` raised, error logged |
| F-03 | Exits on network error | Mock raises `ConnectionError` | `SystemExit` raised, error logged |

---

### 2.2 `load_subscribers`

| ID | Description | Input / Condition | Expected Result |
|----|-------------|-------------------|-----------------|
| S-01 | Returns empty list when file absent | `subscribers.json` does not exist | Returns `[]` |
| S-02 | Returns list from valid file | File contains `{"subscribers": ["+1111", "+2222"]}` | Returns `["+1111", "+2222"]` |
| S-03 | Returns empty list when key missing | File contains `{}` | Returns `[]` |

---

### 2.3 `save_subscribers`

| ID | Description | Input / Condition | Expected Result |
|----|-------------|-------------------|-----------------|
| W-01 | Writes list to file correctly | Input `["+1111", "+2222"]` | File contains correct JSON |
| W-02 | Creates file if absent | File does not yet exist | File is created with correct content |
| W-03 | Overwrites existing file | File has stale data | File replaced with new list |

---

### 2.4 `send_fact`

| ID | Description | Input / Condition | Expected Result |
|----|-------------|-------------------|-----------------|
| T-01 | Sends SMS with correct params | Valid env vars, mock Twilio client | `messages.create` called with correct `body`, `from_`, `to` |
| T-02 | Exits when credentials missing | One or more env vars absent | `SystemExit` raised, error logged |
| T-03 | Logs error on Twilio failure | `messages.create` raises `Exception` | Error logged, no `SystemExit` (caller continues) |

---

### 2.5 `broadcast`

| ID | Description | Input / Condition | Expected Result |
|----|-------------|-------------------|-----------------|
| B-01 | Calls `send_fact` for each subscriber | Two subscribers | `send_fact` called exactly twice |
| B-02 | Logs warning with empty list | `subscribers=[]` | Warning logged, `send_fact` never called |
| B-03 | Continues after one failure | Second `send_fact` raises `Exception` | Third subscriber still receives the fact |

---

### 2.6 CLI — `--add`

| ID | Description | Input / Condition | Expected Result |
|----|-------------|-------------------|-----------------|
| A-01 | Adds new number | Number not in list | Number appended, file saved, confirmation printed |
| A-02 | Rejects duplicate | Number already in list | File unchanged, "already subscribed" printed |

---

### 2.7 CLI — `--remove`

| ID | Description | Input / Condition | Expected Result |
|----|-------------|-------------------|-----------------|
| R-01 | Removes existing number | Number in list | Number removed, file saved, confirmation printed |
| R-02 | Handles missing number | Number not in list | File unchanged, "not subscribed" printed |

---

### 2.8 CLI — `--list`

| ID | Description | Input / Condition | Expected Result |
|----|-------------|-------------------|-----------------|
| L-01 | Prints each subscriber | Two subscribers in file | Both numbers printed, one per line |
| L-02 | Handles empty list | No subscribers | Prints "No subscribers." |

---

### 2.9 CLI — default (send)

| ID | Description | Input / Condition | Expected Result |
|----|-------------|-------------------|-----------------|
| D-01 | Fetches fact and broadcasts | No CLI args, two subscribers | `get_cat_fact` and `broadcast` each called once |

---

## 3. Running the Tests

```bash
python -m pytest test_cats.py -v
```

Or with the standard library runner:

```bash
python -m unittest test_cats -v
```

---

## 4. Coverage Summary

| Module area | Tests |
|---|---|
| Fact fetching | F-01 – F-03 |
| Subscriber persistence | S-01 – S-03, W-01 – W-03 |
| SMS delivery | T-01 – T-03 |
| Broadcast logic | B-01 – B-03 |
| CLI `--add` | A-01 – A-02 |
| CLI `--remove` | R-01 – R-02 |
| CLI `--list` | L-01 – L-02 |
| CLI default | D-01 |

**Total: 20 test cases**
