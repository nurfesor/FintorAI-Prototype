# FintorAI

FintorAI is an early personal-finance Telegram bot prototype started in **July 2025**.
It was built to explore a simple workflow: write a transaction in natural language, classify it, save it, and keep a lightweight personal-finance history.

This repository is a **sanitized public snapshot** of the original private project. The private repository and its historical Git data are not published because they contain private configuration history. No credentials or user data are included here.

## What it does

- Telegram bot interface built with `aiogram`
- natural-language transaction parsing with OpenAI
- regex fallback for simple entries such as `coffee 350`
- manual category/group/subcategory entry flow
- local SQLite transaction history
- optional Google Sheets synchronization and reference categories
- basic financial-advice command

## Stack

- Python 3
- aiogram
- OpenAI API
- SQLAlchemy + SQLite
- Google Sheets API
- Pydantic settings

## Project history

FintorAI was one of my early experiments with an AI-assisted personal-finance workflow. The original private repository was created in July 2025. Later, the product ideas and lessons from FintorAI evolved into a separate project called **Qarjym**.

Qarjym is a separate private project and is not included in this repository.

## Setup

1. Create a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and provide your own credentials.
4. Provide your own Google service-account credentials file if Google Sheets integration is used.
5. Run:

```bash
python bot.py
```

## Configuration

The application expects these environment variables:

- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `GOOGLE_CREDENTIALS_JSON_PATH`
- `SPREADSHEET_ID`
- `CACHE_TTL_SECONDS` (optional, default `3600`)

Never commit real credentials, `.env`, database files, or Google credential files.

## Status

Historical prototype / public portfolio snapshot. It is shared to demonstrate an original project and its architecture, not as a production-ready financial service.

See [`PROVENANCE.md`](PROVENANCE.md) for public-snapshot provenance and [`SECURITY.md`](SECURITY.md) for credential handling.
