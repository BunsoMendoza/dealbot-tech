# Threads Bot Setup — Quick Checklist

A compact checklist covering everything required to build and run a Threads‑based affiliate deals bot.

---

## 1. Accounts

- [ ] Meta Developer account  
- [ ] Instagram account (linked to Threads)  
- [ ] Threads account for the bot  
- [ ] Affiliate accounts (Amazon, Best Buy/Impact, Walmart, Target, etc.)

---

## 2. Meta App Setup

- [ ] Create a new app in **developers.facebook.com**  
- [ ] Add **Threads API** product  
- [ ] Request permissions:  
  - `threads_basic`  
  - `threads_content_publish`  
- [ ] Configure OAuth redirect URI  
- [ ] Retrieve **App ID** and **App Secret**

---

## 3. Authentication

- [ ] Run OAuth login with Instagram  
- [ ] Obtain short‑lived access token  
- [ ] Exchange for long‑lived token  
- [ ] Store token + Threads user ID in `.env`

---

## 4. Bot Code

- [ ] `threads_client.py` — upload + publish posts  
- [ ] `llm.py` — Groq caption generator  
- [ ] `bot.py` — main posting logic  
- [ ] `products.csv` — product list  
- [ ] `requirements.txt` — dependencies  
- [ ] `.env` — API keys + tokens

---

## 5. Posting Pipeline

- [ ] Load product from CSV  
- [ ] Generate caption with Groq  
- [ ] Upload image to Threads  
- [ ] Create post  
- [ ] Publish post  

---

## 6. Automation (Optional)

- [ ] GitHub Actions scheduled posting  
- [ ] Cron job on VPS / Raspberry Pi  
- [ ] Local manual run  
