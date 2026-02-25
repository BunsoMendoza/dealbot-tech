# Task: Python environment & dependencies

Status: Completed

## What I did

- Created a Python virtual environment and installed project dependencies from `requirements.txt`.

## Commands (Windows PowerShell)

```powershell
python -m venv .venv
# Activate the venv
. .venv\Scripts\Activate.ps1
# Upgrade pip and install deps
pip install --upgrade pip
pip install -r requirements.txt
```

Notes:
- `requirements.txt` currently lists `tweepy`, `python-dotenv`, and `requests`.
- Keep your `.env` file with credentials out of version control (already in `.gitignore`).

## Next suggested tasks

- Parse and validate `products.csv`.
- Integrate the LLM in `llm.py` to generate tweet copy.
- Implement scheduling in `bot.py`.
