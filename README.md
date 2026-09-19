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

## Project history and evolution

FintorAI was one of my early experiments with an AI-assisted personal-finance workflow. The original private repository was created in July 2025. As the idea matured, the product direction and lessons from FintorAI evolved into a separate, larger project called **Qarjym**.

Qarjym continues the broader personal-finance assistant direction with a more developed product architecture. It remains a separate project and its private source code is not included in this repository. A verified live demo link can be published here separately without implying that this FintorAI repository is the same deployment.

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

Runnable historical prototype / public portfolio snapshot. With your own Telegram, OpenAI and Google credentials configured as described above, the bot can be started with `python bot.py`.

This repository is preserved as an early stage of the product journey. The broader idea continues to be developed in Qarjym, including further product and UX improvements planned beyond HackAlem. This repository itself is not presented as a production-ready financial service.

See [`PROVENANCE.md`](PROVENANCE.md) for public-snapshot provenance and [`SECURITY.md`](SECURITY.md) for credential handling.
