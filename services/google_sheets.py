import asyncio
import logging
import time
from typing import List, Dict, Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from config import config

class SheetsService:
    _SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    _SHEET_NAME = "Операции"
    _REF_RANGE = "Справочник!A2:C"

    def __init__(self, credentials_path: str, spreadsheet_id: str):
        self._creds = Credentials.from_service_account_file(credentials_path, scopes=self._SCOPES)
        self._service = build("sheets", "v4", credentials=self._creds)
        self._sheets_api = self._service.spreadsheets()
        self.spreadsheet_id = spreadsheet_id
        self.reference_data: List[List[str]] = []
        self._cache_timestamp: float = 0

    async def _is_cache_stale(self) -> bool:
        return time.time() - self._cache_timestamp > config.cache_ttl_seconds

    async def load_reference_data(self) -> None:
        if not self.reference_data or await self._is_cache_stale():
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._sheets_api.values()
                    .get(spreadsheetId=self.spreadsheet_id, range=self._REF_RANGE)
                    .execute()
            )
            self.reference_data = result.get("values", []) or []
            self._cache_timestamp = time.time()

    async def get_reference_data(self) -> List[List[str]]:
        await self.load_reference_data()
        return self.reference_data

    async def get_reference_text(self) -> str:
        data = await self.get_reference_data()
        lines = []
        for row in data:
            if len(row) >= 3:
                lines.append(f"Категория: {row[0]}, Группа: {row[1]}, Подкатегория: {row[2]}")
        return "\n".join(lines)
        
    async def get_all_operations(self) -> List[List[str]]:
        """Fetches all transaction rows for one-time data migration."""
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(
                None,
                lambda: self._sheets_api.values()
                    .get(spreadsheetId=self.spreadsheet_id, range=f"{self._SHEET_NAME}!A2:F")
                    .execute()
            )
            return result.get("values", []) or []
        except Exception as e:
            logging.error(f"Failed to fetch all operations from Google Sheet: {e}")
            return []

    async def append_operation(self, row_values: list) -> None:
        body = {"values": [row_values]}
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: self._sheets_api.values()
                .append(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{self._SHEET_NAME}!A1",
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body=body
                )
                .execute()
        )

    async def get_report_sheet_url(self) -> str:
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}"
