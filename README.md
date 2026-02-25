DealBot — Twitter deal posting bot

Quick start
-----------

1. Copy `.env.example` to `.env` and fill in credentials (`TWITTER_API_KEY`, `TWITTER_API_KEY_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET`). Add `LLM_API_KEY` if you want OpenAI generation.

2. Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

3. Run once (single posting run):

```powershell
python bot.py --once --limit 1
```

4. To run continuously (every hour by default):

```powershell
python bot.py --interval 60 --limit 1
```

Docker
------

Build and run the image:

```powershell
docker build -t dealbot .
docker run --env-file .env dealbot
```

CI
--

There is a GitHub Actions workflow at `.github/workflows/ci.yml` that runs tests on push and PR.

Safety notes
------------

- Keep your `.env` secret and out of version control. Use GitHub Secrets for CI.
- Review generated tweet content before enabling automatic posting.

Monitoring & deployment
-----------------------

- A lightweight health endpoint is available at `/health` (port `8000` by default) and reports `posted_count` and `last_run`.
- To run the health server in the container, the bot exposes port `8000`; `docker-compose.yml` maps that port.
- Example `systemd` unit is provided at `deploy/dealbot.service` — adapt paths and the service user to your system.

Docker Compose
--------------

Use `docker-compose up -d` to build and run the container. The compose file includes a simple HTTP healthcheck that queries `/health`.

