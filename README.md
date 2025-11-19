

---

# Technical Assignment — Autodialer App (Ruby on Rails)

This project is a **multi-tool web application built with Ruby on Rails**, combining three distinct utilities in a single interface:

1. **Autodialer** (Vonage API)
2. **LinkedIn Profile Scraper** (Python + Playwright)
3. **AI Blog Generator** (LLM-based)

This was developed as a first-time exploration of Ruby and Rails, resulting in a simple, minimalistic app with three primary pages: **Autodialer**, **Scraper**, and **Blogs**.
Hosted on render with docker image. link-> [https://autodialer-v1.onrender.com/home]

---

## 🚀 Features Overview

### 1. Autodialer (Ruby on Rails)

A lightweight interface to perform **bulk phone calls** via the **Vonage API** (similar to Twilio).

**Key Capabilities**

* Accepts a comma-separated list of phone numbers.
* Initiates automated calls and plays a test message (limited by free-tier constraints).
* Includes separate service classes for:

  * Handling third-party API calls.
  * Managing request/response flow.
  * Controller logic to glue everything together.

**Important Notes**

* The free Vonage tier allows calling **only verified numbers**, so testing was performed using a single verified personal number.
* Functionality will work for other numbers once on a paid tier or with proper verification.

**Environment Variables**
Place these in a `.env` file:

```
VONAGE_API_KEY=...
VONAGE_API_SECRET=...
VONAGE_FROM_NUMBER=...
```

---

### 2. LinkedIn Profile Scraper (Python + Playwright)

A standalone component with **two modes**: script-based and API-based.

#### **A. Script Version**

**Run:**

```bash
python scraper.py
```

**Usage**

* Add LinkedIn profile URLs (comma-separated) to `profile_url.txt`.
* Output is stored in `linkedin_state.json`.

#### **B. API Version**

**Run:**

```bash
uvicorn app:app --reload --host 0.0.0.0
```

**API Behavior**

* Accepts comma-separated LinkedIn URLs.
* Returns the scraped data in JSON.
* UI fetches from this API to display results.

**How It Works**

* Uses **Playwright** to open Chromium (`headless=False`) so progress can be observed.
* Extracts data from **About** and **Contact** sections using HTML selectors.
* First run requires manual login:
  This generates a `state.json` file allowing future authenticated scraping without logging in again.

---

### 3. AI Blog Generator

A simple interface to generate **technology-focused blog posts** using an LLM.

**Features**

* Some predefined sample blogs included for demonstration.
* Users can generate new blogs by providing a **title** and optional **details**.
* Output displayed directly in the UI.

---

## 📦 Project Structure

```
root/
├── autodialer/          # Rails app containing 3 pages (autodialer, scraper UI, blogs)
├── scraper/             # Python LinkedIn scraper (script + API)
│   ├── scraper.py
│   ├── app.py
│   ├── profile_url.txt
│   └── linkedin_state.json

```

---

## 🛠️ Setup & Installation

### **Rails App**

```
bundle install
rails s -b 0.0.0.0
```

### **Scraper**

```
pip install -r requirements.txt
playwright install
python scraper.py
```

### **Scraper API**

```
uvicorn app:app --reload --host 0.0.0.0
```

---

## 🧪 Testing Notes

* Autodialer tested only on a verified personal number due to Vonage free tier limitations.
* LinkedIn scraper tested in visible browser mode to validate selectors and login flow.
* Blog Generator tested with both predefined and user-generated prompts.

---


