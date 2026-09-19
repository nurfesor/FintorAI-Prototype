# Security

This public snapshot contains no working API credentials by design.

Use `.env.example` only as a template and provide your own values locally. Keep the following out of Git:

- Telegram bot tokens
- OpenAI API keys
- Google service-account credentials/private keys
- spreadsheet identifiers you consider private
- `.env` files
- SQLite databases and user data

The original private repository is not made public because private historical configuration must remain outside this sanitized snapshot.

If a credential is ever committed to a Git repository, removing it from the latest file is not sufficient; revoke/rotate it and treat the historical value as exposed.
