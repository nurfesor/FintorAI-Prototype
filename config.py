import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr, FilePath, ValidationError

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    """
    Holds and validates project settings.
    """
    bot_token: SecretStr
    openai_api_key: SecretStr
    google_credentials_json: FilePath
    spreadsheet_id: str
    cache_ttl_seconds: int = 3600
    openai_transaction_model: str = "gpt-4o-mini"
    openai_advice_model: str = "gpt-4o-mini"

try:
    # Use model_validate for robust parsing and validation from a dictionary
    config = Settings.model_validate({
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "google_credentials_json": os.getenv("GOOGLE_CREDENTIALS_JSON_PATH"),
        "spreadsheet_id": os.getenv("SPREADSHEET_ID"),
        "cache_ttl_seconds": os.getenv("CACHE_TTL_SECONDS", 3600),
        "openai_transaction_model": os.getenv("OPENAI_TRANSACTION_MODEL", "gpt-4o-mini"),
        "openai_advice_model": os.getenv("OPENAI_ADVICE_MODEL", "gpt-4o-mini"),
    })

except ValidationError as e:
    print("--- CONFIGURATION ERROR ---")
    for error in e.errors():
        field = error['loc'][0] if error['loc'] else 'unknown'
        message = error['msg']
        print(f"Field '{field}': {message}")
    print("-------------------------")
    print("Please check your .env file and ensure all variables are set correctly.")
    exit(1)
