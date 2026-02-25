Running DealBot — checklist
=================================

Follow these steps to set up, test, and run the bot. Keep your `.env` file private.

1) Prerequisites

- Install Python 3.10+ (3.11 recommended).
- (Optional) Docker & Docker Compose if you want containerized deployment.

2) Prepare credentials

- Copy ` .env.example` to `.env` and fill in values:
  - `TWITTER_API_KEY`
  - `TWITTER_API_KEY_SECRET`
  - `TWITTER_ACCESS_TOKEN`
  - `TWITTER_ACCESS_TOKEN_SECRET`
  - (optional) `LLM_API_KEY` and `LLM_PROVIDER` (set `openai` to use OpenAI)
- Ensure `.env` is not committed (repo `.gitignore` already excludes it).

3) Create virtual environment & install dependencies

PowerShell:

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

4) Run tests

```powershell
pip install pytest
pytest -q
```

5) Quick smoke tests (local checks)

- Verify `twitter_client` auth (requires real Twitter creds):

```powershell
python -c "from twitter_client import TwitterClient; print(TwitterClient().get_me())"
```

- Generate a sample tweet using the LLM fallback/template:

```powershell
python -c "from llm import generate_tweet; class P: title='Test'; url='https://example.com'; deal_price=9.99; currency='$'; print(generate_tweet(P()))"
```

6) Run a single posting run (dry run first — check generated tweets manually)

```powershell
python bot.py --once --limit 1
```

7) Run continuously

- Using the Python script (simple):

```powershell
python bot.py --interval 60 --limit 1
```

- Using Docker:

```powershell
docker build -t dealbot .
docker run --env-file .env -p 8000:8000 dealbot
```

- Using Docker Compose:

```powershell
docker-compose up -d
```

- Using systemd (example unit at `deploy/dealbot.service`):
  - Place repository at `/opt/dealbot` (or edit the unit to match your path).
  - Create virtualenv at `/opt/dealbot/.venv`, install deps there, and ensure `/opt/dealbot/.env` exists.
  - Enable & start:

```bash
sudo cp deploy/dealbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dealbot.service
```

8) Health checks & monitoring

- A small health endpoint is available at `http://<host>:8000/health` (container maps port 8000).
- Check status with:

```powershell
curl http://localhost:8000/health
```

- The health response includes `posted_count` and `last_run`.

9) CI / GitHub Actions

- Add repository secrets for CI if using LLM/Twitter calls during CI (not recommended to run real posts in CI):
  - `TWITTER_API_KEY`, `TWITTER_API_KEY_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET`
  - `LLM_API_KEY` (if needed)
- The workflow at `.github/workflows/ci.yml` runs tests.

10) Troubleshooting

- Check logs from the running process or container.
- Inspect `posted.json` to see which product URLs have been posted already.
- If tweets fail due to rate limits, review `twitter_client` logs (it has simple retry/backoff).

11) Security & safety notes

- Never commit `.env` to the repo. Use GitHub Secrets for CI.
- Review generated tweet content before enabling automated continuous posting.

12) Optional next steps (if you want me to do them for you)

- Add a `docker-compose.override.yml` for production volumes & logging.
- Add Prometheus metrics export and an alert rule.
- Expand unit tests and add end-to-end test harness.
