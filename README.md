# 📺 EPG Sync Checker

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Selenium](https://img.shields.io/badge/Selenium-Automation-yellow)](https://www.selenium.dev/)
[![Pandas](https://img.shields.io/badge/pandas-Data%20Processing-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)

**Internal-grade quality assurance tooling for live-streaming TV schedules (EPG).**
A Streamlit dashboard + headless-browser automation that verifies, validates, and
synchronizes the Electronic Program Guide (EPG) of a live-streaming platform
against its broadcast CMS — every single day, automatically.

> 🧪 **This is a sanitized showcase version.** All company data (spreadsheet IDs,
> CMS endpoints, channel catalogs, session cookies, service-account keys, and
> webhook URLs) has been replaced with placeholders or sample data.

---

## 🎯 The Problem

A live-streaming platform publishes dozens of linear (24/7) TV channels. Every day,
the editorial team schedules hundreds of programs in a Google Sheets EPG, which then
gets pushed to the public website and the internal broadcast CMS.

When the EPG and the CMS drift apart, viewers see:
- ❌ Black screen / dead air during gaps in the schedule
- ❌ The wrong program at the wrong time
- ❌ Programs that never air at all

Checking this **manually across ~40 channels × 2 days** was a slow, error-prone,
daily chore. This tool automates it end-to-end.

## ✨ Features

| Feature | Description |
| --- | --- |
| 🔍 **Automated EPG Verification** | Cross-checks spreadsheet schedules against the live website + CMS for *today* and *tomorrow*. |
| ⏱️ **Gap Detector Engine** | Flags every hole between two consecutive programs, including a 1-minute tolerance rule. |
| 🌙 **End-of-Day Coverage Check** | Detects schedules that don't reach midnight (`23:59` / cross-midnight), a classic cause of dead air. |
| 🧠 **Fuzzy Title Matching** | Normalization pipeline (accents, quotes, dashes, casing) + keyword intersection, so "FA Cup: Man Utd vs Liverpool" still matches "FA Cup Man Utd VS Liverpool Live". |
| 🟡 **Manual Revision Classifier** | Uses an overlap-scoring algorithm with a duration-penalty formula to distinguish *adjusted* programs from *replaced* ones. |
| 🔄 **Safe Sheet Sync** | Paste the CMS table → the app replaces only the target date's rows and re-uploads, never touching other dates. |
| 📦 **Custom Channel Manager** | Add new channels + Live Stream IDs from the UI; stored in a local JSON database. |
| 🤖 **Headless Automation** | Selenium (Firefox/Chrome, headless) with smart scrolling, date-tab clicking, "show more" expansion, and auto-retry on network lag. |
| 🚨 **Daily Alert Bot** | A scheduled dispatcher that checks every channel and pushes a report to Google Chat via webhook. |
| 🎨 **Modern UI** | Custom CSS, dark/light theme toggle, glassmorphism panels, loading animations. |

## 🖼️ Screenshots

| Dashboard (Dark Mode) | Verification Report |
| :---: | :---: |
| ![Dashboard](assets/dashboard.png) | ![Verification Report](assets/verification-report.png) |

> Running the app without credentials automatically activates **Demo Mode** with a
> built-in sample schedule — everything you see above is reproducible in seconds.

## 🏗️ Architecture

```
┌─────────────────────┐      ┌──────────────────────┐
│   Google Sheets     │      │  Live Website + CMS  │
│  (EPG source of     │      │  (what viewers see)  │
│   truth, per-       │      │                      │
│   channel tabs)     │      └──────────┬───────────┘
└──────────┬──────────┘                 │
           │  gspread API               │  Selenium (headless browser)
           ▼                            ▼
┌──────────────────────────────────────────────────┐
│                 CORE ENGINE (pandas)             │
│  • Column & date normalization                   │
│  • Gap detector                                  │
│  • End-of-day coverage check                     │
│  • Fuzzy title matching (fuzzy + time tolerance) │
│  • Overlap scoring (duration-penalty formula)    │
└──────────────────────┬───────────────────────────┘
                       │
        ┌──────────────┴───────────────┐
        ▼                              ▼
┌───────────────────┐        ┌─────────────────────┐
│  Streamlit UI     │        │  Scheduler / Cron   │
│  (on-demand       │        │  → Google Chat      │
│   verification)   │        │    webhook alerts   │
└───────────────────┘        └─────────────────────┘
```

**Two entry points share the same validation logic:**

| File | Role |
| --- | --- |
| `daily_generator.py` | Interactive Streamlit dashboard (verify a channel, sync CMS data back to Sheets). The main application. |
| `automation/epg_dispatcher.py` | Unattended daily bot — checks *all* channels for today & tomorrow and reports to Google Chat. |

## 🚀 Quick Start

### 1. Install dependencies

```bash
git clone https://github.com/rlyxyz/epg-sync-checker.git
cd epg-sync-checker
pip install -r requirements.txt
```

### 2. Run in Demo Mode (no setup needed) 🎉

```bash
streamlit run daily_generator.py
```

Without credentials, the app automatically runs in **Demo Mode** using a built-in
sample schedule so you can explore every part of the UI and the validation engine.

### 3. Connect your real data

| Secret | Where to put it | Notes |
| --- | --- | --- |
| Google Sheets service account | `credentials.json` (repo root) **or** `.streamlit/secrets.toml` under `[gcp_service_account]` | Share your spreadsheets with the service-account email. |
| Spreadsheet URLs | `URL_SPORT` / `URL_NON_SPORT` constants in `daily_generator.py` | One spreadsheet per category, one tab per channel. |
| Session cookie | `cookies.json` → `{"cookie_string": "..."}` | Needed for the CMS section of the dashboard. |
| Webhook URL | `GOOGLE_CHAT_WEBHOOK` environment variable | Used by the alert bot (never hardcode it). |

> ⚠️ All secrets are listed in `.gitignore` — double-check before committing.

## 📂 Project Structure

```
epg-sync-checker/
├── daily_generator.py           # Main app — Streamlit dashboard
├── automation/
│   └── epg_dispatcher.py        # Scheduled full-catalog checker + Google Chat alerts
├── Mulai_EPG_Checker.bat        # One-click launcher (Windows)
├── setup_firefox_profile.py     # One-time CMS login session setup (Firefox)
├── custom_channels.json         # User-defined channel → live stream ID map
├── packages.txt                 # System packages (Debian/Ubuntu) for Chromium
├── requirements.txt
├── logo_v.jpeg                  # Favicon
├── bg_dark.png / bg_light.png   # Theme backgrounds
├── mata_robot.png               # Design asset
└── README.md
```

## 📐 Validation Rules

1. **Gap rule** — `end_time(n)` must equal `start_time(n+1)` (or be exactly 1 minute apart). Anything else is a gap.
2. **Coverage rule** — the last program of the day must end at `00:00`, `23:59`, `24:00`, or cross midnight.
3. **Fuzzy match rule** — a spreadsheet program matches a CMS/web program when either:
   - normalized titles are substring-equal, **or**
   - ≥ 2 significant words intersect (stop-words like *live*, *replay*, *vs* are ignored), **or**
   - time slots overlap enough to score highest under the duration-penalty formula.

## 📈 Impact

- ⏱️ **From ~1 hour manual checking to a single click** — or zero clicks with the scheduled bot.
- 📺 **~40 channels × 2 days** verified automatically per run.
- 🐛 Dead-air risks (gaps, incomplete coverage, missing CMS entries) are caught **before broadcast**.
- 📣 Instant **Google Chat alerts** for the whole ops team instead of a manual spreadsheet report.

## 🧰 Tech Stack

`Python 3` · `Streamlit` · `pandas` · `BeautifulSoup4` · `Selenium` + `webdriver-manager` · `gspread` + `google-auth` · `Pillow`

## ⚖️ Disclaimer

This repository is a **portfolio showcase**. Domains, spreadsheet IDs, channel
catalogs, credentials, and webhook URLs are placeholders. The scraping logic is
intended for platforms you own or are authorized to test.

---

Made with ❤️ by [rlyxyz](https://github.com/rlyxyz)
