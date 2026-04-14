# Cat Facts Chrome Extension — Design Document

## 1. Overview

A Manifest V3 Chrome extension that delivers a fresh cat fact to the user every
day. The extension provides a popup for instant facts on demand, desktop
notifications on a configurable schedule, and an options page to control
behaviour — all powered by the same free `catfact.ninja` API used by the
existing SMS sender.

---

## 2. Goals

- Show a new cat fact in a popup whenever the user clicks the extension icon.
- Fire a desktop notification once per day (time configurable by the user).
- Cache the current fact locally so the popup loads instantly without waiting
  for a network call.
- Require zero backend infrastructure — the extension talks directly to the
  public Cat Fact API from the browser.

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Chrome Browser                           │
│                                                                 │
│  ┌──────────────┐    click     ┌───────────────────────────┐   │
│  │ Extension    │─────────────▶│        popup.html         │   │
│  │ Toolbar Icon │              │  popup.js                 │   │
│  └──────────────┘              │  - reads cached fact      │   │
│                                │  - "New Fact" button      │   │
│  ┌──────────────────────────┐  └──────────┬────────────────┘   │
│  │   Service Worker         │             │ fetch new fact      │
│  │   background.js          │◀────────────┘                    │
│  │                          │                                  │
│  │  chrome.alarms API       │──────────────────────────────┐   │
│  │  ┌────────────────────┐  │                              ▼   │
│  │  │ daily-fact alarm   │  │                   ┌──────────────┐│
│  │  └────────┬───────────┘  │                   │ catfact.ninja││
│  │           │ fires        │                   │ REST API     ││
│  │           ▼              │                   └──────┬───────┘│
│  │  fetch + cache + notify  │                          │ fact   │
│  └──────────────────────────┘                          │        │
│                                                        │        │
│  ┌──────────────────────────┐    chrome.storage.local  │        │
│  │     options.html         │◀──────────────────────── ┘        │
│  │     options.js           │    { fact, fetchedAt,             │
│  │  - notification time     │      notifyTime, enabled }        │
│  │  - enable/disable        │                                   │
│  └──────────────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Component Breakdown

### 4.1 Manifest (`manifest.json`)

Manifest V3. Required permissions:

| Permission | Reason |
|---|---|
| `alarms` | Schedule the daily notification |
| `notifications` | Show desktop notifications |
| `storage` | Persist the cached fact and user settings |

No `host_permissions` needed — `catfact.ninja` is a public CORS-enabled API
and can be fetched from any extension context.

### 4.2 Service Worker (`background.js`)

Runs in the background (as a MV3 service worker). Responsibilities:

- **On install** — fetch an initial fact, store it, register the daily alarm.
- **On alarm fire** — fetch a new fact, cache it, send a desktop notification.
- **On message from popup** — fetch a new fact on demand and return it.

Key functions:

```
fetchAndCacheFact()   → GET catfact.ninja/fact → store in chrome.storage.local
scheduleDailyAlarm()  → chrome.alarms.create("daily-fact", { periodInMinutes })
handleAlarm()         → fetchAndCacheFact() + showNotification()
```

### 4.3 Popup (`popup.html` + `popup.js`)

Opens when the user clicks the toolbar icon. Layout:

```
┌─────────────────────────────┐
│  🐱 Cat Fact of the Day     │
│─────────────────────────────│
│                             │
│  "Cats sleep up to 16       │
│   hours per day."           │
│                             │
│  [  Get a New Fact  ]       │
│                             │
│  Last updated: 2 hours ago  │
└─────────────────────────────┘
```

- Reads `{ fact, fetchedAt }` from `chrome.storage.local` on open.
- "Get a New Fact" sends a message to the service worker and refreshes the
  displayed fact when the response arrives.
- Shows a relative timestamp ("X minutes ago") so the user knows how fresh
  the fact is.

### 4.4 Options Page (`options.html` + `options.js`)

Accessible via right-click → "Options". Settings:

| Setting | Default | Description |
|---|---|---|
| Daily notification | Enabled | Toggle on/off |
| Notification time | 09:00 | Hour/minute the alarm fires |

Saving options re-registers the alarm with the updated schedule.

### 4.5 Shared Storage Schema (`chrome.storage.local`)

```json
{
  "fact": "Cats have 32 muscles in each ear.",
  "fetchedAt": 1713000000000,
  "notifyEnabled": true,
  "notifyHour": 9,
  "notifyMinute": 0
}
```

---

## 5. Data Flow

### 5.1 First Install

```
Extension installed
      │
      ▼
background.js: onInstalled
      │
      ├─▶ fetchAndCacheFact() ──▶ catfact.ninja ──▶ store { fact, fetchedAt }
      │
      └─▶ scheduleDailyAlarm(hour=9, minute=0)
```

### 5.2 Daily Alarm Fires

```
chrome.alarms: "daily-fact"
      │
      ▼
background.js: handleAlarm()
      │
      ├─▶ fetchAndCacheFact() ──▶ catfact.ninja ──▶ update storage
      │
      └─▶ chrome.notifications.create()
                │
                ▼
          Desktop notification:
          "🐱 Cat Fact — <fact text>"
```

### 5.3 User Clicks Popup

```
User clicks icon
      │
      ▼
popup.js: reads chrome.storage.local
      │
      ├─▶ display cached fact + timestamp
      │
      └─▶ [Get a New Fact] clicked
                │
                ▼
          chrome.runtime.sendMessage({ action: "fetchFact" })
                │
                ▼
          background.js: fetchAndCacheFact()
                │
                ▼
          popup.js: receives response, updates display
```

---

## 6. File Structure

```
chrome-extension/
├── manifest.json         # MV3 manifest — permissions, entry points
├── background.js         # Service worker — alarms, fetch, notify
├── popup.html            # Popup markup
├── popup.js              # Popup logic
├── options.html          # Options page markup
├── options.js            # Options page logic
├── icons/
│   ├── icon16.png        # Toolbar icon (16×16)
│   ├── icon48.png        # Extension management page (48×48)
│   └── icon128.png       # Chrome Web Store (128×128)
└── styles.css            # Shared styles for popup and options
```

---

## 7. Key Design Decisions

| Decision | Rationale |
|---|---|
| Manifest V3 (service worker, not background page) | MV3 is required for new Chrome Web Store submissions; service workers replace persistent background pages |
| `chrome.storage.local` over `localStorage` | Accessible from both the service worker and the popup; `localStorage` is not available in service workers |
| Cache fact in storage, don't fetch on popup open | Popup opens in < 100 ms; network latency would cause visible delay; the daily alarm keeps the cache fresh |
| `chrome.alarms` for scheduling | Survives browser restarts and does not require the service worker to be running continuously |
| No backend | Keeps the extension self-contained and avoids running infrastructure; the public Cat Fact API is free and requires no authentication |

---

## 8. Permissions Justification (Privacy)

Chrome Web Store requires justification for each permission:

- **`alarms`** — needed to schedule the once-daily fact fetch without keeping
  the service worker alive permanently.
- **`notifications`** — needed to push the daily fact to the user as a desktop
  notification.
- **`storage`** — needed to persist the cached fact and user preferences
  between browser sessions.

No browsing history, tab data, or personal information is collected or
transmitted. The only outbound request is `GET https://catfact.ninja/fact`.

---

## 9. Out of Scope

- Syncing facts across devices (`chrome.storage.sync` would require a quota
  analysis and is not needed for v1).
- A history log of past facts.
- Custom fact categories or filtering.
- Integration with the existing SMS sender — the extension is a standalone
  client.

---

## 10. Acceptance Criteria

- [ ] Clicking the extension icon shows the cached cat fact and a timestamp
- [ ] "Get a New Fact" fetches and displays a new fact without reloading the popup
- [ ] A desktop notification fires once per day at the configured time
- [ ] Notifications can be disabled from the options page
- [ ] Notification time can be changed from the options page and takes effect on
      the next alarm cycle
- [ ] The extension loads and functions correctly after a browser restart
- [ ] No errors appear in `chrome://extensions` or the service worker console
